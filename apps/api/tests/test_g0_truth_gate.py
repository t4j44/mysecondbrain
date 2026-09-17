"""G0 Product Truth Gate — regression tests against false-success paths."""

from __future__ import annotations

import inspect

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.ai.embeddings_storage import (
    looks_like_truncated_embedding_dump,
    refuse_embedding_success_without_vector_storage,
    require_storable_embedding_vector,
)
from app.ai.provider import GeminiLLMProvider
from app.ai.retrieval import perform_keyword_search
from app.core.config import settings
from app.core.constants import ErrorCode
from app.core.errors import (
    AIProviderError,
    EmbeddingStorageNotImplementedError,
    IntegrationError,
)
from app.integrations.google_client import GoogleIntegrationService
from app.jobs.handlers.document_processing import process_document_handler
from app.mcp import server as mcp_server_module
from app.mcp.router import MCP_ALL_TOOLS, MCP_WRITE_TOOLS_MANIFEST
from app.mcp.tools import MCPDomainTools
from app.models.entities import Document, Memory, MemoryEmbedding, Profile


async def _ensure_profile(db, user_id: str) -> None:
    existing = await db.get(Profile, user_id)
    if existing:
        return
    db.add(Profile(id=user_id, email=f"{user_id}@test.local", settings={}))
    await db.flush()


async def _create_document(db, user_id: str) -> Document:
    await _ensure_profile(db, user_id)
    doc = Document(
        user_id=user_id,
        filename="strategy-notes.pdf",
        sanitized_filename="strategy-notes.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size_bytes=1024,
        checksum="abc123checksum",
        storage_bucket="brain-documents",
        storage_path="uploads/strategy-notes.pdf",
        processing_status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_document_pipeline_cannot_persist_fabricated_text(
    prepare_database, test_user_id: str
):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as db:
        doc = await _create_document(db, test_user_id)
        with pytest.raises(FileNotFoundError):
            await process_document_handler(db, test_user_id, {"document_id": doc.id})

        await db.refresh(doc)
        assert doc.extracted_text in (None, "")
        assert doc.processing_status == "failed"
        assert doc.error_state == "DOCUMENT_PROCESSING_FAILED"
        assert "Extracted knowledge from" not in (doc.extracted_text or "")

        emb_rows = (
            await db.execute(
                select(MemoryEmbedding).where(
                    MemoryEmbedding.user_id == test_user_id,
                    MemoryEmbedding.entity_id == doc.id,
                )
            )
        ).scalars().all()
        assert emb_rows == []


def test_document_handler_source_has_no_fabricated_template():
    source = inspect.getsource(process_document_handler)
    assert "Extracted knowledge from" not in source
    assert "str(vector[:10])" not in source


def test_truncated_or_fake_embeddings_cannot_be_reported_as_success():
    fake_dump = str([0.01] * 10) + "..."
    assert looks_like_truncated_embedding_dump(fake_dump) is True

    with pytest.raises(EmbeddingStorageNotImplementedError):
        require_storable_embedding_vector(fake_dump)

    with pytest.raises(EmbeddingStorageNotImplementedError):
        require_storable_embedding_vector([0.1, 0.2, 0.3])

    with pytest.raises(EmbeddingStorageNotImplementedError) as exc_info:
        refuse_embedding_success_without_vector_storage(context="g0_test")
    assert exc_info.value.code == ErrorCode.EMBEDDING_STORAGE_NOT_IMPLEMENTED.value

    ok = require_storable_embedding_vector([0.01] * 768)
    assert len(ok) == 768


@pytest.mark.asyncio
async def test_retrieval_never_emits_constant_089(prepare_database, test_user_id: str):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as db:
        await _ensure_profile(db, test_user_id)
        db.add(Memory(user_id=test_user_id, title='Strategy', content='founder strategy keyword evidence about ventures'))
        db.add(
            MemoryEmbedding(
                user_id=test_user_id,
                entity_type="memory",
                entity_id="11111111-1111-4111-a111-111111111111",
                content="founder strategy keyword evidence about ventures",
                embedding=None,
                metadata_payload={},
            )
        )
        await db.commit()

        results = await perform_keyword_search(db, test_user_id, "strategy", limit=5)
        assert results, "keyword search should find the seeded content row"
        for item in results:
            assert item.score is None
            assert item.score != 0.89
            assert item.confidence_available is False
            assert item.search_mode == "keyword"

    import app.ai.retrieval as retrieval_mod

    assert "0.89" not in inspect.getsource(retrieval_mod)


@pytest.mark.asyncio
async def test_google_cannot_report_connected_without_real_integration(
    async_client: AsyncClient, auth_headers: dict, prepare_database, test_user_id: str
):
    res = await async_client.post(
        "/api/v1/integrations/google/callback",
        json={"code": "any_oauth_code_12345", "state": "state"},
        headers=auth_headers,
    )
    assert res.status_code == 503
    assert res.json()['error']['code'] == 'GOOGLE_NOT_CONFIGURED'
    list_res = await async_client.get('/api/v1/integrations', headers=auth_headers)
    assert list_res.status_code == 200
    assert not list_res.json()['items']
    sync_res = await async_client.post('/api/v1/sync/gdrive', json={}, headers=auth_headers)
    assert sync_res.status_code == 409
    assert 'simulated_refresh_token' not in inspect.getsource(GoogleIntegrationService)


@pytest.mark.asyncio
async def test_mcp_writes_are_exposed_truthfully_and_still_fail_closed(
    async_client: AsyncClient,
):
    """
    G5 replaced the G0 'writes exist but are hidden' posture with real exposure. The truth
    rule is unchanged: what the server advertises must match what it actually registers,
    and an unauthenticated caller must still be refused.
    """
    write_tools = [t["name"] for t in MCP_WRITE_TOOLS_MANIFEST]
    for write_tool in write_tools:
        assert hasattr(MCPDomainTools, write_tool)

    info = await async_client.get("/mcp")
    assert info.status_code == 200
    body = info.json()
    assert body["write_tools_status"] == "EXPOSED_SCOPE_ENFORCED"
    assert set(write_tools) == set(body["write_tools"])
    assert set(body["registered_tools"]) == {t["name"] for t in MCP_ALL_TOOLS}

    tools_res = await async_client.get("/mcp/tools")
    assert tools_res.status_code == 200
    advertised = {t["name"] for t in tools_res.json()["tools"]}
    assert set(write_tools).issubset(advertised)

    invoke = await async_client.post(
        "/mcp/tools/invoke",
        json={"tool": "create_task", "arguments": {"title": "should fail"}},
        headers={"X-MCP-API-KEY": "not-a-real-key"},
    )
    assert invoke.status_code == 401

    server_src = inspect.getsource(mcp_server_module)
    for write_tool in write_tools:
        assert f"async def {write_tool}" in server_src


@pytest.mark.asyncio
async def test_production_environment_cannot_silently_select_simulation(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "APP_ENV", "production")

    provider = GeminiLLMProvider(api_key="placeholder_gemini_key")
    assert provider._is_unconfigured() is True

    with pytest.raises(AIProviderError) as gen_exc:
        await provider.generate_content("hello founder")
    assert gen_exc.value.code == ErrorCode.AI_PROVIDER_NOT_CONFIGURED.value

    with pytest.raises(AIProviderError) as emb_exc:
        await provider.embed_text("hello founder")
    assert emb_exc.value.code == ErrorCode.AI_PROVIDER_NOT_CONFIGURED.value

    class _DummyDb:
        pass

    svc = GoogleIntegrationService(_DummyDb(), "user-prod")  # type: ignore[arg-type]
    with pytest.raises(IntegrationError) as exc:
        await svc.connect_oauth_callback('code1234567890', None)
    assert exc.value.code == 'GOOGLE_NOT_CONFIGURED'
