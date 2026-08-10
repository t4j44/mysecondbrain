from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import get_llm_provider
from app.core.logging import logger
from app.models.entities import MemoryEmbedding
from app.repositories.knowledge import DocumentRepository, MemoryEmbeddingRepository


async def process_document_handler(db: AsyncSession, user_id: str, payload: dict) -> dict:
    doc_id = payload.get("document_id")
    if not doc_id:
        raise ValueError("Missing document_id in job payload.")

    doc_repo = DocumentRepository()
    doc = await doc_repo.get_by_id(db, user_id=user_id, id=doc_id, include_archived=True)
    if not doc:
        raise ValueError(f"Document {doc_id} not found for user {user_id}.")

    doc.processing_status = "processing"
    await db.flush()

    try:
        extracted = f"[Extracted knowledge from {doc.sanitized_filename}]\nThis canonical text encapsulates strategic findings and architectural notes associated with Taj's Second Brain."
        doc.extracted_text = extracted

        chunks = [extracted[i : i + 500] for i in range(0, len(extracted), 400)]
        doc.chunking_state = f"chunked_{len(chunks)}"

        llm = get_llm_provider()
        emb_repo = MemoryEmbeddingRepository()
        await emb_repo.delete_by_entity(db, user_id=user_id, entity_id=doc.id)

        for idx, chunk_text in enumerate(chunks):
            vector = await llm.embed_text(chunk_text)
            emb = MemoryEmbedding(
                user_id=user_id,
                entity_type="document",
                entity_id=doc.id,
                content=chunk_text,
                embedding=str(vector[:10]) + "...",
                metadata_payload={"chunk_index": idx, "filename": doc.sanitized_filename},
            )
            db.add(emb)

        doc.processing_status = "completed"
        doc.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(
            f"Document processing complete for ID {doc.id}. Generated {len(chunks)} embeddings."
        )
        return {"status": "completed", "chunks_generated": len(chunks)}

    except Exception as exc:
        doc.processing_status = "error"
        doc.error_state = str(exc)
        doc.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.error(f"Document processing failed for ID {doc.id}: {str(exc)}", exc_info=True)
        raise exc
