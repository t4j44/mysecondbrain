"""Small, explicit calendar windows over canonical events; no inferred history."""
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select

from app.ai.relationship_queries import answer
from app.models.entities import (
    Commitment,
    ContextEvent,
    EntityEdge,
    Person,
    Profile,
    Project,
    Venture,
)


def time_window(expression, zone, clock=None):
    local = (clock or datetime.now(timezone.utc)).astimezone(ZoneInfo(zone))
    today = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if expression == 'yesterday':
        start, end = today - timedelta(days=1), today
    elif expression == 'last week':
        end = today - timedelta(days=today.weekday())
        start = end - timedelta(days=7)
    elif expression == 'last month':
        end = today.replace(day=1)
        start = (end - timedelta(days=1)).replace(day=1)
    elif expression in {'the last 30 days', 'last 30 days'}:
        start, end = local - timedelta(days=30), local
    else:
        match = re.fullmatch(r'between (\d{4}-\d{2}-\d{2}) and (\d{4}-\d{2}-\d{2})', expression)
        if not match:
            return None
        start, end = [datetime.fromisoformat(value).replace(tzinfo=ZoneInfo(zone)) for value in match.groups()]
        end += timedelta(days=1)  # both stated calendar dates included
        if end <= start or (end - start).days > 366:
            raise ValueError('Choose an ordered range of at most 366 calendar days.')
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


async def temporal_answer(db, owner, prompt, device_timezone=None):
    normalized = prompt.strip().rstrip('?! .')
    match = re.fullmatch(
        r'(?i)(what did i work on|what ai sessions did i record|what happened(?: with (.+?))?|'
        r'what changed with (.+?)|what commitments did i create) '
        r'(yesterday|last week|last month|(?:the )?last 30 days|between \d{4}-\d{2}-\d{2} and \d{4}-\d{2}-\d{2})', normalized)
    if not match:
        return None
    profile = await db.get(Profile, owner)
    zone = device_timezone or (profile.timezone if profile else None) or 'UTC'
    try:
        window = time_window(match.group(4).casefold(), zone)
    except (ValueError, KeyError):
        return answer(['Use a valid IANA timezone and an ordered YYYY-MM-DD date range of at most 366 days.'], [])
    if window is None:
        return None
    start, end = window
    scope = match.group(2) or match.group(3)
    entity = None
    if scope:
        candidates = []
        for kind, model in [('person', Person), ('project', Project), ('venture', Venture)]:
            rows = (await db.execute(select(model).where(model.user_id == owner,
                model.deleted_at.is_(None), model.archived_at.is_(None),
                func.lower(model.name) == scope.casefold()).limit(10))).scalars().all()
            candidates.extend((kind, row) for row in rows)
        if len(candidates) != 1:
            return answer(['Choose a specific saved person, project or venture; this name is missing or ambiguous.'], [
                {'id': str(row.id), 'kind': kind, 'title': row.name, 'uri': f'/sources/{kind}/{row.id}'} for kind, row in candidates])
        entity = candidates[0]
    commitments = match.group(1).casefold().startswith('what commitments')
    model = Commitment if commitments else ContextEvent
    date_column = Commitment.created_at if commitments else ContextEvent.occurred_at
    conditions = [model.user_id == owner, model.deleted_at.is_(None), date_column >= start, date_column < end]
    if commitments:
        conditions.append(Commitment.archived_at.is_(None))
    else:
        conditions.append(ContextEvent.privacy_class == 'private')
        if 'ai sessions' in match.group(1).casefold() or 'work on' in match.group(1).casefold():
            conditions.append(ContextEvent.event_type.in_(['ai_session', 'work_session', 'project_update']))
        if entity:
            kind, row = entity
            event_ids = select(EntityEdge.source_event_id).where(EntityEdge.user_id == owner,
                EntityEdge.target_entity_type == kind, EntityEdge.target_entity_id == row.id)
            conditions.append(or_(getattr(ContextEvent, kind + '_id') == row.id, ContextEvent.id.in_(event_ids)))
    rows = (await db.execute(select(model).where(*conditions).order_by(date_column, model.id).limit(51))).scalars().all()
    lines = [f'Saved records in {zone}: {start.astimezone(ZoneInfo(zone)).isoformat()} to '
             f'{end.astimezone(ZoneInfo(zone)).isoformat()} (end excluded).']
    citations = []
    for row in rows[:50]:
        kind = 'commitment' if commitments else 'context_event'
        title = row.description if commitments else row.title
        stamp = row.created_at if commitments else row.occurred_at
        stamp = stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
        summary = row.description if commitments else row.summary or row.title
        source = 'recorded commitment' if commitments else f'{row.source_type}/{row.source_provider or "user"}'
        lines.append(f'[{len(citations) + 1}] {stamp.astimezone(ZoneInfo(zone)).isoformat()} — {summary} ({source})')
        citations.append({'id': str(row.id), 'kind': kind, 'title': title,
                          'snippet': summary, 'uri': f'/sources/{kind}/{row.id}'})
    if not rows:
        lines.append('No supporting records in this window. This does not prove nothing happened.')
    if len(rows) > 50:
        lines.append('Showing the first 50 records. Narrow the dates for a complete answer.')
    return answer(lines, citations)
