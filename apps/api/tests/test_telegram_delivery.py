import io
import json
import zipfile
from datetime import timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import decrypt_token, encrypt_token
from app.integrations.telegram_client import TelegramClient, TelegramResult
from app.models.assistant import (
    CommitmentAction,
    MessagingCallbackToken,
    NotificationDeliveryAttempt,
    NotificationOutbox,
)
from app.models.entities import Commitment
from app.schemas.assistant import TelegramUpdate
from app.services import notification_outbox as outbox
from app.services import telegram_delivery as delivery
from app.services.assistant_connections import nonce_hash, revoke
from app.services.telegram_callbacks import process_callback
from tests.conftest import TestingSessionLocal
from tests.test_notification_outbox import NOW, seed
from tests.test_telegram_transport import SYNTHETIC_TOKEN


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, 'TELEGRAM_LINKING_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_BOT_USERNAME', 'SyntheticBrainBot')
    monkeypatch.setattr(settings, 'TELEGRAM_WEBHOOK_SECRET', 'synthetic_webhook_secret_for_unit_tests')
    monkeypatch.setattr(settings, 'ASSISTANT_OUTBOX_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_DELIVERY_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_BOT_TOKEN', SecretStr(SYNTHETIC_TOKEN))
    monkeypatch.setattr(settings, 'FRONTEND_URL', 'https://brain.example.test')


def callback(raw, chat, *, update_id=101, message_id=19):
    return TelegramUpdate.model_validate({'update_id': update_id, 'callback_query': {
        'id': 'synthetic-callback', 'from': {'id': chat, 'is_bot': False}, 'data': raw,
        'message': {'date': int(NOW.timestamp()), 'message_id': message_id,
            'from': {'id': 12345, 'is_bot': True}, 'chat': {'id': chat, 'type': 'private'}}}})


async def sent(owner, result=None):
    async with TestingSessionLocal() as db:
        row, source, _, connection = await seed(db, owner)
        identity, source_id, chat = row.id, source.id, int(decrypt_token(connection.encrypted_chat_id))
    client = AsyncMock()
    client.send.return_value = result or TelegramResult('delivered', 'PROVIDER_ACCEPTED', '19')
    await delivery.deliver_one(owner, identity, client=client, clock=NOW)
    buttons = {button['text']: button.get('callback_data') for line in client.send.call_args.args[2] for button in line}
    return identity, source_id, chat, buttons, client


async def test_sender_commits_intent_before_http_and_stores_no_raw_tokens(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        row, _, _, _ = await seed(db, test_user_id)
        identity = row.id
    async def respond(request):
        async with TestingSessionLocal() as db:
            stored = await db.get(NotificationOutbox, identity)
            assert stored.status == 'dispatching' and stored.attempt_count == 1
            assert await db.scalar(select(func.count()).select_from(NotificationDeliveryAttempt)) == 1
        payload = json.loads(request.content)
        assert 'Synthetic check-in' not in payload['text']
        assert payload['protect_content'] is True
        for line in payload['reply_markup']['inline_keyboard']:
            for button in line:
                if 'callback_data' in button:
                    raw = button['callback_data']
                    assert len(raw) == 32
                    async with TestingSessionLocal() as db:
                        assert await db.scalar(select(MessagingCallbackToken).where(MessagingCallbackToken.token_hash == nonce_hash(raw)))
        return httpx.Response(200, json={'ok': True, 'result': {'message_id': 19,
            'chat': {'id': payload['chat_id'], 'type': 'private'}, 'from': {'id': 12345, 'is_bot': True}}})
    await delivery.deliver_one(test_user_id, identity, client=TelegramClient(transport=httpx.MockTransport(respond)), clock=NOW)
    async with TestingSessionLocal() as db:
        assert (await db.get(NotificationOutbox, identity)).status == 'delivered'


async def test_uncertain_send_never_retries_and_callback_can_supply_receipt(test_user_id, enabled):
    identity, source, chat, buttons, client = await sent(test_user_id, TelegramResult('uncertain', 'DELIVERY_UNKNOWN'))
    await delivery.deliver_one(test_user_id, identity, client=client, clock=NOW + timedelta(minutes=1))
    assert client.send.await_count == 1
    await process_callback(callback(buttons['Done'], chat), client=client, clock=NOW)
    async with TestingSessionLocal() as db:
        row = await db.get(NotificationOutbox, identity)
        assert row.status == 'delivered' and row.provider_message_id == '19'
        assert (await db.get(Commitment, source)).status == 'completed'
        assert (await db.scalar(select(NotificationDeliveryAttempt))).status == 'delivered'


@pytest.mark.parametrize('label,expected', [('Done', 'completed'), ('Working', 'in_progress'), ('Snooze 1h', 'snoozed'), ('Help', 'snoozed')])
async def test_buttons_use_canonical_actions_and_replay_once(test_user_id, enabled, label, expected):
    identity, source, chat, buttons, client = await sent(test_user_id)
    for update_id in (101, 101, 102):
        await process_callback(callback(buttons[label], chat, update_id=update_id), client=client, clock=NOW)
    async with TestingSessionLocal() as db:
        commitment = await db.get(Commitment, source)
        assert commitment.status == expected
        assert await db.scalar(select(func.count()).select_from(CommitmentAction)) == 1
        if label == 'Snooze 1h':
            reminders = (await db.scalars(select(NotificationOutbox).where(NotificationOutbox.status == 'queued'))).all()
            assert len(reminders) == 1
            assert outbox.aware(reminders[0].scheduled_at) == NOW + timedelta(hours=1)
            assert commitment.source_timezone == 'Asia/Dhaka'
        if label == 'Help':
            action = await db.scalar(select(CommitmentAction))
            assert action.receipt['help']['sources'][0]['id'] == str(source)
            assert all('Synthetic check-in' not in call.args[2] for call in client.edit.call_args_list)
    assert client.send.await_count == 1


@pytest.mark.parametrize('change', ['sender', 'group', 'bot', 'message', 'expiry', 'revision', 'revoked', 'deleted', 'preferences'])
async def test_foreign_stale_deleted_or_revoked_buttons_never_act(test_user_id, enabled, change):
    identity, source, chat, buttons, client = await sent(test_user_id)
    update = callback(buttons['Done'], chat)
    async with TestingSessionLocal() as db:
        if change == 'sender':
            update.callback_query.sender.id += 1
        elif change == 'group':
            update.callback_query.message.chat.type = 'group'
        elif change == 'bot':
            update.callback_query.message.sender.id += 1
        elif change == 'message':
            update.callback_query.message.message_id += 1
        elif change == 'expiry':
            token = await db.scalar(select(MessagingCallbackToken).where(MessagingCallbackToken.token_hash == nonce_hash(buttons['Done'])))
            token.expires_at = NOW
        elif change == 'revoked':
            await revoke(db, test_user_id)
        elif change == 'preferences':
            from app.models.assistant import AssistantPreferences
            (await db.get(AssistantPreferences, test_user_id)).version += 1
        else:
            row = await db.get(Commitment, source)
            if change == 'revision':
                row.description = 'A newer promise'
            else:
                row.deleted_at = NOW
        await db.commit()
    await process_callback(update, client=client, clock=NOW)
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(CommitmentAction)) == 0


async def test_stop_works_with_send_flags_off_and_deleted_source(test_user_id, enabled, monkeypatch):
    _, source, chat, buttons, client = await sent(test_user_id)
    async with TestingSessionLocal() as db:
        (await db.get(Commitment, source)).deleted_at = NOW
        await db.commit()
    monkeypatch.setattr(settings, 'TELEGRAM_DELIVERY_ENABLED', False)
    await process_callback(callback(buttons['Stop reminders'], chat), client=client, clock=NOW)
    from app.models.assistant import AssistantPreferences, MessagingConnection
    async with TestingSessionLocal() as db:
        assert (await db.scalar(select(MessagingConnection))).status == 'revoked'
        assert not (await db.get(AssistantPreferences, test_user_id)).telegram_enabled


async def test_ack_failure_does_not_undo_done(test_user_id, enabled):
    _, source, chat, buttons, client = await sent(test_user_id)
    client.acknowledge.return_value = TelegramResult('uncertain', 'DELIVERY_UNKNOWN')
    client.edit.return_value = TelegramResult('failed', 'PROVIDER_REJECTED')
    await process_callback(callback(buttons['Done'], chat), client=client, clock=NOW)
    async with TestingSessionLocal() as db:
        assert (await db.get(Commitment, source)).status == 'completed'


async def test_confirmed_429_retries_three_times_then_stops(test_user_id, enabled):
    identity, _, _, _, client = await sent(test_user_id, TelegramResult('failed', 'RATE_LIMITED', retry_after=30))
    await delivery.deliver_one(test_user_id, identity, client=client, clock=NOW + timedelta(seconds=29))
    assert client.send.await_count == 1
    for elapsed in (30, 60, 90):
        await delivery.deliver_one(test_user_id, identity, client=client, clock=NOW + timedelta(seconds=elapsed))
    assert client.send.await_count == 3
    async with TestingSessionLocal() as db:
        row = await db.get(NotificationOutbox, identity)
        assert row.status == 'failed' and row.attempt_count == 3
        assert await db.scalar(select(func.count()).select_from(NotificationDeliveryAttempt)) == 3
        assert await db.scalar(select(func.count()).select_from(MessagingCallbackToken)) == 5


async def test_revoke_between_intent_and_transport_prevents_send(test_user_id, enabled, monkeypatch):
    original = outbox.begin_dispatch
    async def stop_after_intent(db, owner, identity, token, **kwargs):
        result = await original(db, owner, identity, token, **kwargs)
        await revoke(db, owner)
        return result
    monkeypatch.setattr(outbox, 'begin_dispatch', stop_after_intent)
    async with TestingSessionLocal() as db:
        row, _, _, _ = await seed(db, test_user_id)
    client = AsyncMock()
    await delivery.deliver_one(test_user_id, row.id, client=client, clock=NOW)
    client.send.assert_not_called()
    async with TestingSessionLocal() as db:
        assert (await db.get(NotificationOutbox, row.id)).status == 'cancelled'


async def test_activity_owner_filter_no_private_fields(async_client, auth_headers, test_user_id, other_user_id, enabled):
    identity, _, _, _, _ = await sent(test_user_id)
    async with TestingSessionLocal() as db:
        await seed(db, other_user_id)
    response = await async_client.get('/api/v1/assistant/activity?limit=1', headers=auth_headers)
    assert response.status_code == 200 and response.headers['cache-control'] == 'private, no-store'
    body = response.json()
    assert len(body['items']) == 1 and body['items'][0]['id'] == str(identity)
    assert set(body['items'][0]) == {'id', 'commitment_id', 'status', 'scheduled_at', 'delivered_at', 'attempt_count'}
    assert body['next_offset'] is None


@pytest.mark.parametrize('change', ['chat', 'user', 'hash', 'ciphertext'])
async def test_corrupted_destination_never_sends(test_user_id, enabled, change):
    async with TestingSessionLocal() as db:
        row, _, _, connection = await seed(db, test_user_id)
        if change == 'chat':
            connection.encrypted_chat_id = encrypt_token('1')
        elif change == 'user':
            connection.encrypted_user_id = encrypt_token('2')
        elif change == 'hash':
            connection.external_chat_hash = '0' * 64
        else:
            connection.encrypted_chat_id = 'invalid-ciphertext'
        await db.commit()
    client = AsyncMock()
    await delivery.deliver_one(test_user_id, row.id, client=client, clock=NOW)
    client.send.assert_not_called()
    async with TestingSessionLocal() as db:
        assert (await db.get(NotificationOutbox, row.id)).error_code == 'INVALID_DESTINATION'


async def test_details_only_leave_after_explicit_permission(test_user_id, enabled):
    async with TestingSessionLocal() as db:
        row, _, preferences, _ = await seed(db, test_user_id)
        preferences.include_details = True
        await db.commit()
    client = AsyncMock()
    client.send.return_value = TelegramResult('delivered', 'PROVIDER_ACCEPTED', '19')
    await delivery.deliver_one(test_user_id, row.id, client=client, clock=NOW)
    assert 'Synthetic check-in' in client.send.call_args.args[1]


async def test_callback_vault_excluded_from_export_and_erased_with_owner(test_user_id, other_user_id, enabled, monkeypatch):
    from app.integrations.storage_client import StorageService
    from app.services.account import close_account, portable_export, request_closure
    monkeypatch.setattr(StorageService, 'delete_owner_files', AsyncMock(return_value=0))
    monkeypatch.setattr('app.services.account.delete_auth_user', AsyncMock())
    _, _, _, buttons, client = await sent(test_user_id)
    await sent(other_user_id)
    async with TestingSessionLocal() as db:
        with zipfile.ZipFile(io.BytesIO(await portable_export(db, test_user_id))) as archive:
            data = archive.read('data.json').decode()
            tables = json.loads(data)['tables']
            assert 'messaging_callback_tokens' not in tables
            assert buttons['Done'] not in data and nonce_hash(buttons['Done']) not in data
            assert len(tables['notification_delivery_attempts']) == 1
    await request_closure(test_user_id)
    await close_account(test_user_id)
    async with TestingSessionLocal() as db:
        for model in (MessagingCallbackToken, NotificationDeliveryAttempt, NotificationOutbox):
            rows = (await db.scalars(select(model))).all()
            assert rows and all(str(row.user_id) == other_user_id for row in rows)
    assert client.send.await_count == 1
