"""Synthetic Telegram callbacks; no bot credentials and no external messages."""
import io
import itertools
import json
import zipfile
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import decrypt_token
from app.integrations.storage_client import StorageService
from app.models.assistant import AssistantPreferences, MessagingConnection, MessagingUpdateReceipt
from app.models.entities import AuditLog
from app.services.account import close_account, portable_export, request_closure
from tests.conftest import TestingSessionLocal

CONNECTION = '/api/v1/assistant/connections/telegram'
PREFERENCES = '/api/v1/assistant/preferences'
WEBHOOK = '/api/v1/integrations/telegram/webhook'
SYNTHETIC_SECRET = 'synthetic_webhook_secret_for_local_tests_only'
UPDATE_IDS = itertools.count(1)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, 'TELEGRAM_LINKING_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_BOT_USERNAME', 'SyntheticBrainBot')
    monkeypatch.setattr(settings, 'TELEGRAM_WEBHOOK_SECRET', SYNTHETIC_SECRET)


async def start(client, headers):
    response = await client.post(CONNECTION + '/start', headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'private, no-store'
    url = urlsplit(response.json()['url'])
    assert url.scheme == 'https' and url.netloc == 't.me'
    return parse_qs(url.query)['start'][0]


async def update(client, command, *, sender=123456789, chat=None, kind='private', secret=SYNTHETIC_SECRET, update_id=None, date=None):
    return await client.post(WEBHOOK, headers={'X-Telegram-Bot-Api-Secret-Token': secret},
        json={'update_id': next(UPDATE_IDS) if update_id is None else update_id, 'message': {'date': int(datetime.now(timezone.utc).timestamp()) if date is None else date, 'from': {'id': sender, 'is_bot': False},
            'chat': {'id': sender if chat is None else chat, 'type': kind}, 'text': command}})


async def test_default_off_and_auth_required(async_client, auth_headers):
    assert not settings.TELEGRAM_LINKING_ENABLED
    assert (await async_client.post(CONNECTION + '/start', headers=auth_headers)).status_code == 409
    assert (await async_client.post(CONNECTION + '/start')).status_code == 401
    assert (await async_client.put(PREFERENCES, json={'expected_version': 0, 'timezone': 'UTC'})).status_code == 401
    assert (await update(async_client, '/start ' + 'a' * 43)).status_code == 401


async def test_one_use_link_is_encrypted_and_not_notification_consent(async_client, auth_headers, test_user_id, enabled):
    nonce = await start(async_client, auth_headers)
    assert (await update(async_client, '/start ' + nonce)).status_code == 200
    assert (await update(async_client, '/start ' + nonce, sender=222222)).status_code == 200
    view = (await async_client.get(CONNECTION, headers=auth_headers)).json()
    assert view['status'] == 'active' and 'encrypted_chat_id' not in view
    assert (await async_client.get(PREFERENCES, headers=auth_headers)).json()['telegram_enabled'] is False
    async with TestingSessionLocal() as db:
        row = await db.scalar(select(MessagingConnection).where(MessagingConnection.user_id == test_user_id))
        assert row.nonce_hash is None and row.nonce_expires_at is None
        assert decrypt_token(row.encrypted_chat_id) == '123456789'
        assert '123456789' not in row.encrypted_chat_id and row.external_chat_hash != '123456789'
        logs = (await db.scalars(select(AuditLog))).all()
        assert len([log for log in logs if log.event_type == 'telegram_linked']) == 1
        assert nonce not in str([log.details for log in logs])


@pytest.mark.parametrize('kind,chat,sender', [('group', -1, 123456789), ('private', 987654, 123456789)])
async def test_sender_and_private_chat_must_match(async_client, auth_headers, enabled, kind, chat, sender):
    nonce = await start(async_client, auth_headers)
    assert (await update(async_client, '/start ' + nonce, kind=kind, chat=chat, sender=sender)).status_code == 200
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'pending'


async def test_forged_webhook_and_expired_nonce_cannot_bind(async_client, auth_headers, test_user_id, enabled):
    nonce = await start(async_client, auth_headers)
    assert (await update(async_client, '/start ' + nonce, secret='wrong')).status_code == 401
    async with TestingSessionLocal() as db:
        row = await db.scalar(select(MessagingConnection).where(MessagingConnection.user_id == test_user_id))
        assert row.nonce_hash != nonce and len(row.nonce_hash) == 64
        row.nonce_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await update(async_client, '/start ' + nonce)).status_code == 200
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'expired'


async def test_a_chat_cannot_bind_two_owners_until_explicit_disconnect(async_client, auth_headers, other_auth_headers, enabled):
    first = await start(async_client, auth_headers)
    second = await start(async_client, other_auth_headers)
    await update(async_client, '/start ' + first)
    await update(async_client, '/start ' + second)
    assert (await async_client.get(CONNECTION, headers=other_auth_headers)).json()['status'] == 'pending'
    assert (await async_client.post(CONNECTION + '/start', headers=auth_headers)).status_code == 409
    assert (await async_client.delete(CONNECTION, headers=auth_headers)).status_code == 200
    await update(async_client, '/start ' + second)
    assert (await async_client.get(CONNECTION, headers=other_auth_headers)).json()['status'] == 'active'
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'revoked'


async def test_preferences_require_link_consent_timezone_version_and_bounded_cap(async_client, auth_headers, enabled):
    payload = {'expected_version': 0, 'timezone': 'Asia/Dhaka', 'telegram_enabled': True, 'consent': True}
    assert (await async_client.put(PREFERENCES, headers=auth_headers, json=payload)).status_code == 409
    nonce = await start(async_client, auth_headers)
    await update(async_client, '/start ' + nonce)
    for invalid in ({'consent': False}, {'timezone': 'Made/Up'}, {'daily_cap': 500}, {'quiet_start_minute': 480}):
        assert (await async_client.put(PREFERENCES, headers=auth_headers, json={**payload, **invalid})).status_code == 422
    result = await async_client.put(PREFERENCES, headers=auth_headers, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['version'] == 1 and result.json()['include_details'] is False
    assert (await async_client.put(PREFERENCES, headers=auth_headers, json=payload)).status_code == 409


async def test_stop_revokes_even_when_feature_disabled_and_stale_updates_cannot_reconnect(async_client, auth_headers, enabled, monkeypatch):
    nonce = await start(async_client, auth_headers)
    await update(async_client, '/start ' + nonce)
    await async_client.put(PREFERENCES, headers=auth_headers, json={
        'expected_version': 0, 'timezone': 'UTC', 'telegram_enabled': True, 'consent': True})
    monkeypatch.setattr(settings, 'TELEGRAM_LINKING_ENABLED', False)
    await update(async_client, '/stop', sender=999999)
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'active'
    await update(async_client, '/stop')
    await update(async_client, '/start ' + nonce)
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'revoked'
    assert (await async_client.get(PREFERENCES, headers=auth_headers)).json()['telegram_enabled'] is False
    assert (await async_client.delete(CONNECTION, headers=auth_headers)).status_code == 200


async def test_export_excludes_connection_secrets_and_owner_isolation_holds(async_client, auth_headers, other_auth_headers, test_user_id, enabled):
    await start(async_client, auth_headers)
    await async_client.put(PREFERENCES, headers=auth_headers, json={'expected_version': 0, 'timezone': 'Asia/Dhaka'})
    assert (await async_client.get(CONNECTION, headers=other_auth_headers)).json()['status'] == 'not_connected'
    assert (await async_client.get(PREFERENCES, headers=other_auth_headers)).json()['version'] == 0
    async with TestingSessionLocal() as db:
        raw = await portable_export(db, test_user_id)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            tables = json.loads(archive.read('data.json'))['tables']
        assert 'messaging_connections' not in tables
        assert 'messaging_update_receipts' not in tables
        assert tables['assistant_preferences'][0]['timezone'] == 'Asia/Dhaka'


async def test_pending_link_cannot_resurrect_closing_account(async_client, auth_headers, test_user_id, enabled):
    nonce = await start(async_client, auth_headers)
    await request_closure(test_user_id)
    assert (await update(async_client, '/start ' + nonce)).status_code == 200
    async with TestingSessionLocal() as db:
        row = await db.scalar(select(MessagingConnection).where(MessagingConnection.user_id == test_user_id))
        assert row.status == 'pending' and row.encrypted_chat_id is None
        assert await db.get(AssistantPreferences, test_user_id) is None


async def test_new_nonce_invalidates_previous_and_webhook_input_is_bounded(async_client, auth_headers, enabled):
    old = await start(async_client, auth_headers)
    current = await start(async_client, auth_headers)
    await update(async_client, '/start ' + old)
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'pending'
    result = await async_client.post(WEBHOOK, content=b'x' * 65537,
        headers={'X-Telegram-Bot-Api-Secret-Token': SYNTHETIC_SECRET})
    assert result.status_code == 400
    await update(async_client, '/start ' + current)
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'active'


async def test_default_encryption_key_cannot_enable_linking(async_client, auth_headers, enabled, monkeypatch):
    from app.core.config import Settings
    monkeypatch.setattr(settings, 'TOKEN_ENCRYPTION_KEY', Settings.model_fields['TOKEN_ENCRYPTION_KEY'].default)
    assert (await async_client.post(CONNECTION + '/start', headers=auth_headers)).status_code == 409


async def test_old_stop_cannot_disconnect_a_relinked_account(async_client, auth_headers, enabled):
    nonce = await start(async_client, auth_headers)
    await update(async_client, '/start ' + nonce)
    await update(async_client, '/stop', update_id=900001)
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'revoked'
    new_nonce = await start(async_client, auth_headers)
    await update(async_client, '/start ' + new_nonce)
    await update(async_client, '/stop', update_id=900001)
    # A delayed command that was never processed is also older than this binding.
    await update(async_client, '/stop', date=int(datetime.now(timezone.utc).timestamp()) - 60)
    assert (await async_client.get(CONNECTION, headers=auth_headers)).json()['status'] == 'active'


async def test_erasure_removes_connections_receipts_and_preferences_only_for_owner(
    async_client, auth_headers, other_auth_headers, test_user_id, other_user_id, enabled, monkeypatch,
):
    monkeypatch.setattr(StorageService, 'delete_owner_files', AsyncMock(return_value=0))
    auth_delete = AsyncMock()
    monkeypatch.setattr('app.services.account.delete_auth_user', auth_delete)
    for headers, sender in ((auth_headers, 111111), (other_auth_headers, 222222)):
        nonce = await start(async_client, headers)
        await update(async_client, '/start ' + nonce, sender=sender)
        await async_client.put(PREFERENCES, headers=headers, json={'expected_version': 0, 'timezone': 'UTC'})
    await request_closure(test_user_id)
    await close_account(test_user_id)
    auth_delete.assert_awaited_once_with(test_user_id)
    async with TestingSessionLocal() as db:
        for model in (AssistantPreferences, MessagingConnection, MessagingUpdateReceipt):
            rows = (await db.scalars(select(model))).all()
            assert len(rows) == 1 and str(rows[0].user_id) == other_user_id
