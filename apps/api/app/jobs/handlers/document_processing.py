from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.knowledge import DocumentRepository


async def process_document_handler(db: AsyncSession, user_id: str, payload: dict) -> dict:
    """
    Extract uploaded bytes locally and index minimized text.

    Success requires both real extraction and durable real vectors.
    """
    doc_id = payload.get("document_id")
    if not doc_id:
        raise ValueError("Missing document_id in job payload.")

    doc_repo = DocumentRepository()
    doc = await doc_repo.get_by_id(db, user_id=user_id, id=doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found for user {user_id}.")

    doc.processing_status = "processing"
    await db.flush()

    from app.ai.indexing import index_record
    from app.integrations.storage_client import StorageService
    from app.services.document_extractor import DocumentExtractor

    try:
        content = await StorageService().read_file(doc.storage_path)
        extracted = DocumentExtractor.extract_text(content, doc.filename, doc.mime_type)
        if not extracted.success:
            raise ValueError(extracted.error)
        doc.extracted_text = extracted.extracted_text
        doc.chunking_state = "extracted"
        # Preserve successful local extraction even when free AI is unavailable.
        await db.commit()
        result = await index_record(db, user_id, "document", str(doc.id))
        doc.processing_status = "completed"
        doc.chunking_state = "completed"
        doc.error_state = None
        await db.commit()
        return result
    except Exception as exc:
        await db.rollback()
        doc = await doc_repo.get_by_id(db, user_id=user_id, id=doc_id)
        if doc:
            doc.processing_status = "failed"
            doc.error_state = getattr(exc, "code", "DOCUMENT_PROCESSING_FAILED")
            await db.commit()
        raise
