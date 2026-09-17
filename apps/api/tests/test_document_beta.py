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
