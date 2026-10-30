"""Real PostgreSQL ownership, constraints and export for relationship additions."""
import io
import json
import uuid
import zipfile

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.rls import identity_statements
from app.models.entities import Commitment
from app.services.account import portable_export
from app.services.enrichment import EnrichmentService
from app.services.relationships import FollowupActionInput, RelationshipService
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]


async def identity(conn, owner):
    for statement, params in identity_statements(owner):
        await conn.execute(text(statement), params)


@pytest.mark.asyncio
async def test_new_relationship_tables_are_tenant_private_and_exportable(pg_engine):
    owner, other, person, project = (str(uuid.uuid4()) for _ in range(4))
    async with pg_engine.begin() as conn:
        for user in (owner, other):
            await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'), {'id': user, 'email': user + '@relationship.test'})
        await conn.execute(text('INSERT INTO public.people(id,user_id,name) VALUES(CAST(:id AS uuid),CAST(:owner AS uuid),:name)'), {'id': person, 'owner': owner, 'name': 'Synthetic contact'})
        await conn.execute(text("INSERT INTO public.projects(id,user_id,name,status) VALUES(CAST(:id AS uuid),CAST(:owner AS uuid),'Synthetic planned work','planned')"), {'id': project, 'owner': owner})
    try:
        async with pg_engine.begin() as conn:
            await identity(conn, owner)
            await conn.execute(text("INSERT INTO public.relationship_actions(user_id,person_id,request_id,suggestion_key,action,outcome) VALUES(CAST(:owner AS uuid),CAST(:person AS uuid),gen_random_uuid(),'synthetic','completed','Synthetic outcome')"), {'owner': owner, 'person': person})
            await conn.execute(text("INSERT INTO public.public_profile_claims(user_id,person_id,field,value,source_url,source_type,source_quote,researched_at,identity_basis,confidence_reason) VALUES(CAST(:owner AS uuid),CAST(:person AS uuid),'company','Example','https://example.com/','public_webpage','Synthetic example quote',now(),'Synthetic identity review','One synthetic source')"), {'owner': owner, 'person': person})
        for table in ('relationship_actions', 'public_profile_claims'):
            async with pg_engine.begin() as conn:
                await identity(conn, other)
                assert await conn.scalar(text(f'SELECT count(*) FROM public.{table}')) == 0
                result = await conn.execute(text(f'DELETE FROM public.{table}'))
                assert result.rowcount == 0
        # Even a valid self-owned row cannot point to the other tenant's contact.
        async with pg_engine.begin() as conn:
            await identity(conn, other)
            with pytest.raises(DBAPIError) as denied:
                await conn.execute(text("INSERT INTO public.relationship_actions(user_id,person_id,request_id,suggestion_key,action) VALUES(CAST(:owner AS uuid),CAST(:person AS uuid),gen_random_uuid(),'bad-link','dismissed')"), {'owner': other, 'person': person})
            assert denied.value.orig.sqlstate == '23503'
        factory = async_sessionmaker(pg_engine, expire_on_commit=False)
        async with factory() as db:
            await identity(db, owner)
            home = await RelationshipService(db, owner).home()
            assert any(item['id'] == project for item in home['projects'])
            profile = await RelationshipService(db, owner).profile(person)
            assert profile['person']['name'] == 'Synthetic contact'
            claims = await EnrichmentService(db, owner).list(person)
            assert len(claims) == 1 and claims[0]['current_value'] is None
            commitment = Commitment(user_id=owner, to_person_id=person, direction='owed_by_me', description='Send synthetic deck')
            db.add(commitment)
            await db.flush()
            suggestion = (await RelationshipService(db, owner).followups(person))[0]
            action = FollowupActionInput(confirmed=True, request_id=uuid.uuid4(), suggestion_key=suggestion['key'],
                action='completed', outcome='Sent the synthetic deck and recorded the response.')
            receipt = await RelationshipService(db, owner).act(person, action)
            assert {item['kind'] for item in receipt['records']} == {'interaction', 'memory'}
            await identity(db, owner)
            assert await RelationshipService(db, owner).act(person, action) == receipt
            assert (await RelationshipService(db, owner).home())['followups'] == []
            exported = await portable_export(db, owner)
            with zipfile.ZipFile(io.BytesIO(exported)) as archive:
                tables = json.loads(archive.read('data.json'))['tables']
                assert len(tables['relationship_actions']) == 2
                assert len(tables['public_profile_claims']) == 1
        async with pg_engine.begin() as conn:
            await conn.execute(text('INSERT INTO public.account_closures(user_id) VALUES(CAST(:owner AS uuid))'), {'owner': owner})
        async with pg_engine.begin() as conn:
            await identity(conn, owner)
            for table in ('relationship_actions', 'public_profile_claims'):
                assert await conn.scalar(text(f'SELECT count(*) FROM public.{table}')) == 0
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM public.account_closures WHERE user_id=CAST(:owner AS uuid)'), {'owner': owner})
            for user in (owner, other):
                await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:owner AS uuid)'), {'owner': user})
