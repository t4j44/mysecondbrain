"""Durable reminder safety boundary. No provider transport is wired in this slice."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select

from app.core.config import settings
from app.models.assistant import AssistantPreferences, MessagingConnection, NotificationOutbox
from app.models.entities import ACTIVE_COMMITMENT_STATUSES, AuditLog, Commitment
from app.services.assistant_connections import aware, linking_available, owner_lock

LEASE_DURATION = timedelta(minutes=5)


def enabled():
    return settings.ASSISTANT_OUTBOX_ENABLED and linking_available()


def next_allowed_time(now, preferences):
    """Advance in UTC through missing/repeated local minutes; never guess a DST offset."""
    now = aware(now).astimezone(timezone.utc)
    if not preferences.quiet_enabled:
        return now
    zone = ZoneInfo(preferences.timezone)
    start, end = preferences.quiet_start_minute, preferences.quiet_end_minute
    if start == end:
        raise ValueError('A quiet window must have distinct endpoints.')
    for minute in range(48 * 60 + 1):
        candidate = now if minute == 0 else now.replace(second=0, microsecond=0) + timedelta(minutes=minute)
        local = candidate.astimezone(zone)
        clock = local.hour * 60 + local.minute
        silent = start <= clock < end if start < end else clock >= start or clock < end
        if not silent:
            return candidate
    raise ValueError('No safe notification time found.')


async def cancel_pending(db, owner, commitment_id=None):
    query = select(NotificationOutbox).where(NotificationOutbox.user_id == owner,
        NotificationOutbox.status.in_(('queued', 'leased')))
    if commitment_id is not None:
        query = query.where(NotificationOutbox.commitment_id == commitment_id)
    for row in (await db.scalars(query.with_for_update())).all():
        row.status, row.error_code = 'cancelled', 'SOURCE_OR_PERMISSION_CHANGED'
        row.lease_token = row.lease_until = None
        row.updated_at = datetime.now(timezone.utc)


async def enqueue_check_in(db, owner, commitment):
    """Called only for an explicit Snooze. Caller commits it atomically with that action."""
    if not enabled():
        return None
    await owner_lock(db, owner)
    preferences = await db.get(AssistantPreferences, owner, populate_existing=True)
    connection = await db.scalar(select(MessagingConnection).where(
        MessagingConnection.user_id == owner, MessagingConnection.provider == 'telegram'))
    if (not preferences or not preferences.telegram_enabled or not preferences.consent_at
            or preferences.revoked_at or not connection or connection.status != 'active'
            or not connection.encrypted_chat_id or commitment.status != 'snoozed'
            or not commitment.reminder_at or not commitment.source_timezone
            or str(commitment.user_id) != owner or commitment.deleted_at):
        return None
    row = await db.scalar(select(NotificationOutbox).where(NotificationOutbox.user_id == owner,
        NotificationOutbox.commitment_id == commitment.id, NotificationOutbox.commitment_revision == commitment.revision,
        NotificationOutbox.channel == 'telegram', NotificationOutbox.slot == 'explicit_check_in'))
    if row:
        return row
    row = NotificationOutbox(user_id=owner, commitment_id=commitment.id,
        commitment_revision=commitment.revision, connection_id=connection.id,
        connection_revision=connection.revision, preferences_version=preferences.version,
        scheduled_at=commitment.reminder_at, available_at=commitment.reminder_at)
    db.add(row)
    await db.flush()
    return row


async def current_context(db, owner, row):
    commitment = await db.scalar(select(Commitment).where(Commitment.id == row.commitment_id,
        Commitment.user_id == owner).with_for_update().execution_options(populate_existing=True))
    preferences = await db.get(AssistantPreferences, owner, populate_existing=True)
    connection = await db.scalar(select(MessagingConnection).where(MessagingConnection.id == row.connection_id,
        MessagingConnection.user_id == owner).with_for_update().execution_options(populate_existing=True))
    if (not commitment or commitment.deleted_at or commitment.status not in ACTIVE_COMMITMENT_STATUSES
            or commitment.revision != row.commitment_revision
            or aware(commitment.reminder_at) != aware(row.scheduled_at)
            or not preferences or not preferences.telegram_enabled or not preferences.consent_at
            or preferences.revoked_at or preferences.version != row.preferences_version
            or not connection or connection.status != 'active' or not connection.encrypted_chat_id
            or connection.revision != row.connection_revision):
        return None
    return preferences


async def quota_available(db, owner, row, preferences, now):
    local = now.astimezone(ZoneInfo(preferences.timezone))
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    # Respect the entire local day AND a rolling 24h window; timezone changes cannot reset usage.
    since = min(midnight, now - timedelta(hours=24))
    count = await db.scalar(select(func.count()).select_from(NotificationOutbox).where(
        NotificationOutbox.user_id == owner, NotificationOutbox.id != row.id,
        or_((NotificationOutbox.status == 'leased') & (NotificationOutbox.lease_until > now),
            NotificationOutbox.status.in_(('dispatching', 'delivered', 'uncertain', 'failed'))
            & (NotificationOutbox.dispatch_started_at >= since))))
    return count < preferences.daily_cap


async def eligible(db, owner, row, now):
    if now > aware(row.scheduled_at) + timedelta(hours=24):
        row.status, row.error_code = 'cancelled', 'CHECK_IN_EXPIRED'
        row.lease_token = row.lease_until = None
        row.updated_at = now
        return False
    preferences = await current_context(db, owner, row)
    if preferences is None:
        row.status, row.error_code = 'cancelled', 'SOURCE_OR_PERMISSION_CHANGED'
        row.lease_token = row.lease_until = None
        row.updated_at = now
        return False
    allowed = next_allowed_time(now, preferences)
    if allowed > now or not await quota_available(db, owner, row, preferences, now):
        row.status = 'queued'
        row.available_at = allowed if allowed > now else now + timedelta(hours=1)
        row.lease_token = row.lease_until = None
        row.updated_at = now
        return False
    return True


async def locked_row(db, owner, identity):
    await owner_lock(db, owner)
    return await db.scalar(select(NotificationOutbox).where(NotificationOutbox.id == identity,
        NotificationOutbox.user_id == owner).with_for_update().execution_options(populate_existing=True))


async def claim(db, owner, identity, *, clock=None):
    """Reserve capacity before a future sender; commit before using the lease token."""
    if not enabled():
        return None
    now = aware(clock or datetime.now(timezone.utc))
    row = await locked_row(db, owner, identity)
    if not row or row.status != 'queued' or aware(row.available_at) > now:
        return None
    if not await eligible(db, owner, row, now):
        await db.flush()
        return None
    row.status, row.lease_token, row.lease_until = 'leased', str(uuid4()), now + LEASE_DURATION
    row.updated_at = now
    await db.flush()
    return str(row.lease_token)


async def begin_dispatch(db, owner, identity, token, *, clock=None):
    """Persist intent before transport. A crash after this point is uncertain, never replayed."""
    if not enabled():
        return False
    now = aware(clock or datetime.now(timezone.utc))
    row = await locked_row(db, owner, identity)
    if (not row or row.status != 'leased' or str(row.lease_token) != token
            or aware(row.lease_until) <= now):
        return False
    if not await eligible(db, owner, row, now):
        await db.flush()
        return False
    row.status, row.dispatch_started_at = 'dispatching', now
    row.lease_until, row.updated_at = now + LEASE_DURATION, now
    await db.flush()
    return True


async def settle(db, owner, identity, token, outcome, *, provider_message_id=None, clock=None):
    if outcome not in ('delivered', 'uncertain', 'failed'):
        raise ValueError('Unsupported delivery outcome.')
    if outcome == 'delivered' and (not isinstance(provider_message_id, str)
            or not provider_message_id.isascii() or not provider_message_id.isdecimal()
            or not 0 < len(provider_message_id) <= 100):
        raise ValueError('Delivery requires a real provider message identifier.')
    row = await locked_row(db, owner, identity)
    if not row or row.status != 'dispatching' or str(row.lease_token) != token:
        return False
    now = aware(clock or datetime.now(timezone.utc))
    row.status, row.updated_at = outcome, now
    row.provider_message_id = provider_message_id if outcome == 'delivered' else None
    row.delivered_at = now if outcome == 'delivered' else None
    row.error_code = {'uncertain': 'DELIVERY_UNKNOWN', 'failed': 'PROVIDER_REJECTED'}.get(outcome)
    row.lease_until = None
    db.add(AuditLog(user_id=owner, event_type='notification_delivery_state', target_entity='notification',
        target_id=row.id, details={'status': outcome, 'channel': row.channel}))
    await db.flush()
    return True


async def recover_expired(db, owner, *, clock=None):
    await owner_lock(db, owner)
    now = aware(clock or datetime.now(timezone.utc))
    rows = (await db.scalars(select(NotificationOutbox).where(NotificationOutbox.user_id == owner,
        NotificationOutbox.status.in_(('leased', 'dispatching')), NotificationOutbox.lease_until <= now)
        .with_for_update())).all()
    for row in rows:
        row.status = 'uncertain' if row.status == 'dispatching' else 'queued'
        row.error_code = 'DELIVERY_UNKNOWN' if row.status == 'uncertain' else None
        row.lease_token = row.lease_until = None
        row.updated_at = now
    await db.flush()
    return len(rows)
