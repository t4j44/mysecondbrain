"""Private beta measurements: facts and approved outcomes, never inferred success."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import func, select

from app.models.entities import (
    AuditLog,
    Commitment,
    EntityEdge,
    Interaction,
    Person,
    Project,
    RelationshipAction,
)
from app.services.relationships import active, utc


class WillingnessInput(BaseModel):
    response: Literal['yes', 'no', 'unsure']


async def activation(db, owner):
    counts = {}
    for name, model in [('people', Person), ('interactions', Interaction), ('projects', Project), ('commitments', Commitment)]:
        counts[name] = await db.scalar(select(func.count()).select_from(model).where(*active(model, owner)))
    counts['ask_answers'] = await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.user_id == owner,
        AuditLog.event_type == 'relationship_ask_answered'))
    counts['connections'] = await db.scalar(select(func.count()).select_from(EntityEdge).where(EntityEdge.user_id == owner))
    targets = {'people': 5, 'interactions': 3, 'projects': 1, 'commitments': 1, 'ask_answers': 1}
    activated = all(counts[key] >= target for key, target in targets.items())
    first_activation = await db.scalar(select(func.min(AuditLog.timestamp)).where(AuditLog.user_id == owner, AuditLog.event_type == 'relationship_activated'))
    if activated and not first_activation:
        first_activation = datetime.now(timezone.utc)
        db.add(AuditLog(user_id=owner, event_type='relationship_activated', details={'definition': 1}))
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    successes = await db.scalar(select(func.count()).select_from(RelationshipAction).where(RelationshipAction.user_id == owner,
        RelationshipAction.action == 'completed', RelationshipAction.created_at >= cutoff))
    return {'counts': counts, 'targets': targets, 'activated': activated, 'first_activated_at': first_activation,
        'successful_actions_last_7_days': successes,
        'definition': 'Five people, three recorded interactions, one project, one commitment and one Ask response with supporting evidence.',
        'success_definition': 'An approved follow-up with a recorded outcome. Views and AI suggestions do not count as success.'}


async def record_home_observation(db, owner, followups):
    """Count distinct served evidence keys; refreshes do not invent new suggestions."""
    import hashlib
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    seen = await db.scalar(select(AuditLog.id).where(AuditLog.user_id == owner,
        AuditLog.event_type == 'relationship_home_view', AuditLog.timestamp >= cutoff).limit(1))
    if not seen:
        db.add(AuditLog(user_id=owner, event_type='relationship_home_view', details={}))
    keys = {hashlib.sha256(item['key'].encode()).hexdigest() for item in followups}
    hashes = set((await db.execute(select(AuditLog.request_id).where(AuditLog.user_id == owner,
        AuditLog.event_type == 'relationship_suggestion_served', AuditLog.request_id.in_(keys)))).scalars().all())
    for item in followups:
        key = hashlib.sha256(item['key'].encode()).hexdigest()
        if key not in hashes:
            db.add(AuditLog(user_id=owner, event_type='relationship_suggestion_served', request_id=key, details={}))
            hashes.add(key)


async def private_activity(db, owner):
    now = datetime.now(timezone.utc)
    events = (await db.execute(select(AuditLog.event_type, AuditLog.timestamp).where(AuditLog.user_id == owner,
        AuditLog.timestamp >= now - timedelta(days=56)).order_by(AuditLog.timestamp.desc()).limit(10000))).all()
    weeks = []
    monday = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
    for offset in range(8):
        start = monday - timedelta(days=7 * offset)
        end = start + timedelta(days=7)
        kinds = [kind for kind, date in events if start <= utc(date) < end]
        weeks.append({'week_start': start.date().isoformat(), 'active': bool(kinds),
            'followups_completed': kinds.count('relationship_action_completed'),
            'suggestions_served': kinds.count('relationship_suggestion_served'),
            'ask_answers': kinds.count('relationship_ask_answered')})
    willingness = await db.scalar(select(AuditLog.event_type).where(AuditLog.user_id == owner,
        AuditLog.event_type.in_(['willingness_to_pay_yes', 'willingness_to_pay_no', 'willingness_to_pay_unsure']))
        .order_by(AuditLog.timestamp.desc()).limit(1))
    return {'weeks': weeks, 'willingness_to_pay': willingness.removeprefix('willingness_to_pay_') if willingness else None,
        'notice': 'Only your activity. No signup, revenue or testimonial claims are inferred. Calendar weeks use UTC.'}
