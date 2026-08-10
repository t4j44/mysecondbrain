from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    KPI,
    Achievement,
    ContentItem,
    ContentVersion,
    Decision,
    Document,
    Idea,
    KPIEntry,
    Memory,
    MemoryEmbedding,
    PortfolioCaseStudy,
    WeeklyReview,
)
from app.repositories.base import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    def __init__(self):
        super().__init__(Memory)

    async def get_recent(self, db: AsyncSession, user_id: str, limit: int = 5) -> List[Memory]:
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id, Memory.deleted_at.is_(None), Memory.archived_at.is_(None)
            )
            .order_by(desc(Memory.memory_date))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class MemoryEmbeddingRepository(BaseRepository[MemoryEmbedding]):
    def __init__(self):
        super().__init__(MemoryEmbedding)

    async def delete_by_entity(self, db: AsyncSession, user_id: str, entity_id: str) -> None:
        stmt = select(MemoryEmbedding).where(
            MemoryEmbedding.user_id == user_id, MemoryEmbedding.entity_id == entity_id
        )
        result = await db.execute(stmt)
        for emb in result.scalars().all():
            await db.delete(emb)
        await db.flush()

    async def search_similar(
        self, db: AsyncSession, user_id: str, query_text: str, limit: int = 10
    ) -> List[MemoryEmbedding]:
        # Perform fallback ILIKE search across embeddings content when vector extensions are disabled in local testing
        stmt = (
            select(MemoryEmbedding)
            .where(
                MemoryEmbedding.user_id == user_id,
                func.lower(MemoryEmbedding.content).contains(query_text.lower()),
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class IdeaRepository(BaseRepository[Idea]):
    def __init__(self):
        super().__init__(Idea)


class DecisionRepository(BaseRepository[Decision]):
    def __init__(self):
        super().__init__(Decision)


class DocumentRepository(BaseRepository[Document]):
    def __init__(self):
        super().__init__(Document)

    async def get_by_checksum(
        self, db: AsyncSession, user_id: str, checksum: str
    ) -> Optional[Document]:
        stmt = select(Document).where(
            Document.user_id == user_id,
            Document.checksum == checksum,
            Document.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class KPIRepository(BaseRepository[KPI]):
    def __init__(self):
        super().__init__(KPI)

    async def get_active_kpis(self, db: AsyncSession, user_id: str) -> List[KPI]:
        stmt = select(KPI).where(
            KPI.user_id == user_id,
            KPI.is_active.is_(True),
            KPI.deleted_at.is_(None),
            KPI.archived_at.is_(None),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class KPIEntryRepository(BaseRepository[KPIEntry]):
    def __init__(self):
        super().__init__(KPIEntry)

    async def get_by_kpi(self, db: AsyncSession, user_id: str, kpi_id: str) -> List[KPIEntry]:
        stmt = (
            select(KPIEntry)
            .where(KPIEntry.user_id == user_id, KPIEntry.kpi_id == kpi_id)
            .order_by(desc(KPIEntry.entry_date))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(self):
        super().__init__(Achievement)


class PortfolioCaseStudyRepository(BaseRepository[PortfolioCaseStudy]):
    def __init__(self):
        super().__init__(PortfolioCaseStudy)


class ContentRepository(BaseRepository[ContentItem]):
    def __init__(self):
        super().__init__(ContentItem)


class ContentVersionRepository(BaseRepository[ContentVersion]):
    def __init__(self):
        super().__init__(ContentVersion)

    async def list_versions(
        self, db: AsyncSession, user_id: str, content_id: str
    ) -> List[ContentVersion]:
        stmt = (
            select(ContentVersion)
            .where(ContentVersion.user_id == user_id, ContentVersion.content_id == content_id)
            .order_by(desc(ContentVersion.version_number))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class WeeklyReviewRepository(BaseRepository[WeeklyReview]):
    def __init__(self):
        super().__init__(WeeklyReview)
