import asyncio

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
    from app.services.document_normalizer import converter_identity, normalize

    try:
        metadata = doc.conversion_metadata or {}
        if not doc.extracted_text or metadata.get("source_checksum") != doc.checksum or metadata.get("converter_identity") != converter_identity():
            content = await StorageService().read_file(doc.storage_path)
            markdown, metadata = await asyncio.to_thread(normalize, content, doc.filename)
            # Conversion ran outside the event loop; recheck deletion before saving.
            await db.refresh(doc)
            if doc.deleted_at is not None:
                raise ValueError("Document was deleted during conversion")
            doc.extracted_text = markdown
            doc.conversion_metadata = metadata
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
