"""Canonical, restartable indexing over existing records and pgvector tables."""

import hashlib
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, and_, cast, delete, exists, literal, or_, select, text
from sqlalchemy.dialects.postgresql import JSONB

from app.ai.privacy import private_ai_scope
from app.ai.provider import GeminiLLMProvider
from app.core.config import settings
from app.core.errors import AIProviderError, NotFoundError
from app.models import entities as m
from app.models.rag import DocumentChunk, Embedding
from app.schemas.knowledge import SearchResultItem
from app.services.document_chunker import CHUNKING_VERSION, chunk_markdown
from app.services.document_extractor import DocumentExtractor

SOURCES = {
    "memory": (m.Memory, ("title", "content")),
    "person": (m.Person, ("name", "role", "company", "notes")),
    "organization": (m.Organization, ("name", "description", "industry")),
    "interaction": (m.Interaction, ("title", "summary", "detailed_notes", "location")),
    "meeting": (m.Meeting, ("title", "summary", "notes", "agenda")),
    "project": (m.Project, ("name", "description")),
    "task": (m.Task, ("title", "description", "status", "due_date")),
    "commitment": (m.Commitment, ("description", "notes", "direction", "status", "due_at")),
    "venture": (m.Venture, ("name", "description")),
    "document": (m.Document, ("filename", "extracted_text")),
    "achievement": (m.Achievement, ("title", "role", "problem", "impact", "responsibilities", "skills")),
    "work_session": (m.WorkSession, ("title", "objective", "summary", "outcomes", "skills_exercised")),
    "evidence": (m.EvidenceItem, ("title", "content")),
    "decision": (m.Decision, ("title", "context", "decision", "rationale", "expected_impact")),
}


def record_text(record: Any, kind: str) -> str:
    return "\n".join(f"{key}: {getattr(record, key)}" for key in SOURCES[kind][1]
                     if getattr(record, key, None))


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def owned_record(db, user_id: str, kind: str, record_id: str):
    if kind not in SOURCES:
        raise NotFoundError("Unsupported source type.")
    model = SOURCES[kind][0]
    clauses = [
        model.id == record_id, model.user_id == user_id,
        model.deleted_at.is_(None),
    ]
    if hasattr(model, "archived_at"):
        clauses.append(model.archived_at.is_(None))
    result = await db.execute(select(model).where(*clauses))
    record = result.scalar_one_or_none()
    if record is None:
        raise NotFoundError("Source is not available.")
    return record


async def index_record(db, user_id: str, kind: str, record_id: str) -> dict:
    if db.bind.dialect.name == 'postgresql':
        # Serialize index replacement for the same owner/source across workers.
        await db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))'),
            {'key': f'index:{user_id}:{kind}:{record_id}'})
    record = await owned_record(db, user_id, kind, record_id)
    llm = GeminiLLMProvider()
    if llm._is_unconfigured():
        raise AIProviderError(message="Configure Gemini before indexing. No synthetic vectors were stored.")
    source = record_text(record, kind)
    existing = (await db.execute(select(Embedding).where(Embedding.user_id == user_id,
        Embedding.source_record_type == kind, Embedding.source_record_id == record_id,
        Embedding.model == llm.embedding_model))).scalars().all()
    if existing and all(row.meta.get('source_fingerprint') == fingerprint(source)
                        and row.meta.get('data_mode') == settings.AI_DATA_MODE
                        and row.meta.get('privacy_version') == 1
                        and row.meta.get('chunking_version') == CHUNKING_VERSION for row in existing):
        return {'source_type': kind, 'source_id': str(record_id), 'chunks': len(existing), 'unchanged': True}
    chunks = chunk_markdown(record.extracted_text or "") if kind == "document" else DocumentExtractor.split_text_into_chunks(source, chunk_size=1200, overlap=150)
    if len(chunks) > 100:
        raise AIProviderError(message="This beta supports up to 100 text chunks per record.")
    # Finish inference before replacing a previous index. Failures leave the old
    # index intact (retrieval rejects stale fingerprints).
    vectors = []
    with private_ai_scope(user_id, db):
        for chunk in chunks:
            vectors.append(await llm.embed_text(chunk["chunk_text"]))
    await db.execute(delete(Embedding).where(
        Embedding.user_id == user_id, Embedding.source_record_type == kind,
        Embedding.source_record_id == record_id,
    ))
    reusable_chunks = {}
    if kind == "document":
        stored = (await db.execute(select(DocumentChunk).where(
            DocumentChunk.user_id == user_id, DocumentChunk.document_id == record_id,
        ).order_by(DocumentChunk.chunk_index))).scalars().all()
        if len(stored) == len(chunks) and all(
            row.checksum == chunk['checksum'] and row.meta.get('chunking_version') == CHUNKING_VERSION
            and row.meta.get('source_checksum') == record.checksum
            for row, chunk in zip(stored, chunks, strict=True)
        ):
            reusable_chunks = {row.chunk_index: row for row in stored}
        else:
            await db.execute(delete(DocumentChunk).where(
                DocumentChunk.user_id == user_id, DocumentChunk.document_id == record_id,
            ))
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk_id = None
        if kind == "document":
            doc_chunk = reusable_chunks.get(chunk['chunk_index'])
            if doc_chunk is None:
                doc_chunk = DocumentChunk(user_id=user_id, document_id=record_id,
                    chunk_index=chunk["chunk_index"], chunk_text=chunk["chunk_text"],
                    token_count=chunk["token_count"], character_count=chunk["character_count"],
                    checksum=chunk["checksum"], embedding_status="completed",
                    section_title=chunk.get("section_title"), page_number=chunk.get("page_number"),
                    meta={**chunk.get("metadata", {}), "source_checksum": record.checksum})
                db.add(doc_chunk)
                await db.flush()
            chunk_id = doc_chunk.id
        db.add(Embedding(user_id=user_id, source_record_type=kind,
            source_record_id=record_id, document_chunk_id=chunk_id, embedding=vector,
            provider="gemini", model=llm.embedding_model, dimensions=768,
            content_checksum=chunk["checksum"], meta={
                "content": chunk["chunk_text"], "source_fingerprint": fingerprint(source),
                "data_mode": settings.AI_DATA_MODE, "privacy_version": 1,
                "chunking_version": CHUNKING_VERSION, "chunk_index": chunk["chunk_index"],
                "section_title": chunk.get("section_title"), "page_number": chunk.get("page_number"),
            }))
    if hasattr(record, "embedding_status"):
        record.embedding_status = "completed"
    await db.flush()
    return {"source_type": kind, "source_id": str(record_id), "chunks": len(chunks)}


async def semantic_search(db, user_id: str, query: str, limit: int = 10,
                          entity_types: list[str] | None = None) -> list[SearchResultItem]:
    if db.bind.dialect.name != "postgresql":
        raise AIProviderError(message="Semantic retrieval requires PostgreSQL with pgvector.")
    llm = GeminiLLMProvider()
    if llm._is_unconfigured():
        raise AIProviderError(message="Semantic retrieval requires a configured embedding provider.")
    with private_ai_scope(user_id, db):
        vector = await llm.embed_text(query, task_type="RETRIEVAL_QUERY")
    kinds = [kind for kind in (entity_types or list(SOURCES)) if kind in SOURCES]
    if not kinds:
        return []
    # Build correlated owner/visibility checks with SQLAlchemy; all values are
    # bound parameters, and filters run before vector ranking.
    live = []
    for kind in kinds:
        model = SOURCES[kind][0]
        conditions = [model.id == Embedding.source_record_id,
                      model.user_id == Embedding.user_id, model.deleted_at.is_(None)]
        if hasattr(model, "archived_at"):
            conditions.append(model.archived_at.is_(None))
        live.append(and_(Embedding.source_record_type == kind,
                         exists(select(model.id).where(*conditions))))
    metadata = cast(Embedding.meta, JSONB)
    # Migrations install pgvector in extensions; do not depend on a connection's
    # search_path including that schema to resolve the cosine-distance operator.
    distance = Embedding.embedding.op("OPERATOR(extensions.<=>)", return_type=Float)(
        literal(vector, type_=Vector(768)))
    result = await db.execute(select(
        Embedding.source_record_type, Embedding.source_record_id, Embedding.document_chunk_id,
        Embedding.meta.label("metadata"), (1 - distance).label("score"),
    ).where(
        Embedding.user_id == user_id, Embedding.model == llm.embedding_model,
        metadata["data_mode"].astext == settings.AI_DATA_MODE,
        metadata["privacy_version"].astext == '1',
        metadata["chunking_version"].astext == str(CHUNKING_VERSION), or_(*live),
    ).order_by(distance).limit(min(max(limit, 1), 50) * 4))
    items = []
    seen = set()
    for row in result.mappings():
        kind, identity = row["source_record_type"], str(row["source_record_id"])
        key = (kind, str(row["document_chunk_id"]) if kind == "document" else identity)
        if key in seen:
            continue
        record = await owned_record(db, user_id, kind, identity)
        metadata = row["metadata"]
        if metadata.get("source_fingerprint") != fingerprint(record_text(record, kind)):
            continue
        if float(row["score"]) < 0.25:
            continue
        seen.add(key)
        items.append(SearchResultItem(id=identity, entity_type=kind,
            title=str(getattr(record, "title", None) or getattr(record, "name", None)
                      or getattr(record, "filename", None) or kind),
            snippet=metadata.get("content", "")[:1800], score=float(row["score"]),
            chunk_id=str(row["document_chunk_id"]) if row["document_chunk_id"] else None,
            chunk_index=metadata.get("chunk_index"), section=metadata.get("section_title"),
            page=metadata.get("page_number"),
            confidence_available=False, search_mode="semantic"))
        if len(items) >= limit:
            break
    return items
