import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.config import settings
from app.core.security import decrypt_token
from app.dependencies.database import rls_db_session
from app.integrations.telegram_client import TelegramResult
from app.models.assistant import (
    CommitmentAction,
    MessagingCallbackToken,
    MessagingConnection,
    NotificationDeliveryAttempt,
    NotificationOutbox,
)
from app.services import telegram_delivery as delivery
from app.services.assistant_connections import revoke
from app.services.telegram_callbacks import process_callback
from tests.integration.conftest import requires_postgres
from tests.integration.test_assistant_connections_postgres import (
    assistant_owners as assistant_owners,
)
from tests.integration.test_meeting_intelligence_postgres import identity as set_identity
from tests.integration.test_notification_outbox_postgres import NOW, enqueue, prepare
from tests.test_telegram_delivery import callback
from tests.test_telegram_transport import SYNTHETIC_TOKEN

pytestmark = [pytest.mark.postgres, requires_postgres]


@pytest.fixture
def delivery_enabled(monkeypatch):
    monkeypatch.setattr(settings, 'ASSISTANT_OUTBOX_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_DELIVERY_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_BOT_TOKEN', SecretStr(SYNTHETIC_TOKEN))
    monkeypatch.setattr(settings, 'FRONTEND_URL', 'https://brain.example.test')


async def test_two_workers_send_once_with_committed_intent(pg_engine, assistant_owners, delivery_enabled):
    owner = assistant_owners[0]
    identity = await enqueue(owner, (await prepare(owner))[0])
    client = AsyncMock()
    async def send(*args):
        async with rls_db_session(owner) as db:
            row = await db.get(NotificationOutbox, identity)
            assert row.status == 'dispatching' and row.attempt_count == 1
            assert await db.scalar(select(func.count()).select_from(NotificationDeliveryAttempt)) == 1
        return TelegramResult('delivered', 'PROVIDER_ACCEPTED', '19')
    client.send.side_effect = send
    await asyncio.gather(*(delivery.deliver_one(owner, identity, client=client, clock=NOW) for _ in range(2)))
    assert client.send.await_count == 1
    async with rls_db_session(owner) as db:
        assert (await db.get(NotificationOutbox, identity)).status == 'delivered'


async def test_stop_serializes_with_inflight_send_and_cancels_next(pg_engine, assistant_owners, delivery_enabled):
    owner = assistant_owners[0]
    sources = await prepare(owner)
    identities = [await enqueue(owner, source) for source in sources]
    sending, release, stopped = asyncio.Event(), asyncio.Event(), asyncio.Event()
    client = AsyncMock()
    async def send(*args):
        sending.set()
        await asyncio.wait_for(release.wait(), 10)
        return TelegramResult('delivered', 'PROVIDER_ACCEPTED', '19')
    client.send.side_effect = send
    async def stop():
        async with rls_db_session(owner) as db:
            await revoke(db, owner)
            await db.commit()
        stopped.set()
    sender = asyncio.create_task(delivery.deliver_one(owner, identities[0], client=client, clock=NOW))
    await asyncio.wait_for(sending.wait(), 10)
    revoker = asyncio.create_task(stop())
    try:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(stopped.wait(), 0.1)
    finally:
        release.set()
        await asyncio.gather(sender, revoker)
    await delivery.deliver_one(owner, identities[1], client=client, clock=NOW)
    assert client.send.await_count == 1
    async with rls_db_session(owner) as db:
        assert (await db.get(NotificationOutbox, identities[1])).status == 'cancelled'


async def test_concurrent_callbacks_apply_one_action_and_reconcile_unknown(pg_engine, assistant_owners, delivery_enabled):
    owner = assistant_owners[0]
    identity = await enqueue(owner, (await prepare(owner))[0])
    client = AsyncMock()
    client.send.return_value = TelegramResult('uncertain', 'DELIVERY_UNKNOWN')
    await delivery.deliver_one(owner, identity, client=client, clock=NOW)
    buttons = {b['text']: b.get('callback_data') for line in client.send.call_args.args[2] for b in line}
    async with rls_db_session(owner) as db:
        chat = int(decrypt_token((await db.scalar(select(MessagingConnection))).encrypted_chat_id))
    updates = [callback(buttons['Done'], chat, update_id=uuid4().int % (2**63)) for _ in range(2)]
    await asyncio.gather(*(process_callback(update, client=client, clock=NOW) for update in updates))
    async with rls_db_session(owner) as db:
        assert await db.scalar(select(func.count()).select_from(CommitmentAction)) == 1
        row = await db.get(NotificationOutbox, identity)
        assert row.status == 'delivered' and row.provider_message_id == '19'
        assert (await db.scalar(select(NotificationDeliveryAttempt))).status == 'delivered'


async def test_delivery_tables_owner_fk_and_browser_denial(pg_engine, assistant_owners, delivery_enabled):
    owner, other = assistant_owners
    identity = await enqueue(owner, (await prepare(owner))[0])
    foreign = await enqueue(other, (await prepare(other))[0])
    client = AsyncMock()
    client.send.return_value = TelegramResult('uncertain', 'DELIVERY_UNKNOWN')
    await delivery.deliver_one(owner, identity, client=client, clock=NOW)
    async with rls_db_session(other) as db:
        assert await db.scalar(select(func.count()).select_from(MessagingCallbackToken)) == 0
        assert await db.scalar(select(func.count()).select_from(NotificationDeliveryAttempt)) == 0
    async with rls_db_session(owner) as db:
        with pytest.raises(DBAPIError):
            async with db.begin_nested():
                await db.execute(text('UPDATE public.messaging_callback_tokens SET outbox_id=CAST(:foreign AS uuid)'), {'foreign': foreign})
    role = 'delivery_browser_' + uuid4().hex
    async with pg_engine.begin() as db:
        await db.execute(text(f'CREATE ROLE {role} NOLOGIN NOINHERIT'))
        await db.execute(text(f'GRANT authenticated TO {role}'))
        try:
            await db.execute(text(f'SET LOCAL SESSION AUTHORIZATION {role}'))
            await set_identity(db, owner)
            for table in ('messaging_callback_tokens', 'notification_delivery_attempts'):
                assert await db.scalar(text(f'SELECT count(*) FROM public.{table}')) == 0
                assert not await db.scalar(text("SELECT has_table_privilege('authenticated',:table,'TRUNCATE')"), {'table': 'public.' + table})
        finally:
            await db.execute(text('RESET ROLE'))
            await db.execute(text('RESET SESSION AUTHORIZATION'))
            await db.execute(text(f'DROP ROLE {role}'))


async def test_safe_rate_limit_retry_has_bounded_attempt_ledger(pg_engine, assistant_owners, delivery_enabled):
    owner = assistant_owners[0]
    identity = await enqueue(owner, (await prepare(owner))[0])
    client = AsyncMock()
    client.send.return_value = TelegramResult('failed', 'RATE_LIMITED', retry_after=30)
    for seconds in (0, 30, 60, 90):
        await delivery.deliver_one(owner, identity, client=client, clock=NOW + timedelta(seconds=seconds))
    assert client.send.await_count == 3
    async with rls_db_session(owner) as db:
        assert (await db.get(NotificationOutbox, identity)).status == 'failed'
        assert await db.scalar(select(func.count()).select_from(NotificationDeliveryAttempt)) == 3
