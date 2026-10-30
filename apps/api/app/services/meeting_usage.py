"""Atomic usage updates under RLS. Callers own the transaction."""
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.core.config import settings
from app.core.errors import AppError
from app.models.meeting_intelligence import UsageCounter

METRIC = 'meeting_audio_seconds'


def month_start(now: datetime | None = None) -> datetime:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def quota_view(db, owner):
    used = await db.scalar(select(UsageCounter.quantity).where(UsageCounter.user_id == owner,
        UsageCounter.metric == METRIC, UsageCounter.period_start == month_start())) or 0
    limit = settings.MEETING_AUDIO_MONTHLY_LIMIT_SECONDS
    return {'used_seconds': used, 'limit_seconds': limit, 'remaining_seconds': max(0, limit-used),
        'percentage_used': round(min(100, used / limit * 100), 2), 'period_start': month_start(),
        'data_mode': settings.AI_DATA_MODE, 'max_bytes': settings.MEETING_AUDIO_MAX_BYTES,
        'retention_days': settings.MEETING_AUDIO_RETENTION_DAYS}


async def charge(db, capture, target_seconds: int):
    delta = max(0, target_seconds - capture.charged_seconds)
    if not delta:
        return
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert = pg_insert if db.bind.dialect.name == 'postgresql' else sqlite_insert
    await db.execute(insert(UsageCounter).values(user_id=capture.user_id, metric=METRIC,
        period_start=capture.period_start, quantity=0).on_conflict_do_nothing())
    result = await db.execute(update(UsageCounter).where(UsageCounter.user_id == capture.user_id,
        UsageCounter.metric == METRIC, UsageCounter.period_start == capture.period_start,
        UsageCounter.quantity + delta <= settings.MEETING_AUDIO_MONTHLY_LIMIT_SECONDS)
        .values(quantity=UsageCounter.quantity+delta, updated_at=datetime.now(timezone.utc)))
    if result.rowcount != 1:
        raise AppError("You've used your meeting allowance for this month.", code='MEETING_QUOTA_EXCEEDED', status_code=429)
    capture.charged_seconds += delta
