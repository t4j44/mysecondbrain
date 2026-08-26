from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DocumentExtractionNotImplementedError
from app.core.logging import logger
from app.repositories.knowledge import DocumentRepository


async def process_document_handler(db: AsyncSession, user_id: str, payload: dict) -> dict:
    """
    Document processing job (G0 fail-closed).

    Real byte extraction + vector embedding persistence are deferred (G4).
    This handler MUST NOT invent canonical text or report embedding success.
    """
    doc_id = payload.get("document_id")
    if not doc_id:
        raise ValueError("Missing document_id in job payload.")

    doc_repo = DocumentRepository()
    doc = await doc_repo.get_by_id(db, user_id=user_id, id=doc_id, include_archived=True)
    if not doc:
        raise ValueError(f"Document {doc_id} not found for user {user_id}.")

    doc.processing_status = "processing"
    await db.flush()

    # G0: refuse fabricated extraction. Do not open/store invented text.
    # DocumentExtractor exists for future wiring (G4) but is intentionally not
    # invoked here until the job opens real uploaded bytes end-to-end.
    failure = DocumentExtractionNotImplementedError(
        details={
            "document_id": str(doc.id),
            "filename": getattr(doc, "sanitized_filename", None)
            or getattr(doc, "filename", None),
        },
    )
    doc.extracted_text = None
    doc.chunking_state = None
    doc.processing_status = "failed"
    doc.error_state = failure.code
    doc.updated_at = datetime.now(timezone.utc)
    await db.commit()
    logger.warning(
        "Document processing blocked (extraction not implemented) for ID %s.",
        doc.id,
    )
    raise failure
