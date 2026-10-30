"""Migration 33: several Google accounts per capability, still one row per account."""
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]

INSERT = text("INSERT INTO public.integrations(user_id,provider,external_account_identifier) "
              "VALUES(CAST(:owner AS uuid), CAST(:provider AS integration_provider), :account)")


@pytest.fixture
async def owner(pg_engine):
    identity = str(uuid4())
    async with pg_engine.begin() as conn:
        await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                           {'id': identity, 'email': identity + '@google-accounts.test'})
    try:
        yield identity
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': identity})


async def add(pg_engine, owner, provider, account):
    async with pg_engine.begin() as conn:
        await conn.execute(INSERT, {'owner': owner, 'provider': provider, 'account': account})


async def test_one_user_can_connect_several_accounts_for_one_capability(pg_engine, owner):
    await add(pg_engine, owner, 'google_drive', 'a@example.test')
    await add(pg_engine, owner, 'google_drive', 'b@example.test')
    await add(pg_engine, owner, 'google_calendar', 'a@example.test')
    async with pg_engine.begin() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM public.integrations WHERE user_id=CAST(:o AS uuid)"), {'o': owner}) == 3


@pytest.mark.parametrize('duplicate', ['a@example.test', 'A@Example.TEST'])
async def test_the_same_account_cannot_be_connected_twice_for_a_capability(pg_engine, owner, duplicate):
    await add(pg_engine, owner, 'google_drive', 'a@example.test')
    with pytest.raises(IntegrityError):
        await add(pg_engine, owner, 'google_drive', duplicate)


async def test_rows_from_before_accounts_were_recorded_stay_unique_and_coexist(pg_engine, owner):
    await add(pg_engine, owner, 'google_calendar', None)
    await add(pg_engine, owner, 'google_calendar', 'a@example.test')
    with pytest.raises(IntegrityError):
        await add(pg_engine, owner, 'google_calendar', None)


async def test_two_users_may_connect_the_same_google_account(pg_engine, owner):
    other = str(uuid4())
    async with pg_engine.begin() as conn:
        await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                           {'id': other, 'email': other + '@google-accounts.test'})
    try:
        await add(pg_engine, owner, 'google_drive', 'shared@example.test')
        await add(pg_engine, other, 'google_drive', 'shared@example.test')
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': other})
