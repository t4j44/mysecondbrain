"""Explicit account linking. This module never sends a Telegram message."""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings, settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.security import encrypt_token
from app.dependencies.database import admin_db_session, rls_db_session
from app.models.assistant import AssistantPreferences, MessagingConnection, MessagingUpdateReceipt
from app.models.entities import AuditLog
from app.schemas.assistant import AssistantPreferencesUpdate, TelegramUpdate
from app.services.account import require_active


def linking_available():
    return bool(settings.TELEGRAM_LINKING_ENABLED
        and re.fullmatch(r'[A-Za-z0-9_]{5,32}', settings.TELEGRAM_BOT_USERNAME)
        and re.fullmatch(r'[A-Za-z0-9_-]{32,256}', settings.TELEGRAM_WEBHOOK_SECRET)
        and len(settings.TOKEN_ENCRYPTION_KEY) >= 32
        and settings.TOKEN_ENCRYPTION_KEY != Settings.model_fields['TOKEN_ENCRYPTION_KEY'].default)


def require_linking():
    if not linking_available():
        raise ConflictError('Telegram linking is not enabled for this release.')


def identity_hash(kind, value):
    return hmac.new(settings.TOKEN_ENCRYPTION_KEY.encode(),
        f'telegram:{kind}:{value}'.encode(), hashlib.sha256).hexdigest()


def nonce_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


async def owner_lock(db, owner):
    if db.bind.dialect.name == 'postgresql':
        # Serialize creation of the first preference/connection as well as edits.
        await db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:owner, 37))'), {'owner': owner})
    await require_active(db, owner)


async def connection_for(db, owner):
    return await db.scalar(select(MessagingConnection).where(MessagingConnection.user_id == owner,
        MessagingConnection.provider == 'telegram').with_for_update().execution_options(populate_existing=True))


def audit(db, owner, event, connection=None, **details):
    db.add(AuditLog(user_id=owner, event_type=event, target_entity='assistant',
        target_id=connection.id if connection else None,
        details={'provider': 'telegram', **details}))


def connection_view(row):
    if row is None:
        return {'status': 'not_connected', 'linked_at': None, 'expires_at': None}
    status = row.status
    if status == 'pending' and (not row.nonce_expires_at or aware(row.nonce_expires_at) <= datetime.now(timezone.utc)):
        status = 'expired'
    return {'status': status, 'linked_at': row.linked_at.isoformat() if row.linked_at else None,
        'expires_at': row.nonce_expires_at.isoformat() if status == 'pending' else None}


def preferences_view(row):
    if row is None:
        return {'version': 0, 'timezone': None, 'quiet_start_minute': 1320, 'quiet_end_minute': 480,
            'quiet_enabled': True, 'telegram_enabled': False, 'include_details': False, 'daily_cap': 3}
    return {key: getattr(row, key) for key in ('version', 'timezone', 'quiet_start_minute',
        'quiet_end_minute', 'quiet_enabled', 'telegram_enabled', 'include_details', 'daily_cap')}


async def start_link(db, owner):
    require_linking()
    await owner_lock(db, owner)
    row = await connection_for(db, owner)
    if row and row.status == 'active':
        raise ConflictError('Disconnect the current Telegram account before linking another.')
    if row is None:
        row = MessagingConnection(user_id=owner)
        db.add(row)
        await db.flush()
    nonce = secrets.token_urlsafe(32)
    row.status, row.nonce_hash = 'pending', nonce_hash(nonce)
    row.nonce_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    row.revision += 1
    row.revoked_at = None
    row.updated_at = datetime.now(timezone.utc)
    audit(db, owner, 'telegram_link_requested', row, revision=row.revision)
    await db.flush()
    return {'url': f'https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={nonce}',
        'expires_at': row.nonce_expires_at.isoformat(), 'expires_seconds': 600}


async def save_preferences(db, owner, payload: AssistantPreferencesUpdate):
    await owner_lock(db, owner)
    row = await db.get(AssistantPreferences, owner, populate_existing=True)
    if (row.version if row else 0) != payload.expected_version:
        raise ConflictError('Assistant preferences changed. Reload before saving.')
    if payload.telegram_enabled:
        require_linking()
        connection = await connection_for(db, owner)
        if not connection or connection.status != 'active':
            raise ConflictError('Link your Telegram account before enabling notifications.')
    if row is None:
        row = AssistantPreferences(user_id=owner)
        db.add(row)
    now = datetime.now(timezone.utc)
    for key, value in payload.model_dump(exclude={'expected_version', 'consent'}).items():
        setattr(row, key, value)
    row.version = payload.expected_version + 1
    row.updated_at = now
    if payload.telegram_enabled:
        row.consent_at, row.revoked_at = now, None
    else:
        row.revoked_at = now
    audit(db, owner, 'assistant_preferences_updated', version=row.version,
        telegram_enabled=row.telegram_enabled, include_details=row.include_details)
    from app.services.notification_outbox import cancel_pending
    await cancel_pending(db, owner)
    await db.flush()
    return preferences_view(row)


async def revoke(db, owner):
    # Always permitted, including when the integration feature flag is off.
    await owner_lock(db, owner)
    row = await connection_for(db, owner)
    now = datetime.now(timezone.utc)
    if row and row.status != 'revoked':
        row.status, row.revoked_at, row.updated_at = 'revoked', now, now
        row.revision += 1
        row.external_chat_hash = row.external_user_hash = None
        row.encrypted_chat_id = row.encrypted_user_id = None
        row.nonce_hash = row.nonce_expires_at = None
        audit(db, owner, 'telegram_disconnected', row, revision=row.revision)
    preferences = await db.get(AssistantPreferences, owner, populate_existing=True)
    if preferences and preferences.telegram_enabled:
        preferences.telegram_enabled, preferences.revoked_at, preferences.updated_at = False, now, now
        preferences.version += 1
    from app.services.notification_outbox import cancel_pending
    await cancel_pending(db, owner)
    await db.flush()
    return connection_view(row)


async def process_update(update: TelegramUpdate):
    message = update.message
    if not message or message.sender.is_bot or message.chat.type != 'private' or message.chat.id != message.sender.id:
        return
    command = message.text.strip()
    start = re.fullmatch(r'/start ([A-Za-z0-9_-]{43})', command)
    stopping = command == '/stop'
    if not start and not stopping:
        return
    if start and not linking_available():
        return
    chat_hash = identity_hash('chat', message.chat.id)
    user_hash = identity_hash('user', message.sender.id)
    # Narrow credential lookup only. Domain work re-enters the canonical owner RLS session.
    async with admin_db_session(reason='telegram_binding_lookup') as lookup:
        query = select(MessagingConnection.user_id).where(MessagingConnection.provider == 'telegram')
        if start:
            query = query.where(MessagingConnection.nonce_hash == nonce_hash(start.group(1)))
        else:
            query = query.where(MessagingConnection.status == 'active',
                MessagingConnection.external_chat_hash == chat_hash, MessagingConnection.external_user_hash == user_hash)
        owner = await lookup.scalar(query)
    if not owner:
        return
    try:
        async with rls_db_session(str(owner)) as db:
            await owner_lock(db, str(owner))
            row = await connection_for(db, str(owner))
            if not row:
                return
            if await db.get(MessagingUpdateReceipt, ('telegram', update.update_id)):
                return
            if stopping:
                if row.status != 'active' or row.external_chat_hash != chat_hash or row.external_user_hash != user_hash:
                    return
                if message.date < int(aware(row.linked_at).timestamp()):
                    return
                await revoke(db, str(owner))
            elif start:
                now = datetime.now(timezone.utc)
                if (row.status != 'pending' or row.nonce_hash != nonce_hash(start.group(1))
                        or not row.nonce_expires_at or aware(row.nonce_expires_at) <= now):
                    return
                row.external_chat_hash, row.external_user_hash = chat_hash, user_hash
                row.encrypted_chat_id, row.encrypted_user_id = encrypt_token(str(message.chat.id)), encrypt_token(str(message.sender.id))
                row.status, row.linked_at, row.updated_at = 'active', now, now
                row.nonce_hash = row.nonce_expires_at = None
                row.revision += 1
                audit(db, str(owner), 'telegram_linked', row, revision=row.revision)
            db.add(MessagingUpdateReceipt(user_id=str(owner), connection_id=row.id,
                provider='telegram', update_id=update.update_id))
            await db.commit()
    except IntegrityError:
        # Global unique chat/sender constraints also hold for concurrent owners.
        # Do not disclose whether the chat is connected to a different account.
        return
    except (AuthenticationError, ConflictError, NotFoundError):
        # Deletion/revocation wins; a late update must not resurrect a connection.
        return
