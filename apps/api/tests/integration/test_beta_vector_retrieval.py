"""Actual pgvector persistence/ranking and tenant checks with explicit test vectors.

This proves database behavior, not live Gemini quality. Never run on production.
"""
import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.indexing import index_record, semantic_search
from app.ai.provider import GeminiLLMProvider
from app.models.entities import Memory
from app.models.rag import Embedding
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]


@pytest.mark.asyncio
@pytest.mark.parametrize('search_path', ['public', 'public, extensions'])
async def test_real_vector_storage_filters_owner_deleted_and_stale(pg_engine, monkeypatch, search_path):
    owners = [str(uuid.uuid4()), str(uuid.uuid4())]
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: False)
    embedding = AsyncMock(return_value=[1.0] + [0.0] * 767)
    monkeypatch.setattr(GeminiLLMProvider, 'embed_text', embedding)
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with pg_engine.begin() as conn:
        for owner in owners:
            await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'),
                               {'id': owner, 'email': owner + '@vector.test'})
    try:
        async with factory() as db:
            records = [Memory(user_id=owner, title='Semantic evidence', content='Designed a retrieval system.') for owner in owners]
            db.add_all(records)
            await db.commit()
            for owner, record in zip(owners, records, strict=True):
                await index_record(db, owner, 'memory', str(record.id))
                await db.commit()
            rows = (await db.execute(select(Embedding).where(Embedding.user_id.in_(owners)))).scalars().all()
            assert len(rows) == 2 and all(len(row.embedding) == 768 for row in rows)
            again = await index_record(db, owners[0], 'memory', str(records[0].id))
            assert again['unchanged'] is True
            assert embedding.await_count == 2
            await db.execute(text("SELECT set_config('search_path', :path, true)"), {'path': search_path})
            results = await semantic_search(db, owners[0], 'retrieval architecture')
            assert [item.id for item in results] == [str(records[0].id)]
            assert results[0].search_mode == 'semantic'
            assert results[0].score == pytest.approx(1.0)
            records[0].content = 'Changed canonical evidence'
            await db.commit()
            assert await semantic_search(db, owners[0], 'retrieval architecture') == []
            await index_record(db, owners[0], 'memory', str(records[0].id))
            await db.commit()
            assert len(await semantic_search(db, owners[0], 'retrieval architecture')) == 1
            await db.execute(text('UPDATE memories SET deleted_at=now() WHERE id=CAST(:id AS uuid)'), {'id': str(records[0].id)})
            await db.commit()
            assert await semantic_search(db, owners[0], 'retrieval architecture') == []
    finally:
        async with pg_engine.begin() as conn:
            for owner in owners:
                await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})
