"""Reviewed owner actions on the canonical ledger; no external side effects."""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.jobs.index_queue import queue_index
from app.models.assistant import CommitmentAction
from app.models.entities import (
    ACTIVE_COMMITMENT_STATUSES,
    AuditLog,
    Commitment,
    EntityEdge,
    Meeting,
    Task,
)
from app.schemas.commitment_actions import CommitmentActionInput
from app.schemas.network import CommitmentResponse
from app.services.assistant_connections import owner_lock


async def owned_commitment(db, owner, identity):
    row = await db.scalar(select(Commitment).where(Commitment.id == identity,
        Commitment.user_id == owner, Commitment.deleted_at.is_(None)).with_for_update()
        .execution_options(populate_existing=True))
    if row is None:
        raise NotFoundError('Commitment record not found.')
    return row


async def complete_linked_tasks(db, owner, identity, now):
    links = select(EntityEdge.source_entity_id).where(EntityEdge.user_id == owner,
        EntityEdge.source_entity_type == 'task', EntityEdge.target_entity_type == 'commitment',
        EntityEdge.target_entity_id == identity, EntityEdge.relationship_type == 'fulfills',
        EntityEdge.valid_to.is_(None))
    tasks = (await db.scalars(select(Task).where(Task.user_id == owner, Task.id.in_(links),
        Task.archived_at.is_(None), Task.deleted_at.is_(None)).with_for_update())).all()
    for task in tasks:
        other_links = select(EntityEdge.target_entity_id).where(EntityEdge.user_id == owner,
            EntityEdge.source_entity_type == 'task', EntityEdge.source_entity_id == task.id,
            EntityEdge.target_entity_type == 'commitment', EntityEdge.relationship_type == 'fulfills',
            EntityEdge.valid_to.is_(None))
        unfinished = await db.scalar(select(Commitment.id).where(Commitment.user_id == owner,
            Commitment.id.in_(other_links), Commitment.id != identity,
            Commitment.deleted_at.is_(None), Commitment.status != 'completed').limit(1))
        if not unfinished and task.status != 'done':
            task.status, task.completion_date = 'done', now
            queue_index(db, task)


async def act(db, owner, identity, payload: CommitmentActionInput):
    await owner_lock(db, owner)
    row = await owned_commitment(db, owner, identity)
    values = payload.model_dump(mode='json')
    if payload.snoozed_until:
        values['snoozed_until'] = payload.snoozed_until.astimezone(timezone.utc).isoformat()
    fingerprint = hashlib.sha256(json.dumps({'commitment_id': str(row.id), **values}, sort_keys=True).encode()).hexdigest()
    prior = await db.scalar(select(CommitmentAction).where(CommitmentAction.user_id == owner,
        CommitmentAction.request_id == str(payload.request_id)))
    if prior:
        if prior.request_hash != fingerprint:
            raise ConflictError('This request already recorded a different action. Reload the commitment.')
        return prior.receipt
    if row.revision != payload.expected_revision:
        raise ConflictError('This commitment changed. Reload and review it before acting.')
    if row.status not in ACTIVE_COMMITMENT_STATUSES:
        raise ConflictError('This commitment is already closed. Reload its current state.')
    now = datetime.now(timezone.utc)
    help_result = None
    if payload.action == 'snooze':
        target = payload.snoozed_until
        if target is None or not now < target <= now + timedelta(days=365):
            raise ValidationError('Choose a future reminder time within the next year.')
        row.status, row.reminder_at, row.source_timezone = 'snoozed', target, payload.timezone
    elif payload.action in ('done', 'working', 'cancel'):
        row.status = {'done': 'completed', 'working': 'in_progress', 'cancel': 'cancelled'}[payload.action]
        row.completed_at = now if payload.action == 'done' else None
        row.reminder_at = None
        if payload.action == 'done':
            await complete_linked_tasks(db, owner, row.id, now)
    else:
        sources = [{'kind': 'commitment', 'id': str(row.id), 'uri': f'/sources/commitment/{row.id}'}]
        if row.meeting_id:
            meeting = await db.scalar(select(Meeting).where(Meeting.id == row.meeting_id,
                Meeting.user_id == owner, Meeting.archived_at.is_(None), Meeting.deleted_at.is_(None)))
            if meeting:
                sources.append({'kind': 'meeting', 'id': str(meeting.id), 'uri': f'/meetings/{meeting.id}'})
        help_result = {'label': 'Draft to review', 'text': f'Could we agree on the next step for: {row.description[:1000]}?',
            'suggestion': 'Review the source and edit this draft before using it.', 'sources': sources}
    if payload.action != 'help':
        await db.flush()
        await db.refresh(row)
        from app.services.notification_outbox import cancel_pending, enqueue_check_in
        await cancel_pending(db, owner, row.id)
        if payload.action == 'snooze':
            await enqueue_check_in(db, owner, row)
        queue_index(db, row)
    result = {'commitment': CommitmentResponse.model_validate(row).model_dump(mode='json'),
        'action': payload.action, 'self_reported': payload.action == 'done', 'help': help_result}
    db.add(CommitmentAction(user_id=owner, commitment_id=row.id, request_id=str(payload.request_id),
        action=payload.action, request_hash=fingerprint, receipt=result))
    db.add(AuditLog(user_id=owner, event_type='commitment_action', target_entity='commitment',
        target_id=row.id, details={'action': payload.action, 'revision': row.revision,
            'request_id': str(payload.request_id), 'self_reported': payload.action == 'done'}))
    await db.flush()
    return result
