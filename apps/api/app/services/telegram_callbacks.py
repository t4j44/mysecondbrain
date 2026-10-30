"""Authenticated, owner-bound buttons delegate to the canonical commitment ledger."""
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.dependencies.database import admin_db_session, rls_db_session
from app.integrations.telegram_client import TelegramClient, bot_identity, delivery_available
from app.models.assistant import MessagingCallbackToken, MessagingUpdateReceipt
from app.schemas.commitment_actions import CommitmentActionInput
from app.services import notification_outbox as outbox
from app.services.assistant_connections import (
    aware,
    connection_for,
    identity_hash,
    nonce_hash,
    owner_lock,
    revoke,
)
from app.services.commitment_actions import act, owned_commitment
from app.services.telegram_delivery import source_button


async def apply_callback(db, owner, update, now):
    callback, message = update.callback_query, update.callback_query.message
    await owner_lock(db, owner)
    token = await db.scalar(select(MessagingCallbackToken).where(MessagingCallbackToken.user_id == owner,
        MessagingCallbackToken.token_hash == nonce_hash(callback.data)).with_for_update())
    if not token or aware(token.expires_at) <= now:
        return None
    row = await outbox.locked_row(db, owner, token.outbox_id)
    connection = await connection_for(db, owner)
    if (not row or not connection or connection.status != 'active'
            or str(connection.id) != str(row.connection_id) or connection.revision != row.connection_revision
            or connection.external_chat_hash != identity_hash('chat', message.chat.id)
            or connection.external_user_hash != identity_hash('user', callback.sender.id)
            or message.date < int(aware(connection.linked_at).timestamp())
            or (row.provider_message_id and row.provider_message_id != str(message.message_id))
            or row.status not in ('dispatching', 'delivered', 'uncertain')):
        return None
    # Stop is deliberately independent of source existence, preferences and send flags.
    if token.action != 'stop':
        await owned_commitment(db, owner, row.commitment_id)
    if token.used_at:
        return token.acknowledgement, [[source_button(row.commitment_id)]]
    if await db.get(MessagingUpdateReceipt, ('telegram', update.update_id)):
        return None
    if token.action != 'stop' and not delivery_available():
        return None
    if row.status in ('dispatching', 'uncertain'):
        # The opaque token was persisted before send, and this authenticated provider
        # update identifies the exact bot, recipient and message. It is receipt evidence.
        row.status, row.provider_message_id, row.delivered_at = 'delivered', str(message.message_id), now
        row.lease_token = row.lease_until = None
        row.error_code, row.updated_at = None, now
        await outbox.finish_attempt(db, owner, row, 'delivered', None, now)
    if token.action == 'stop':
        await revoke(db, owner)
        acknowledgement = 'Reminders stopped. Telegram disconnected.'
    elif await outbox.current_context(db, owner, row) is None:
        acknowledgement = 'This check-in changed. Open Second Brain to review it.'
    else:
        preferences = await outbox.current_context(db, owner, row)
        payload = CommitmentActionInput(request_id=token.id, expected_revision=row.commitment_revision,
            action=token.action, snoozed_until=now + timedelta(hours=1) if token.action == 'snooze' else None,
            timezone=preferences.timezone if token.action == 'snooze' else None)
        await act(db, owner, row.commitment_id, payload)
        acknowledgement = {'done': 'Marked done by you.', 'working': 'Marked as working.',
            'snooze': 'Check-in moved one hour ahead. Quiet hours and daily limits still apply.',
            'help': 'Draft to review: Could we agree on the next step and timing? Review the linked commitment before using it.'}[token.action]
    token.used_at, token.acknowledgement = now, acknowledgement
    db.add(MessagingUpdateReceipt(user_id=owner, connection_id=connection.id,
        provider='telegram', update_id=update.update_id))
    await db.flush()
    return acknowledgement, [] if token.action == 'stop' else [[source_button(row.commitment_id)]]


async def process_callback(update, *, client=None, clock=None):
    callback = update.callback_query
    message = callback.message if callback else None
    if (not callback or not message or message.date == 0 or callback.sender.is_bot
            or message.chat.type != 'private' or message.chat.id != callback.sender.id
            or not message.sender or not message.sender.is_bot or message.sender.id != bot_identity()
            or not re.fullmatch(r'[A-Za-z0-9_-]{32}', callback.data)):
        return
    async with admin_db_session(reason='telegram_callback_owner_lookup') as db:
        owner = await db.scalar(select(MessagingCallbackToken.user_id).where(
            MessagingCallbackToken.token_hash == nonce_hash(callback.data)))
    if not owner:
        return
    try:
        async with rls_db_session(str(owner)) as db:
            feedback = await apply_callback(db, str(owner), update, aware(clock or datetime.now(timezone.utc)))
            await db.commit()
    except (IntegrityError, AuthenticationError, ConflictError, NotFoundError):
        return
    if feedback:
        # Domain commit has succeeded. Lost feedback never rolls it back or sends a new push.
        transport = client or TelegramClient()
        await transport.acknowledge(callback.id, feedback[0])
        await transport.edit(message.chat.id, message.message_id, feedback[0], feedback[1])
