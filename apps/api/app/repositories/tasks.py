from datetime import datetime
from typing import List, Optional

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self):
        super().__init__(Task)

    async def get_tasks_today(
        self, db: AsyncSession, user_id: str, start_of_day: datetime, end_of_day: datetime
    ) -> List[Task]:
        stmt = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.status != "done",
                Task.status != "cancelled",
                Task.deleted_at.is_(None),
                Task.due_date >= start_of_day,
                Task.due_date <= end_of_day,
            )
            .order_by(asc(Task.priority), asc(Task.due_date))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue_tasks(self, db: AsyncSession, user_id: str, now: datetime) -> List[Task]:
        stmt = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.status != "done",
                Task.status != "cancelled",
                Task.deleted_at.is_(None),
                Task.due_date < now,
            )
            .order_by(asc(Task.due_date))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_entity(
        self,
        db: AsyncSession,
        user_id: str,
        venture_id: Optional[str] = None,
        project_id: Optional[str] = None,
        person_id: Optional[str] = None,
    ) -> List[Task]:
        stmt = select(Task).where(Task.user_id == user_id, Task.deleted_at.is_(None))
        if venture_id:
            stmt = stmt.where(Task.venture_id == venture_id)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if person_id:
            stmt = stmt.where(Task.person_id == person_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())
