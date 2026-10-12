from typing import List, Optional

from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, ExportRecord, Integration, JobRecord
from app.repositories.base import BaseRepository


class IntegrationRepository(BaseRepository[Integration]):
    def __init__(self):
        super().__init__(Integration)

    async def list_for_provider(
        self, db: AsyncSession, user_id: str, provider: str
    ) -> List[Integration]:
        stmt = select(Integration).where(
            Integration.user_id == user_id, Integration.provider_name == provider
        ).order_by(asc(Integration.created_at), asc(Integration.id))
        return list((await db.execute(stmt)).scalars().all())

    async def get_for_account(
        self, db: AsyncSession, user_id: str, provider: str, account: Optional[str]
    ) -> Optional[Integration]:
        """The row for one Google account; `None` finds the row from before accounts were recorded."""
        stmt = select(Integration).where(
            Integration.user_id == user_id, Integration.provider_name == provider,
            Integration.account_identifier.is_(None) if account is None
            else func.lower(Integration.account_identifier) == account.lower(),
        )
        return (await db.execute(stmt.limit(1))).scalars().first()

    async def get_by_provider(
        self, db: AsyncSession, user_id: str, provider: str
    ) -> Optional[Integration]:
        rows = await self.list_for_provider(db, user_id, provider)
        return next((row for row in rows if row.is_connected), rows[0] if rows else None)


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
