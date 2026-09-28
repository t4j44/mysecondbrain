"""Owner-scoped event provenance. Callers own the transaction and confirmation gate."""
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, select, text

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.jobs.index_queue import delete_index, queue_index
from app.models.entities import (
    ContextEvent,
    ContextMedia,
    EntityEdge,
    Interaction,
    JobRecord,
    Person,
    PortfolioCaseStudy,
    RelationshipAction,
)


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError('Choose an IANA timezone such as Asia/Dhaka.') from exc
    return value


class EventInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirmed: Literal[True]
    request_id: UUID
    event_type: str = Field(default='manual_capture', min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=4000)
    occurred_at: AwareDatetime
    timezone: str = Field(default='UTC', max_length=100)
    raw_text: str = Field(default='', max_length=64000)
    person_id: UUID | None = None
    project_id: UUID | None = None
    venture_id: UUID | None = None
    privacy_class: Literal['private', 'restricted'] = 'private'

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        return validate_timezone(value)


async def create_event(db, owner, *, key, **values):
    """Serializes replay before mutation; never rewrites the original event on retry."""
    from app.ai.indexing import owned_record
    if db.bind.dialect.name == 'postgresql':
        await db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key, 29))'),
                         {'key': f'{owner}:{key}'})
    prior = (await db.execute(select(ContextEvent).where(ContextEvent.user_id == owner,
        ContextEvent.idempotency_key == key))).scalar_one_or_none()
    if prior:
        if prior.deleted_at:
            raise ConflictError('This event was deleted. Use a new request to save new context.')
        return prior, False
    for kind in ('person', 'project', 'venture'):
        if values.get(kind + '_id'):
            await owned_record(db, owner, kind, str(values[kind + '_id']))
    if len(values.get('raw_text') or '') > 64000 or len(json.dumps(values.get('raw_payload', {})).encode()) > 120000:
        raise ConflictError('Context exceeds the beta event size limit.')
    event = ContextEvent(user_id=owner, idempotency_key=key, **values)
    db.add(event)
    await db.flush()
    if event.privacy_class == 'private':
        queue_index(db, event)
    for kind in ('person', 'project', 'venture'):
        if getattr(event, kind + '_id'):
            await event_link(db, event, kind, getattr(event, kind + '_id'), derived=False)
    return event, True


async def event_link(db, event, kind, identity, *, derived=True):
    relation = 'derived_record' if derived else 'references'
    existing = await db.scalar(select(EntityEdge.id).where(EntityEdge.user_id == event.user_id,
        EntityEdge.source_event_id == event.id, EntityEdge.source_entity_type == 'context_event',
        EntityEdge.target_entity_type == kind, EntityEdge.target_entity_id == str(identity),
        EntityEdge.relationship_type == relation, EntityEdge.valid_to.is_(None)))
    if existing:
        return
    edge = EntityEdge(user_id=event.user_id, source_entity_type='context_event',
        source_entity_id=event.id, target_entity_type=kind, target_entity_id=str(identity),
        relationship_type=relation, source_event_id=event.id,
        occurred_at=event.occurred_at, valid_from=event.occurred_at,
        metadata_payload={'confirmed': True})
    db.add(edge)


async def current_edge(db, *, event=None, **values):
    """Close the previous identical fact rather than losing its provenance."""
    keys = ('user_id', 'source_entity_type', 'source_entity_id', 'target_entity_type',
            'target_entity_id', 'relationship_type')
    prior = (await db.execute(select(EntityEdge).where(
        *(getattr(EntityEdge, key) == values[key] for key in keys), EntityEdge.valid_to.is_(None)
    ).with_for_update())).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if prior:
        prior.valid_to = now
        await db.flush()
    db.add(EntityEdge(**values, valid_from=now, occurred_at=event.occurred_at if event else now,
        source_event_id=event.id if event else None))


async def get_event(db, owner, identity):
    row = (await db.execute(select(ContextEvent).where(ContextEvent.user_id == owner,
        ContextEvent.id == str(identity), ContextEvent.deleted_at.is_(None)))).scalar_one_or_none()
    if not row:
        raise NotFoundError('Context event is not available.')
    return row


def event_view(event):
    return {key: getattr(event, key) for key in ('id', 'event_type', 'title', 'summary',
        'occurred_at', 'recorded_at', 'updated_at', 'timezone', 'source_type', 'source_provider',
        'person_id', 'project_id', 'venture_id', 'privacy_class')} | {'metadata': event.metadata_payload}


async def event_list(db, owner, *, person_id=None, project_id=None, start=None, end=None, limit=50):
    conditions = [ContextEvent.user_id == owner, ContextEvent.deleted_at.is_(None)]
    for column, value in ((ContextEvent.person_id, person_id), (ContextEvent.project_id, project_id)):
        if value:
            conditions.append(column == str(value))
    if start:
        conditions.append(ContextEvent.occurred_at >= start)
    if end:
        conditions.append(ContextEvent.occurred_at < end)
    events = (await db.execute(select(ContextEvent).where(*conditions)
        .order_by(ContextEvent.occurred_at.desc(), ContextEvent.id).limit(limit))).scalars().all()
    media = (await db.execute(select(ContextMedia).where(ContextMedia.user_id == owner,
        ContextMedia.event_id.in_([e.id for e in events])))).scalars().all()
    return [{**event_view(e), 'media': [{'id': str(m.id), 'kind': m.kind, 'width': m.width,
        'height': m.height} for m in media if m.event_id == e.id]} for e in events]


def erase_media(db, row):
    for path in (row.storage_path, row.thumbnail_path):
        db.add(JobRecord(user_id=row.user_id, job_type='storage_delete', status='pending',
            result_payload={'bucket': settings.STORAGE_BUCKET_DOCUMENTS, 'path': path}))


async def delete_event(db, owner, identity):
    """Remove derived context and media access immediately; object erasure is durable/retryable."""
    from app.ai.indexing import SOURCES
    from app.services.person_context import invalidate_drafts
    event = await get_event(db, owner, identity)
    edges = (await db.execute(select(EntityEdge).where(EntityEdge.user_id == owner,
        EntityEdge.source_event_id == event.id))).scalars().all()
    now = datetime.now(timezone.utc)
    record_ids = {str(event.id)}
    for edge in edges:
        if edge.relationship_type != 'derived_record' or edge.target_entity_type not in {*SOURCES, 'portfolio_case_study'}:
            continue
        model = PortfolioCaseStudy if edge.target_entity_type == 'portfolio_case_study' else SOURCES[edge.target_entity_type][0]
        row = (await db.execute(select(model).where(model.user_id == owner,
            model.id == edge.target_entity_id))).scalar_one_or_none()
        if row:
            row.deleted_at = now
            record_ids.add(str(row.id))
            await delete_index(db, row)
            await invalidate_drafts(db, owner, str(row.id))
    media = (await db.execute(select(ContextMedia).where(ContextMedia.user_id == owner,
        ContextMedia.event_id == event.id))).scalars().all()
    for item in media:
        erase_media(db, item)
        await db.delete(item)
    receipts = (await db.execute(select(RelationshipAction).where(RelationshipAction.user_id == owner))).scalars().all()
    opened_id = (event.metadata_payload or {}).get('opened_id')
    for receipt in receipts:
        if (receipt.receipt or {}).get('context_event_id') == str(event.id) or str(receipt.id) == opened_id:
            # Retain only replay metadata. Retries must not recreate a deleted outcome.
            receipt.outcome = None
            receipt.receipt = {'deleted': True, 'context_event_id': str(event.id)}
    jobs = (await db.execute(select(JobRecord).where(JobRecord.user_id == owner,
        JobRecord.job_type.in_(['capture_draft', 'index_record'])))).scalars().all()
    for job in jobs:
        payload = job.result_payload or {}
        if str(job.id) == event.source_external_id or str(payload.get('record_id')) in record_ids:
            await db.delete(job)
    await invalidate_drafts(db, owner, str(event.id))
    await delete_index(db, event)
    await db.execute(delete(EntityEdge).where(EntityEdge.user_id == owner, EntityEdge.source_event_id == event.id))
    event.deleted_at = now
    # Keep a content-free replay tombstone, so retries cannot resurrect erased context.
    event.raw_text, event.raw_payload, event.summary, event.title = None, {}, None, 'Deleted context'
    event.metadata_payload = {}
    if event.person_id:
        await db.flush()
        person = await db.get(Person, event.person_id)
        if person and str(person.user_id) == str(owner):
            person.last_interaction_at = await db.scalar(select(func.max(Interaction.date)).where(
                Interaction.user_id == owner, Interaction.person_id == person.id,
                Interaction.deleted_at.is_(None), Interaction.archived_at.is_(None)))
