import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import settings
from app.dependencies.database import rls_db_session
from app.models.assistant import AssistantPreferences, NotificationOutbox
from app.models.entities import Commitment
from app.services import notification_outbox as outbox
from app.services.assistant_connections import process_update
from tests.integration.conftest import requires_postgres
from tests.integration.test_assistant_connections_postgres import (
    assistant_owners as assistant_owners,
)
from tests.integration.test_assistant_connections_postgres import link_nonce, start_update
from tests.integration.test_meeting_intelligence_postgres import identity as set_identity

pytestmark = [pytest.mark.postgres, requires_postgres]
NOW = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, 'ASSISTANT_OUTBOX_ENABLED', True)


async def prepare(owner):
    update = start_update(await link_nonce(owner), update_id=uuid4().int % (2**63))
    update.message.sender.id = update.message.chat.id = 1 + uuid4().int % (2**51)
    await process_update(update)
    async with rls_db_session(owner) as db:
        db.add(AssistantPreferences(user_id=owner, timezone='UTC', quiet_enabled=False,
            telegram_enabled=True, consent_at=NOW, daily_cap=1))
        commitments = [Commitment(user_id=owner, description='Synthetic', status='snoozed', reminder_at=NOW, source_timezone='UTC') for _ in range(2)]
        db.add_all(commitments)
        await db.flush()
        sources = [str(row.id) for row in commitments]
        await db.commit()
        return sources


async def enqueue(owner, source):
    async with rls_db_session(owner) as db:
        row = await outbox.enqueue_check_in(db, owner, await db.get(Commitment, source))
        await db.commit()
        return str(row.id)


async def reserve(owner, identity):
    async with rls_db_session(owner) as db:
        token = await outbox.claim(db, owner, identity, clock=NOW)
        await db.commit()
        return token


async def test_concurrent_schedule_dedup_and_quota_reservation(pg_engine, assistant_owners, enabled):
    owner = assistant_owners[0]
    sources = await prepare(owner)
    duplicates = await asyncio.gather(*(enqueue(owner, sources[0]) for _ in range(2)))
    assert duplicates[0] == duplicates[1]
    second = await enqueue(owner, sources[1])
    tokens = await asyncio.gather(reserve(owner, duplicates[0]), reserve(owner, second))
    assert sum(token is not None for token in tokens) == 1
    async with rls_db_session(owner) as db:
        assert await db.scalar(text('SELECT count(*) FROM public.notification_outbox')) == 2


async def test_database_edit_invalidates_lease(pg_engine, assistant_owners, enabled):
    owner = assistant_owners[0]
    source = (await prepare(owner))[0]
    identity = await enqueue(owner, source)
    token = await reserve(owner, identity)
    async with rls_db_session(owner) as db:
        await db.execute(text("UPDATE public.commitments SET description='Corrected' WHERE id=CAST(:id AS uuid)"), {'id': source})
        await db.commit()
        assert not await outbox.begin_dispatch(db, owner, identity, token, clock=NOW)
        await db.commit()
        assert (await db.get(NotificationOutbox, identity)).status == 'cancelled'


async def test_persisted_dispatch_crash_cannot_be_replayed(pg_engine, assistant_owners, enabled):
    owner = assistant_owners[0]
    identity = await enqueue(owner, (await prepare(owner))[0])
    token = await reserve(owner, identity)
    async with rls_db_session(owner) as db:
        assert await outbox.begin_dispatch(db, owner, identity, token, clock=NOW)
        await db.commit()
    async with rls_db_session(owner) as db:
        assert await outbox.recover_expired(db, owner, clock=NOW + timedelta(minutes=6)) == 1
        await db.commit()
    assert await reserve(owner, identity) is None
    async with rls_db_session(owner) as db:
        assert (await db.get(NotificationOutbox, identity)).status == 'uncertain'


async def test_owner_rls_cross_owner_references_and_browser_forgery(pg_engine, assistant_owners, enabled):
    owner, other = assistant_owners
    identity = await enqueue(owner, (await prepare(owner))[0])
    foreign_source = (await prepare(other))[0]
    async with rls_db_session(other) as db:
        assert await db.get(NotificationOutbox, identity) is None
    async with rls_db_session(owner) as db:
        with pytest.raises(DBAPIError):
            async with db.begin_nested():
                await db.execute(text('UPDATE public.notification_outbox SET commitment_id=CAST(:source AS uuid) WHERE id=CAST(:id AS uuid)'),
                    {'source': foreign_source, 'id': identity})
    role = 'outbox_browser_' + uuid4().hex
    async with pg_engine.begin() as db:
        await db.execute(text(f'CREATE ROLE {role} NOLOGIN NOINHERIT'))
        await db.execute(text(f'GRANT authenticated TO {role}'))
        try:
            await db.execute(text(f'SET LOCAL SESSION AUTHORIZATION {role}'))
            await set_identity(db, owner)
            assert await db.scalar(text('SELECT count(*) FROM public.notification_outbox')) == 0
            assert (await db.execute(text("UPDATE public.notification_outbox SET status='queued'"))).rowcount == 0
            assert not await db.scalar(text("SELECT has_table_privilege('authenticated','public.notification_outbox','TRUNCATE')"))
        finally:
            await db.execute(text('RESET ROLE'))
            await db.execute(text('RESET SESSION AUTHORIZATION'))
            await db.execute(text(f'DROP ROLE {role}'))
