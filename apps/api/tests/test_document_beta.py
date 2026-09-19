from unittest.mock import AsyncMock

import pytest

from app.ai.provider import GeminiLLMProvider
from app.ai.retrieval import perform_keyword_search
from app.core.errors import AIProviderError
from app.integrations.storage_client import StorageService
from app.jobs.handlers.document_processing import process_document_handler
from app.models.entities import Document
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_extracted_document_remains_searchable_when_ai_is_unavailable(test_user_id, other_user_id, monkeypatch):
    monkeypatch.setattr(StorageService, 'read_file', AsyncMock(return_value=b'Retrieval prototype evidence'))
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    async with TestingSessionLocal() as db:
        document = Document(user_id=test_user_id, filename='evidence.txt', sanitized_filename='evidence.txt',
            extension='txt', mime_type='text/plain', size_bytes=28, checksum='synthetic-test',
            storage_bucket='brain-documents', storage_path=test_user_id + '/evidence.txt')
        db.add(document)
        await db.commit()
        with pytest.raises(AIProviderError):
            await process_document_handler(db, test_user_id, {'document_id': str(document.id)})
        await db.refresh(document)
        assert document.extracted_text == 'Retrieval prototype evidence'
        assert document.processing_status == 'failed'
        assert document.chunking_state == 'extracted'
        assert [item.id for item in await perform_keyword_search(db, test_user_id, 'prototype')] == [str(document.id)]
        assert await perform_keyword_search(db, other_user_id, 'prototype') == []


@pytest.mark.asyncio
async def test_queued_delete_cannot_remove_identical_reupload(test_user_id, monkeypatch, tmp_path):
    from sqlalchemy import select

    from app.core.config import settings
    from app.jobs.runner import JobRunner
    from app.models.entities import JobRecord
    from app.services.knowledge import DocumentService
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, 'SUPABASE_URL', '')
    async with TestingSessionLocal() as db:
        service = DocumentService(db, test_user_id)
        old = await service.upload_document('fixture.txt', b'synthetic repeat', 'text/plain')
        old_path = old.storage_path
        await service.delete_document(str(old.id))
        new = await service.upload_document('fixture.txt', b'synthetic repeat', 'text/plain')
        assert new.storage_path != old_path
        deletion = (await db.execute(select(JobRecord).where(JobRecord.job_type == 'storage_delete'))).scalar_one()
        await JobRunner._execute_payload(db, test_user_id, 'storage_delete', deletion.result_payload)
        assert await service.storage.read_file(new.storage_path) == b'synthetic repeat'
        with pytest.raises(FileNotFoundError):
            await service.storage.read_file(old_path)
        duplicate = await service.upload_document('another-name.txt', b'synthetic repeat', 'text/plain')
        assert duplicate.id == new.id
