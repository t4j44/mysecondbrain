from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self):
        super().__init__(Project)

    async def get_by_venture(
        self, db: AsyncSession, user_id: str, venture_id: str
    ) -> List[Project]:
        stmt = select(Project).where(
            Project.user_id == user_id,
            Project.venture_id == venture_id,
            Project.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_count(self, db: AsyncSession, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Project)
            .where(
                Project.user_id == user_id,
                Project.status == "in_progress",
                Project.deleted_at.is_(None),
                Project.archived_at.is_(None),
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
