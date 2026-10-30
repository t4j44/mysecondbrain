import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.errors import ConflictError, NotFoundError
from app.dependencies.database import rls_db_session
from app.models.entities import Commitment
from app.schemas.commitment_actions import CommitmentActionInput
from app.services.commitment_actions import act
from tests.integration.conftest import requires_postgres
from tests.integration.test_assistant_connections_postgres import (
    assistant_owners as assistant_owners,
)
from tests.integration.test_meeting_intelligence_postgres import identity as set_identity

pytestmark = [pytest.mark.postgres, requires_postgres]


async def test_receipts_reject_cross_owner_links_and_browser_forgery(pg_engine, assistant_owners):
    owner, other = assistant_owners
    own_id, foreign_id = await create_commitment(owner), await create_commitment(other)
    await perform(owner, own_id, CommitmentActionInput(request_id=uuid4(), expected_revision=1, action='help'))
    statement = text("""INSERT INTO public.commitment_actions(user_id,commitment_id,request_id,action,request_hash,receipt)
        VALUES(CAST(:owner AS uuid),CAST(:source AS uuid),CAST(:request AS uuid),'help',:hash,'{}'::jsonb)""")
    async with pg_engine.begin() as db:
        await set_identity(db, owner)
        with pytest.raises(DBAPIError):
            async with db.begin_nested():
                await db.execute(statement, {'owner': owner, 'source': foreign_id, 'request': str(uuid4()), 'hash': '0' * 64})
    role = 'commitment_browser_' + uuid4().hex
    async with pg_engine.begin() as db:
        await db.execute(text(f'CREATE ROLE {role} NOLOGIN NOINHERIT'))
        await db.execute(text(f'GRANT authenticated TO {role}'))
        try:
            await db.execute(text(f'SET LOCAL SESSION AUTHORIZATION {role}'))
            await set_identity(db, owner)
            assert await db.scalar(text('SELECT count(*) FROM public.commitment_actions')) == 0
            with pytest.raises(DBAPIError):
                async with db.begin_nested():
                    await db.execute(statement, {'owner': owner, 'source': own_id, 'request': str(uuid4()), 'hash': '0' * 64})
        finally:
            await db.execute(text('RESET ROLE'))
            await db.execute(text('RESET SESSION AUTHORIZATION'))
            await db.execute(text(f'DROP ROLE {role}'))


async def create_commitment(owner):
    async with rls_db_session(owner) as db:
        row = Commitment(user_id=owner, description='Synthetic proposal', direction='owed_by_me')
        db.add(row)
        await db.commit()
        return str(row.id)


async def perform(owner, identity, payload):
    async with rls_db_session(owner) as db:
        try:
            receipt = await act(db, owner, identity, payload)
            await db.commit()
            return receipt
        except ConflictError:
            await db.rollback()
            return 'conflict'


async def test_identical_concurrent_action_commits_once(pg_engine, assistant_owners):
    owner = assistant_owners[0]
    identity = await create_commitment(owner)
    request = CommitmentActionInput(request_id=uuid4(), expected_revision=1, action='done')
    results = await asyncio.gather(*(perform(owner, identity, request) for _ in range(2)))
    assert results[0] == results[1] and results[0] != 'conflict'
    async with rls_db_session(owner) as db:
        assert (await db.get(Commitment, identity)).revision == 2
        assert await db.scalar(text('SELECT count(*) FROM public.commitment_actions')) == 1
    async with rls_db_session(assistant_owners[1]) as db:
        assert await db.scalar(text('SELECT count(*) FROM public.commitment_actions')) == 0
        with pytest.raises(NotFoundError):
            await act(db, assistant_owners[1], identity, request)


async def test_competing_actions_have_one_winner_and_database_edits_advance_revision(pg_engine, assistant_owners):
    owner = assistant_owners[0]
    identity = await create_commitment(owner)
    requests = [CommitmentActionInput(request_id=uuid4(), expected_revision=1, action=action) for action in ('done', 'working')]
    results = await asyncio.gather(*(perform(owner, identity, request) for request in requests))
    assert results.count('conflict') == 1
    async with rls_db_session(owner) as db:
        assert (await db.get(Commitment, identity)).revision == 2
        await db.execute(text("UPDATE public.commitments SET description='Edited later', revision=1 WHERE id=CAST(:id AS uuid)"), {'id': identity})
        await db.commit()
        assert (await db.get(Commitment, identity, populate_existing=True)).revision == 3
        assert not await db.scalar(text("SELECT has_table_privilege('authenticated','public.commitment_actions','TRUNCATE')"))
