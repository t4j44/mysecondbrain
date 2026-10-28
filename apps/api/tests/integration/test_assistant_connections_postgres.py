"""Real RLS, browser-role denial and concurrent Telegram identity uniqueness."""
import asyncio
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings
from app.dependencies import database
from app.schemas.assistant import TelegramUpdate
from app.services.assistant_connections import process_update, start_link
from tests.integration.conftest import requires_postgres
from tests.integration.test_meeting_intelligence_postgres import identity

pytestmark = [pytest.mark.postgres, requires_postgres]


@pytest.fixture
async def assistant_owners(pg_engine, monkeypatch):
    owners = [str(uuid4()), str(uuid4())]
    monkeypatch.setattr(settings, 'TELEGRAM_LINKING_ENABLED', True)
    monkeypatch.setattr(settings, 'TELEGRAM_BOT_USERNAME', 'SyntheticBrainBot')
    monkeypatch.setattr(settings, 'TELEGRAM_WEBHOOK_SECRET', 'synthetic_webhook_secret_for_postgres_tests')
    monkeypatch.setattr(settings, 'TOKEN_ENCRYPTION_KEY', 'synthetic_vault_key_for_isolated_postgres_tests')
    monkeypatch.setattr(database, 'AsyncSessionLocal', async_sessionmaker(pg_engine, expire_on_commit=False))
    async with pg_engine.begin() as db:
        for owner in owners:
            await db.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                {'id': owner, 'email': owner + '@assistant.test'})
    try:
        yield owners
    finally:
        async with pg_engine.begin() as db:
            for owner in owners:
                await db.execute(text('DELETE FROM public.account_closures WHERE user_id=CAST(:id AS uuid)'), {'id': owner})
                await db.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})


async def link_nonce(owner):
    async with database.rls_db_session(owner) as db:
        result = await start_link(db, owner)
        await db.commit()
        return parse_qs(urlsplit(result['url']).query)['start'][0]


def start_update(nonce, update_id=1):
    return TelegramUpdate.model_validate({'update_id': update_id, 'message': {'date': int(datetime.now(timezone.utc).timestamp()),
        'from': {'id': 123456789, 'is_bot': False}, 'chat': {'id': 123456789, 'type': 'private'},
        'text': '/start ' + nonce}})


async def test_owner_rls_and_browser_login_cannot_forge_or_read_bindings(pg_engine, assistant_owners):
    owner, other = assistant_owners
    await link_nonce(owner)
    async with pg_engine.begin() as db:
        await identity(db, other)
        assert await db.scalar(text('SELECT count(*) FROM public.messaging_connections')) == 0
    async with pg_engine.begin() as db:
        await identity(db, owner)
        assert await db.scalar(text('SELECT count(*) FROM public.messaging_connections')) == 1
        for table in ('assistant_preferences', 'messaging_connections', 'messaging_update_receipts'):
            assert not await db.scalar(text("SELECT has_table_privilege('authenticated', :table, 'TRUNCATE')"), {'table': 'public.' + table})
            assert not await db.scalar(text("SELECT has_table_privilege('anon', :table, 'SELECT')"), {'table': 'public.' + table})
    role = 'assistant_browser_' + uuid4().hex
    async with pg_engine.begin() as db:
        await db.execute(text(f'CREATE ROLE {role} NOLOGIN NOINHERIT'))
        await db.execute(text(f'GRANT authenticated TO {role}'))
        try:
            await db.execute(text(f'SET LOCAL SESSION AUTHORIZATION {role}'))
            await identity(db, owner)
            assert await db.scalar(text('SELECT count(*) FROM public.messaging_connections')) == 0
            assert (await db.execute(text("UPDATE public.messaging_connections SET nonce_hash='forged'"))).rowcount == 0
        finally:
            await db.execute(text('RESET ROLE'))
            await db.execute(text('RESET SESSION AUTHORIZATION'))
            await db.execute(text(f'DROP ROLE {role}'))


async def test_two_owners_racing_to_bind_same_chat_have_one_winner(pg_engine, assistant_owners):
    nonces = [await link_nonce(owner) for owner in assistant_owners]
    await asyncio.gather(*(process_update(start_update(nonce, index + 1)) for index, nonce in enumerate(nonces)))
    async with pg_engine.begin() as db:
        rows = (await db.execute(text("SELECT status FROM public.messaging_connections WHERE user_id IN (CAST(:a AS uuid),CAST(:b AS uuid))"),
            {'a': assistant_owners[0], 'b': assistant_owners[1]})).scalars().all()
        assert sorted(rows) == ['active', 'pending']


async def test_account_closure_blocks_delayed_link(pg_engine, assistant_owners):
    owner = assistant_owners[0]
    nonce = await link_nonce(owner)
    async with pg_engine.begin() as db:
        await db.execute(text("INSERT INTO public.account_closures(user_id,status) VALUES(CAST(:id AS uuid),'pending')"), {'id': owner})
    await process_update(start_update(nonce))
    async with pg_engine.begin() as db:
        assert await db.scalar(text('SELECT status FROM public.messaging_connections WHERE user_id=CAST(:id AS uuid)'), {'id': owner}) == 'pending'
