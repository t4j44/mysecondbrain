"""Prompt context against migrated PostgreSQL RLS, not SQLite policy simulation."""
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.privacy import private_ai_scope
from app.core.errors import AIProviderError
from app.mcp.tools import MCPDomainTools
from app.models.entities import ContextEvent
from app.services.prompt_context import retrieve_prompt_context
from tests.integration.conftest import requires_postgres
from tests.integration.test_context_v15_postgres import (
    context_fixture as shared_context_fixture,
)
from tests.integration.test_context_v15_postgres import identity

context_fixture = shared_context_fixture
pytestmark = [pytest.mark.postgres, requires_postgres]


@pytest.mark.parametrize('claim', ['owner', 'other'])
async def test_prompt_context_claims_recheck_and_no_domain_mutation(pg_engine, context_fixture, monkeypatch, claim):
    ids = context_fixture
    async def offline(*args, **kwargs):
        raise AIProviderError('Synthetic embedding unavailable')
    monkeypatch.setattr('app.services.prompt_context.semantic_search', offline)
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    statements = []
    def observe(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.strip().upper())
    async with factory() as db:
        await identity(db, ids[claim])
        event.listen(pg_engine.sync_engine, 'before_cursor_execute', observe)
        try:
            # Even if an owner argument were forged, the authenticated DB role filters it.
            results = await retrieve_prompt_context(db, ids['owner'], 'cobalt', 8)
            assert [item['id'] for item in results] == ([ids['event']] if claim == 'owner' else [])
            assert not any(sql.startswith(('INSERT', 'UPDATE', 'DELETE')) for sql in statements)
            if claim == 'owner':
                row = (await db.execute(select(ContextEvent).where(ContextEvent.id == ids['event']))).scalar_one()
                row.privacy_class = 'restricted'
                await db.flush()
                assert await retrieve_prompt_context(db, ids['owner'], 'cobalt', 8) == []
        finally:
            event.remove(pg_engine.sync_engine, 'before_cursor_execute', observe)
            await db.rollback()


async def test_plain_prompt_does_not_query_canonical_postgres(pg_engine, context_fixture, monkeypatch):
    ids = context_fixture
    provider = AsyncMock()
    provider.generate_content.return_value = 'Please clarify the supplied sentence.'
    monkeypatch.setattr('app.services.prompt_enhancer.get_llm_provider', lambda: provider)
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    def forbidden(*args):
        raise AssertionError('Plain enhancement queried PostgreSQL')
    async with factory() as db:
        await identity(db, ids['owner'])
        event.listen(pg_engine.sync_engine, 'before_cursor_execute', forbidden)
        try:
            with private_ai_scope(ids['owner'], db):
                result = await MCPDomainTools(db=db, user_id=ids['owner']).enhance_prompt(text='clarify this sentence')
            assert result['context_items_used'] == 0
        finally:
            event.remove(pg_engine.sync_engine, 'before_cursor_execute', forbidden)
