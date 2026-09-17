"""
Application mappings for the canonical RAG tables owned by supabase/migrations 0008.

Mappings only — the retrieval/embedding pipeline is out of scope here (G4 owns it).
"""

from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, UniqueConstraint

from app.models.base import Base, FlexibleUUID
from app.models.entities import JSONEncodedDict, VectorType, utc_now
from app.utils.identifiers import generate_uuid

EMBEDDING_DIMENSIONS = 768


class DocumentChunk(Base):
    """Maps to canonical public.document_chunks."""

    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks"),)

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    document_id: Any = Column(
        FlexibleUUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Any = Column(Integer, nullable=False)
    chunk_text: Any = Column(Text, nullable=False)
    token_count: Any = Column(Integer, nullable=True)
    character_count: Any = Column(Integer, nullable=True)
    page_number: Any = Column(Integer, nullable=True)
    section_title: Any = Column(Text, nullable=True)
    meta: Any = Column("metadata", JSONEncodedDict, default=dict)
    checksum: Any = Column(Text, nullable=True)
    embedding_status: Any = Column(Text, default="pending")
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Embedding(Base):
    """Maps to canonical public.embeddings (pgvector 768 dimensions)."""

    __tablename__ = "embeddings"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    source_record_type: Any = Column(Text, nullable=False)
    source_record_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    document_chunk_id: Any = Column(
        FlexibleUUID, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True, index=True
    )
    embedding: Any = Column(VectorType(EMBEDDING_DIMENSIONS), nullable=False)
    provider: Any = Column(Text, nullable=False, default="gemini")
    model: Any = Column(Text, nullable=False, default="gemini-embedding-001")
    dimensions: Any = Column(Integer, nullable=False, default=EMBEDDING_DIMENSIONS)
    content_checksum: Any = Column(Text, nullable=True)
    meta: Any = Column("metadata", JSONEncodedDict, default=dict)
    version: Any = Column(Integer, nullable=False, default=1)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class EmbeddingJob(Base):
    """Maps to canonical public.embedding_jobs (asynchronous indexing queue)."""

    __tablename__ = "embedding_jobs"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    source_record_type: Any = Column(Text, nullable=False)
    source_record_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    document_chunk_id: Any = Column(
        FlexibleUUID, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Any = Column(Text, nullable=False, default="pending")
    error_message: Any = Column(Text, nullable=True)
    retry_count: Any = Column(Integer, nullable=False, default=0)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
