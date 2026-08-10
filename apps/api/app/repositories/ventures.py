from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Venture
from app.repositories.base import BaseRepository


class VentureRepository(BaseRepository[Venture]):
    def __init__(self):
        super().__init__(Venture)

    async def get_by_slug(
        self, db: AsyncSession, user_id: str, slug: str, include_archived: bool = False
    ) -> Optional[Venture]:
        stmt = select(Venture).where(Venture.user_id == user_id, Venture.slug == slug)
        if not include_archived:
            stmt = stmt.where(Venture.deleted_at.is_(None), Venture.archived_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, user_id: str, name: str) -> Optional[Venture]:
        stmt = select(Venture).where(
            Venture.user_id == user_id,
            func.lower(Venture.name) == func.lower(name),
            Venture.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_count(self, db: AsyncSession, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Venture)
            .where(
                Venture.user_id == user_id,
                Venture.status == "active",
                Venture.deleted_at.is_(None),
                Venture.archived_at.is_(None),
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
