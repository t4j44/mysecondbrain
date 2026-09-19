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


@pytest.mark.asyncio
async def test_account_export_and_erasure_against_real_schema(pg_engine, monkeypatch):
    import io
    import json
    import zipfile
    from unittest.mock import AsyncMock

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.dependencies import database
    from app.integrations.storage_client import StorageService
    from app.models.entities import AccountClosure, Memory
    from app.services.account import close_account, portable_export, request_closure

    owners = [str(uuid.uuid4()), str(uuid.uuid4())]
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    monkeypatch.setattr(database, 'AsyncSessionLocal', factory)
    monkeypatch.setattr(StorageService, 'delete_owner_files', AsyncMock(return_value=0))
    monkeypatch.setattr('app.services.account.delete_auth_user', AsyncMock())
    async with pg_engine.begin() as conn:
        for owner in owners:
            await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                               {'id': owner, 'email': owner + '@erasure.test'})
    try:
        async with factory() as db:
            db.add_all([Memory(user_id=owners[0], title='Erase fixture', content='own evidence'),
                        Memory(user_id=owners[1], title='Keep fixture', content='foreign evidence')])
            await db.commit()
        async with database.rls_db_session(owners[0]) as db:
            archive = await portable_export(db, owners[0])
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                data = json.loads(bundle.read('data.json'))
                assert [row['title'] for row in data['tables']['memories']] == ['Erase fixture']
        await request_closure(owners[0])
        await close_account(owners[0])
        async with factory() as db:
            remaining = (await db.execute(select(Memory).where(Memory.user_id.in_(owners)))).scalars().all()
            assert [row.title for row in remaining] == ['Keep fixture']
            assert (await db.get(AccountClosure, owners[0])).status == 'completed'
    finally:
        async with pg_engine.begin() as conn:
            for owner in owners:
                await conn.execute(text('DELETE FROM public.account_closures WHERE user_id=CAST(:id AS uuid)'), {'id': owner})
                await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})
