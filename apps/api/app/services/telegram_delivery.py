"""Persist intent, recheck permissions, then make one bounded provider call."""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.config import settings
from app.core.errors import IntegrationError
from app.core.security import decrypt_token
from app.dependencies.database import rls_db_session
from app.integrations.telegram_client import TelegramClient, delivery_available
from app.models.assistant import MessagingCallbackToken, MessagingConnection
from app.models.entities import Commitment
from app.services import notification_outbox as outbox
from app.services.assistant_connections import aware, identity_hash, nonce_hash


def source_button(identity):
    return {'text': 'Open in Second Brain',
        'url': f'{settings.FRONTEND_URL.rstrip("/")}/sources/commitment/{identity}'}


async def issue_buttons(db, owner, row, now):
    # Only definitively rejected sends are retried. Their unused buttons become invalid.
    await db.execute(delete(MessagingCallbackToken).where(MessagingCallbackToken.user_id == owner,
        MessagingCallbackToken.outbox_id == row.id, MessagingCallbackToken.used_at.is_(None)))
    buttons = []
    for action, label in [('done', 'Done'), ('working', 'Working'), ('snooze', 'Snooze 1h'),
            ('help', 'Help'), ('stop', 'Stop reminders')]:
        raw = secrets.token_urlsafe(24)
        db.add(MessagingCallbackToken(user_id=owner, outbox_id=row.id, token_hash=nonce_hash(raw),
            action=action, expires_at=now + timedelta(days=7)))
        buttons.append({'text': label, 'callback_data': raw})
    await db.flush()
    return [buttons[:2], buttons[2:4], [buttons[4]], [source_button(row.commitment_id)]]


async def deliver_one(owner, identity, *, client=None, clock=None):
    if not delivery_available():
        return
    now = aware(clock or datetime.now(timezone.utc))
    async with rls_db_session(owner) as db:
        token = await outbox.claim(db, owner, identity, clock=now)
        await db.commit()
    if not token:
        return
    async with rls_db_session(owner) as db:
        started = await outbox.begin_dispatch(db, owner, identity, token, clock=now)
        row = await outbox.locked_row(db, owner, identity)
        keyboard = await issue_buttons(db, owner, row, now) if started else []
        await db.commit()
    if not started:
        return
    async with rls_db_session(owner) as db:
        row = await outbox.locked_row(db, owner, identity)
        now = aware(clock or datetime.now(timezone.utc))
        if (not row or row.status != 'dispatching' or str(row.lease_token) != token
                or aware(row.lease_until) <= now):
            return
        if not delivery_available():
            await outbox.settle(db, owner, identity, token, 'failed', clock=now)
            row.error_code = 'DELIVERY_DISABLED'
            await outbox.finish_attempt(db, owner, row, 'failed', row.error_code, now)
            await db.commit()
            return
        if not await outbox.eligible(db, owner, row, now):
            await outbox.finish_attempt(db, owner, row, 'failed', 'PERMISSION_RECHECK', now)
            await db.commit()
            return
        connection = await db.get(MessagingConnection, row.connection_id)
        preferences = await outbox.current_context(db, owner, row)
        try:
            chat_id = int(decrypt_token(connection.encrypted_chat_id))
            user_id = int(decrypt_token(connection.encrypted_user_id))
            if (not 0 < chat_id < 2**52 or user_id != chat_id
                    or connection.external_chat_hash != identity_hash('chat', chat_id)
                    or connection.external_user_hash != identity_hash('user', user_id)):
                raise ValueError('Invalid private destination.')
        except (ValueError, IntegrationError):
            await outbox.settle(db, owner, identity, token, 'failed', clock=now)
            row.error_code = 'INVALID_DESTINATION'
            await outbox.finish_attempt(db, owner, row, 'failed', row.error_code, now)
            await db.commit()
            return
        message = 'Your check-in is ready. How is it going?'
        if preferences.include_details:
            commitment = await db.get(Commitment, row.commitment_id)
            message += '\n\n' + commitment.description[:1000]
        # Owner, source and connection locks remain held through the bounded call.
        result = await (client or TelegramClient()).send(chat_id, message, keyboard)
        finished = aware(clock or datetime.now(timezone.utc))
        await outbox.settle(db, owner, identity, token, result.status,
            provider_message_id=result.message_id, clock=finished)
        row.error_code = None if result.status == 'delivered' else result.code
        await outbox.finish_attempt(db, owner, row, result.status, row.error_code, finished)
        if (result.status == 'failed' and result.code == 'RATE_LIMITED'
                and result.retry_after and row.attempt_count < 3):
            # A valid 429 explicitly rejected the request. Ambiguous outcomes never retry.
            row.status, row.available_at = 'queued', finished + timedelta(seconds=result.retry_after)
            row.lease_token = None
        await db.commit()


async def due_items(now):
    from app.dependencies.database import admin_db_session
    from app.models.assistant import NotificationOutbox
    async with admin_db_session(reason='telegram_due_owner_lookup') as db:
        return (await db.execute(select(NotificationOutbox.user_id, NotificationOutbox.id).where(
            ((NotificationOutbox.status == 'queued') & (NotificationOutbox.available_at <= now))
            | (NotificationOutbox.status.in_(('leased', 'dispatching')) & (NotificationOutbox.lease_until <= now)))
            .order_by(NotificationOutbox.available_at, NotificationOutbox.id).limit(20))).all()


async def delivery_worker():
    import asyncio

    from app.core.errors import AuthenticationError, NotFoundError
    from app.core.logging import logger
    while True:
        try:
            if delivery_available():
                for owner, identity in await due_items(datetime.now(timezone.utc)):
                    try:
                        async with rls_db_session(str(owner)) as db:
                            await outbox.recover_expired(db, str(owner))
                            await db.commit()
                        await deliver_one(str(owner), identity)
                    except (AuthenticationError, NotFoundError):
                        continue
                    except Exception:
                        # URL/exception text may contain a provider credential or private data.
                        logger.error('Telegram delivery item interrupted; persisted intent will be recovered.')
        except Exception:
            logger.error('Telegram delivery scan interrupted.')
        await asyncio.sleep(15)
