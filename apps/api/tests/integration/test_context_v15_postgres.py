"""V1.5 owner policies, cross-owner references, OAuth vault and event vectors."""
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.indexing import index_record, semantic_search
from app.ai.provider import GeminiLLMProvider
from app.db.rls import identity_statements
from app.models.entities import ContextEvent
from app.services.context_events import delete_event
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]


async def identity(db, owner):
    for sql, params in identity_statements(owner):
        await db.execute(text(sql), params)


@pytest.fixture
async def context_fixture(pg_engine):
    ids = {key: str(uuid4()) for key in ('owner', 'other', 'person', 'event', 'media', 'grant')}
    ids['client'] = 'synthetic-' + uuid4().hex
    async with pg_engine.begin() as conn:
        for owner in (ids['owner'], ids['other']):
            await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'), {'id': owner, 'email': owner + '@v15.test'})
        await conn.execute(text("INSERT INTO public.people(id,user_id,name) VALUES(CAST(:person AS uuid),CAST(:owner AS uuid),'Synthetic')"), ids)
        await conn.execute(text("INSERT INTO public.context_events(id,user_id,event_type,title,summary,occurred_at,source_type,person_id) VALUES(CAST(:event AS uuid),CAST(:owner AS uuid),'moment','Synthetic event','Synthetic cobalt',now(),'manual',CAST(:person AS uuid))"), ids)
        await conn.execute(text("INSERT INTO public.context_media(id,user_id,event_id,request_id,kind,storage_path,thumbnail_path,mime_type,size_bytes,width,height,thumbnail_bytes,content_hash) VALUES(CAST(:media AS uuid),CAST(:owner AS uuid),CAST(:event AS uuid),gen_random_uuid(),'moment',:owner || '/photo.webp',:owner || '/thumb.webp','image/webp',100,50,50,25,'synthetic')"), ids)
        await conn.execute(text("INSERT INTO public.mcp_oauth_clients(id,metadata) VALUES(:client,'{}')"), ids)
        await conn.execute(text("INSERT INTO public.mcp_oauth_grants(id,user_id,client_id,client_name,scopes,issuer,resource,expires_at) VALUES(CAST(:grant AS uuid),CAST(:owner AS uuid),:client,'Synthetic','[]','https://example.test','https://example.test/mcp',now()+interval '1 day')"), ids)
    try:
        yield ids
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM public.account_closures WHERE user_id=CAST(:owner AS uuid)'), ids)
            for owner in (ids['owner'], ids['other']):
                await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})
            await conn.execute(text('DELETE FROM public.mcp_oauth_clients WHERE id=:client'), ids)


async def test_v15_owner_rls_and_account_closure(pg_engine, context_fixture):
    ids = context_fixture
    for owner, expected in ((ids['owner'], 1), (ids['other'], 0)):
        async with pg_engine.begin() as conn:
            await identity(conn, owner)
            for table in ('context_events', 'context_media', 'mcp_oauth_grants'):
                assert await conn.scalar(text(f'SELECT count(*) FROM public.{table} WHERE user_id=CAST(:owner AS uuid)'), ids) == expected
            if owner == ids['other']:
                assert (await conn.execute(text("UPDATE public.context_events SET title='foreign change' WHERE id=CAST(:event AS uuid)"), ids)).rowcount == 0
                assert (await conn.execute(text('DELETE FROM public.context_media WHERE id=CAST(:media AS uuid)'), ids)).rowcount == 0
    async with pg_engine.begin() as conn:
        await conn.execute(text('INSERT INTO public.account_closures(user_id) VALUES(CAST(:owner AS uuid))'), ids)
    async with pg_engine.begin() as conn:
        await identity(conn, ids['owner'])
        for table in ('context_events', 'context_media', 'mcp_oauth_grants'):
            assert await conn.scalar(text(f'SELECT count(*) FROM public.{table} WHERE user_id=CAST(:owner AS uuid)'), ids) == 0


@pytest.mark.parametrize('sql', [
    "INSERT INTO public.context_events(user_id,event_type,title,occurred_at,source_type,person_id) VALUES(CAST(:other AS uuid),'moment','Bad reference',now(),'manual',CAST(:person AS uuid))",
    "INSERT INTO public.context_media(user_id,event_id,request_id,kind,storage_path,thumbnail_path,mime_type,size_bytes,width,height,thumbnail_bytes,content_hash) VALUES(CAST(:other AS uuid),CAST(:event AS uuid),gen_random_uuid(),'moment',:other || '/photo.webp',:other || '/thumb.webp','image/webp',10,10,10,5,'bad')",
    "INSERT INTO public.entity_edges(user_id,source_entity_type,source_entity_id,target_entity_type,target_entity_id,relationship_type,source_event_id) VALUES(CAST(:other AS uuid),'person',gen_random_uuid(),'project',gen_random_uuid(),'related_to',CAST(:event AS uuid))",
])
async def test_v15_cross_owner_foreign_keys(pg_engine, context_fixture, sql):
    async with pg_engine.begin() as conn:
        await identity(conn, context_fixture['other'])
        with pytest.raises(DBAPIError) as error:
            await conn.execute(text(sql), context_fixture)
        assert error.value.orig.sqlstate == '23503'


@pytest.mark.parametrize('table', ['mcp_oauth_clients', 'mcp_oauth_requests', 'mcp_oauth_codes', 'mcp_oauth_tokens'])
async def test_oauth_vault_is_unavailable_to_authenticated_role(pg_engine, context_fixture, table):
    async with pg_engine.begin() as conn:
        await identity(conn, context_fixture['owner'])
        with pytest.raises(DBAPIError) as error:
            await conn.execute(text(f'SELECT * FROM public.{table}'))
        assert error.value.orig.sqlstate == '42501'


async def test_events_real_pgvector_owner_restriction_and_delete(pg_engine, context_fixture, monkeypatch):
    ids = context_fixture
    async def embed(self, value, task_type='RETRIEVAL_DOCUMENT'):
        return [1.0] + [0.0] * 767
    monkeypatch.setattr(GeminiLLMProvider, 'embed_text', embed)
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: False)
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as db:
        await identity(db, ids['owner'])
        event = await db.get(ContextEvent, ids['event'])
        await index_record(db, ids['owner'], 'context_event', str(event.id))
        await db.commit()
        await identity(db, ids['owner'])
        results = await semantic_search(db, ids['owner'], 'cobalt', 5, ['context_event'])
        assert [item.id for item in results] == [ids['event']]
        event.privacy_class = 'restricted'
        await db.flush()
        assert not await semantic_search(db, ids['owner'], 'cobalt', 5, ['context_event'])
        event.privacy_class = 'private'
        await db.commit()
    async with factory() as db:
        await identity(db, ids['other'])
        assert not await semantic_search(db, ids['other'], 'cobalt', 5, ['context_event'])
    async with factory() as db:
        await identity(db, ids['owner'])
        await delete_event(db, ids['owner'], ids['event'])
        await db.commit()
        await identity(db, ids['owner'])
        assert not await semantic_search(db, ids['owner'], 'cobalt', 5, ['context_event'])
