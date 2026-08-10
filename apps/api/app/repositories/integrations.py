from typing import List, Optional

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, ExportRecord, Integration, JobRecord
from app.repositories.base import BaseRepository


class IntegrationRepository(BaseRepository[Integration]):
    def __init__(self):
        super().__init__(Integration)

    async def get_by_provider(
        self, db: AsyncSession, user_id: str, provider: str
    ) -> Optional[Integration]:
        stmt = select(Integration).where(
            Integration.user_id == user_id, Integration.provider_name == provider
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class JobRepository(BaseRepository[JobRecord]):
    def __init__(self):
        super().__init__(JobRecord)

    async def get_pending_jobs(self, db: AsyncSession, limit: int = 10) -> List[JobRecord]:
        stmt = (
            select(JobRecord)
            .where(JobRecord.status == "pending")
            .order_by(asc(JobRecord.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_unscoped(self, db: AsyncSession, id: str) -> Optional[JobRecord]:
        stmt = select(JobRecord).where(JobRecord.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class ExportRepository(BaseRepository[ExportRecord]):
    def __init__(self):
        super().__init__(ExportRecord)


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)
