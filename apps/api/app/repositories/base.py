from typing import Any, Dict, Generic, Optional, Type, TypeVar

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResult, PaginationParams, validate_sort_field
from app.models.entities import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Abstract BaseRepository enforcing rigorous user isolation (auth.uid == user_id)
    and exclusion of soft-deleted/archived records by default.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self, db: AsyncSession, user_id: str, id: str, include_archived: bool = False
    ) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self.model.user_id == user_id)
        if not include_archived and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if not include_archived and hasattr(self.model, "archived_at"):
            stmt = stmt.where(self.model.archived_at.is_(None))

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        db: AsyncSession,
        user_id: str,
        pagination: PaginationParams,
        *,
        include_archived: Any = False,
        allowlist_sort_fields: Any = None,
        **filters: Any,
    ) -> PaginatedResult[ModelType]:
        stmt = select(self.model).where(self.model.user_id == user_id)
        count_stmt = (
            select(func.count()).select_from(self.model).where(self.model.user_id == user_id)
        )

        if not include_archived and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
            count_stmt = count_stmt.where(self.model.deleted_at.is_(None))
        if not include_archived and hasattr(self.model, "archived_at"):
            stmt = stmt.where(self.model.archived_at.is_(None))
            count_stmt = count_stmt.where(self.model.archived_at.is_(None))

        # Apply keyword matching and column exact filters
        for field, value in filters.items():
            if value is None or not hasattr(self.model, field):
                continue
            col = getattr(self.model, field)
            stmt = stmt.where(col == value)
            count_stmt = count_stmt.where(col == value)

        # Total count calculation
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        # Validate sort allowlist
        sort_fields = allowlist_sort_fields or ["created_at", "updated_at", "id"]
        valid_sort_field = validate_sort_field(pagination.sort_by or "created_at", sort_fields)
        sort_column = getattr(self.model, valid_sort_field, self.model.id)
        order_func = asc if pagination.sort_order.lower() == "asc" else desc

        stmt = (
            stmt.order_by(order_func(sort_column)).offset(pagination.offset).limit(pagination.limit)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult.create(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def create(self, db: AsyncSession, *, obj_in_data: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        from app.jobs.index_queue import queue_index
        queue_index(db, db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, user_id: str, id: str, update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        db_obj = await self.get_by_id(db, user_id=user_id, id=id, include_archived=True)
        if not db_obj:
            return None

        for field, value in update_data.items():
            if field in {"id", "user_id", "created_at"}:
                continue
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await db.flush()
        await db.refresh(db_obj)
        from app.jobs.index_queue import queue_index
        queue_index(db, db_obj)
        return db_obj

    async def delete(
        self, db: AsyncSession, user_id: str, id: str, hard_delete: bool = False
    ) -> bool:
        """Execute soft delete / archival by default to protect historical founder memory."""
        db_obj = await self.get_by_id(db, user_id=user_id, id=id, include_archived=True)
        if not db_obj:
            return False

        from app.jobs.index_queue import delete_index
        await delete_index(db, db_obj)

        if hard_delete:
            await db.delete(db_obj)
        else:
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            if hasattr(db_obj, "deleted_at"):
                db_obj.deleted_at = now
            elif hasattr(db_obj, "archived_at"):
                db_obj.archived_at = now

        await db.flush()
        return True
