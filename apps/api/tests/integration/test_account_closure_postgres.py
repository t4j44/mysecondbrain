"""Requires migrated isolated PostgreSQL; SQLite cannot validate these policies."""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]


@pytest.mark.asyncio
async def test_closure_restricts_direct_authenticated_database_access(pg_engine):
    owner = str(uuid.uuid4())
    async with pg_engine.begin() as conn:
        await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                           {'id': owner, 'email': owner + '@closure.test'})
    try:
        async with pg_engine.begin() as conn:
            assert await conn.scalar(text('SELECT public.account_active(CAST(:id AS uuid))'), {'id': owner})
            await conn.execute(text('INSERT INTO public.account_closures(user_id) VALUES(CAST(:id AS uuid))'), {'id': owner})
        async with pg_engine.begin() as conn:
            await conn.execute(text("SELECT set_config('request.jwt.claim.sub', :owner, true)"), {'owner': owner})
            await conn.execute(text('SET LOCAL ROLE authenticated'))
            assert not await conn.scalar(text('SELECT public.account_active(CAST(:id AS uuid))'), {'id': owner})
            assert await conn.scalar(text('SELECT count(*) FROM public.profiles')) == 0
            with pytest.raises(DBAPIError) as denied:
                await conn.execute(text('INSERT INTO public.memories(user_id,title,body) VALUES(CAST(:id AS uuid),:title,:body)'),
                                   {'id': owner, 'title': 'blocked', 'body': 'synthetic'})
            assert denied.value.orig.sqlstate == '42501'
        async with pg_engine.connect() as conn:
            tables = (await conn.execute(text("SELECT tablename FROM pg_policies WHERE policyname='account_active_guard'"))).scalars().all()
            assert {'profiles', 'memories', 'documents', 'people', 'tasks'}.issubset(tables)
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM public.account_closures WHERE user_id=CAST(:id AS uuid)'), {'id': owner})
            await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})
