"""Explicit owner corrections to saved meeting facts, with derived-record reconciliation.

Original speech and evidence never change. Corrections are user assertions, not
new claims about what the recording proves. No provider call or outbound send.
"""
import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field
from sqlalchemy import inspect, select

from app.core.errors import ConflictError, NotFoundError
from app.jobs.index_queue import queue_index
from app.models.entities import (
    AuditLog,
    Commitment,
    ContextEvent,
    Decision,
    EntityEdge,
    Interaction,
    Memory,
    Person,
    Task,
)
from app.schemas.meeting_intelligence import CANDIDATE_FIELDS, StrictModel
from app.schemas.meetings import MeetingResponse
from app.services.assistant_connections import owner_lock
from app.services.meeting_intelligence import capture_for, require_review_snapshot
from app.services.notification_outbox import cancel_pending
from app.services.person_context import invalidate_drafts

MODELS = {'commitments': Commitment, 'tasks': Task, 'decisions': Decision, 'memories': Memory, 'interactions': Interaction}
NOTICE = 'Meeting details were corrected by the owner. Review the saved details and original transcript.'


class SavedDetailCorrection(StrictModel):
    request_id: UUID
    expected_review_token: str = Field(pattern=r'^[0-9a-f]{64}$')
    expected_records_token: str = Field(pattern=r'^[0-9a-f]{64}$')
    confirmed: Literal[True]
    candidate_id: str = Field(pattern=r'^[a-z_]+:[0-9]+$', max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    due_at: AwareDatetime | None = None
    reason: str = Field(min_length=1, max_length=1000)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


async def related_records(db, owner, meeting, capture):
    records = []
    for key, model in MODELS.items():
        ids = (capture.receipt or {}).get(key, [])
        if ids:
            rows = (await db.scalars(select(model).where(model.user_id == owner, model.id.in_(ids))
                .order_by(model.id).with_for_update().execution_options(populate_existing=True))).all()
            if len(rows) != len(set(ids)):
                raise ConflictError('A saved meeting record is unavailable. Review its history before correcting it.')
            records.extend(rows)
    events = (await db.scalars(select(ContextEvent).where(ContextEvent.user_id == owner,
        ContextEvent.source_type == 'meeting', ContextEvent.source_external_id == str(meeting.id))
        .order_by(ContextEvent.id).with_for_update().execution_options(populate_existing=True))).all()
    records.extend(events)
    people = {str(row.person_id) for row in records if isinstance(row, Interaction) and row.person_id}
    if people:
        records.extend((await db.scalars(select(Person).where(Person.user_id == owner, Person.id.in_(people))
            .order_by(Person.id).with_for_update().execution_options(populate_existing=True))).all())
    edges = (await db.scalars(select(EntityEdge).where(EntityEdge.user_id == owner,
        EntityEdge.source_entity_type == 'meeting', EntityEdge.source_entity_id == meeting.id,
        EntityEdge.valid_to.is_(None)).order_by(EntityEdge.id).with_for_update())).all()
    records_token = digest([
        {'table': row.__tablename__, 'values': {attr.key: getattr(row, attr.key)
            for attr in inspect(type(row)).column_attrs}}
        for row in [*records, *edges]])
    return records, edges, records_token


async def correction_state(db, owner, identity):
    await owner_lock(db, owner)
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if not capture.confirmed_at:
        raise ConflictError('Save the meeting review before correcting a saved detail.')
    records, _, token = await related_records(db, owner, meeting, capture)
    return {'review_token': MeetingResponse.model_validate(meeting).review_token,
        'records_token': token, 'affected_records': len(records),
        'corrections': (capture.receipt or {}).get('corrections', []),
        'notice': 'Corrections update existing records. Original speech and quotations are preserved.'}


async def correct_saved_detail(db, owner, identity, payload: SavedDetailCorrection):
    await owner_lock(db, owner)
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if not capture.confirmed_at:
        raise ConflictError('Save the meeting review before correcting a saved detail.')
    receipt = copy.deepcopy(capture.receipt or {})
    history = receipt.get('corrections', [])
    request_hash = digest(payload.model_dump(mode='json'))
    prior = next((item for item in history if item['request_id'] == str(payload.request_id)), None)
    if prior:
        if prior['request_hash'] != request_hash:
            raise ConflictError('This correction request was already used for a different edit.')
        return prior['result']
    require_review_snapshot(meeting, payload.expected_review_token)
    records, edges, token = await related_records(db, owner, meeting, capture)
    if token != payload.expected_records_token:
        raise ConflictError('A linked record changed. Reload and review it before correcting the meeting.')
    if len(history) >= 50:
        raise ConflictError('This meeting has reached its 50 correction limit. Its history remains available.')
    category, position = payload.candidate_id.split(':')
    data = copy.deepcopy(capture.intelligence)
    if category not in CANDIDATE_FIELDS or payload.candidate_id not in receipt.get('selected', []):
        raise NotFoundError('This saved detail is unavailable.')
    items = data.get(category, [])
    index = int(position)
    if index >= len(items):
        raise NotFoundError('This saved detail is unavailable.')
    if not payload.description.strip() or not payload.reason.strip():
        raise ConflictError('Enter the corrected detail and a reason.')
    if payload.due_at and category not in {'commitments', 'action_items', 'follow_ups'}:
        raise ConflictError('Only a commitment or task can have a deadline.')
    before = copy.deepcopy(items[index])
    item = {**before, 'description': payload.description.strip(),
        'due_at': payload.due_at.isoformat() if payload.due_at else None}
    # Keep original due_evidence and quotations, even when the owner corrects a
    # date. The correction journal explicitly separates the assertion from speech.
    items[index] = item
    affected = [edge for edge in edges if (edge.metadata_payload or {}).get('candidate_id') == payload.candidate_id]
    targets = {str(edge.target_entity_id): edge.target_entity_type for edge in affected}
    by_id = {str(row.id): row for row in records}
    if any(identity not in by_id for identity in targets):
        raise ConflictError('The original derived record is unavailable. No replacement was created.')
    # A task may fulfill several promises. Do not rewrite that task implicitly,
    # or leave it claiming to fulfill a materially different promise.
    promises = [key for key, kind in targets.items() if kind == 'commitment']
    if promises and await db.scalar(select(EntityEdge.id).where(EntityEdge.user_id == owner,
        EntityEdge.source_entity_type == 'task', EntityEdge.target_entity_type == 'commitment',
        EntityEdge.target_entity_id.in_(promises), EntityEdge.relationship_type == 'fulfills',
        EntityEdge.valid_to.is_(None)).limit(1)):
        raise ConflictError('This promise has a linked task. Review that relationship before correcting the promise.')
    now = datetime.now(timezone.utc)
    for target_id, kind in targets.items():
        row = by_id[target_id]
        if row.deleted_at or getattr(row, 'archived_at', None):
            raise ConflictError('A linked record was removed or archived. Restore or review it before correcting it.')
        description = item['description'] + (f' (Condition: {item["condition"]})' if item.get('condition') else '')
        if kind == 'commitment':
            if row.status in {'completed', 'cancelled'}:
                raise ConflictError('This commitment is closed. Its completion history must be reviewed separately.')
            row.description, row.due_at = description, payload.due_at
            row.reminder_at = None
            await cancel_pending(db, owner, row.id)
        elif kind == 'task':
            if row.status == 'done':
                raise ConflictError('This task is completed. Its completion history must be reviewed separately.')
            row.title, row.due_date = description[:500], payload.due_at
            row.description = 'Original quotation (historical speech): ' + before['evidence_text']
            row.calendar_sync_metadata = {**(row.calendar_sync_metadata or {}),
                'correction_review_required': True, 'correction_request_id': str(payload.request_id)}
        elif kind == 'decision':
            row.title, row.decision = description[:255], description
            row.context = f'Meeting {identity}. Original quotation (historical speech): ' + before['evidence_text']
        elif kind == 'memory':
            row.title, row.body = description[:255], description
            row.summary = 'Original quotation (historical speech): ' + before['evidence_text']
            row.meta = {**(row.meta or {}), 'owner_corrected': True}
        queue_index(db, row)
        await invalidate_drafts(db, owner, str(row.id))
    # Old prose may repeat the corrected fact. Retain it for audit but remove it
    # from current summaries and retrieval; do not invent a replacement summary.
    if 'original_intelligence' not in receipt:
        receipt['original_intelligence'] = copy.deepcopy(capture.intelligence)
    data.update(summary=NOTICE, executive_summary=NOTICE, detailed_summary='', discussion_sections=[],
        topics=[], suggested_title=None, purpose=None, agenda_items=[])
    selected = set(receipt.get('selected', []))
    meeting.summary = NOTICE
    meeting.decisions_list = [v['description'] for i, v in enumerate(data.get('decisions', [])) if f'decisions:{i}' in selected]
    meeting.action_items = [v['description'] for key in ('action_items', 'follow_ups')
        for i, v in enumerate(data.get(key, [])) if f'{key}:{i}' in selected]
    for row in records:
        if isinstance(row, Person):
            row.metadata_payload = {key: value for key, value in (row.metadata_payload or {}).items()
                if key not in {'ai_summary', 'relationship_summary', 'summary'}}
            queue_index(db, row)
            await invalidate_drafts(db, owner, str(row.id))
        elif isinstance(row, (Interaction, ContextEvent)):
            row.summary = NOTICE
            queue_index(db, row)
            await invalidate_drafts(db, owner, str(row.id))
        elif isinstance(row, Memory) and str(row.id) not in targets:
            # Other AI-derived memories might restate the edited detail. They
            # remain in history but cannot be retrieved as current facts.
            row.archived_at = now
            await invalidate_drafts(db, owner, str(row.id))
    for edge in affected:
        edge.metadata_payload = {**(edge.metadata_payload or {}), 'owner_corrected': True,
            'correction_request_id': str(payload.request_id)}
    result = {'meeting_id': str(identity), 'request_id': str(payload.request_id),
        'corrected_candidate': payload.candidate_id, 'updated_records': sorted(targets),
        'summary_invalidated': True, 'source_preserved': True}
    history.append({'request_id': str(payload.request_id), 'request_hash': request_hash,
        'at': now.isoformat(), 'reason': payload.reason.strip(), 'candidate_id': payload.candidate_id,
        'before': before, 'after': item, 'result': result})
    receipt['corrections'] = history
    capture.receipt, capture.intelligence = receipt, data
    meeting.meta = {**(meeting.meta or {}), 'correction_version': len(history), 'summary_needs_review': True}
    queue_index(db, meeting)
    await invalidate_drafts(db, owner, str(meeting.id))
    db.add(AuditLog(user_id=owner, event_type='meeting_detail_corrected', target_entity='meeting',
        target_id=meeting.id, details={'request_id': str(payload.request_id),
            'candidate_id': payload.candidate_id, 'correction_version': len(history)}))
    await db.flush()
    return result
