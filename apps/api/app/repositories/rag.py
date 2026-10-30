"""
Repositories for the canonical RAG tables (documents chunks, embeddings, embedding jobs).

Data access only. Chunking, embedding generation, and similarity ranking are not
implemented here — G4 owns the retrieval pipeline.
"""

from typing import List, Optional

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag import DocumentChunk, Embedding, EmbeddingJob
from app.repositories.base import BaseRepository


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    def __init__(self):
        super().__init__(DocumentChunk)

    async def list_for_document(
        self, db: AsyncSession, user_id: str, document_id: str
    ) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.user_id == user_id, DocumentChunk.document_id == document_id)
            .order_by(asc(DocumentChunk.chunk_index))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class EmbeddingRepository(BaseRepository[Embedding]):
    def __init__(self):
        super().__init__(Embedding)

    async def get_for_chunk(
        self, db: AsyncSession, user_id: str, document_chunk_id: str
    ) -> Optional[Embedding]:
        stmt = select(Embedding).where(
            Embedding.user_id == user_id,
            Embedding.document_chunk_id == document_chunk_id,
        )
        result = await db.execute(stmt)
        return result.scalars().first()


class EmbeddingJobRepository(BaseRepository[EmbeddingJob]):
    def __init__(self):
        super().__init__(EmbeddingJob)

    async def list_pending(
        self, db: AsyncSession, user_id: str, limit: int = 50
    ) -> List[EmbeddingJob]:
        stmt = (
            select(EmbeddingJob)
            .where(EmbeddingJob.user_id == user_id, EmbeddingJob.status == "pending")
            .order_by(asc(EmbeddingJob.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
