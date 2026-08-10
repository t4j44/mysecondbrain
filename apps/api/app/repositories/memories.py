from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import String, and_, asc, cast, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import NotFoundError
from app.models.entities import Person
from app.models.memories import Memory
from app.schemas.memories import MemoryCreate, MemoryUpdate


class MemoriesRepository:
    @staticmethod
    async def create_memory(db: AsyncSession, user_id: UUID, schema: MemoryCreate) -> Memory:
        # Validate person if linked
        if schema.linked_person_id:
            p_query = select(Person).where(
                and_(Person.id == schema.linked_person_id, Person.user_id == user_id)
            )
            p_result = await db.execute(p_query)
            if not p_result.scalar_one_or_none():
                raise NotFoundError(f"Linked contact with ID {schema.linked_person_id} not found.")

        db_memory = Memory(
            user_id=user_id,
            title=schema.title,
            content=schema.content,
            category=schema.category,
            tags=schema.tags,
            linked_venture_id=schema.linked_venture_id,
            linked_person_id=schema.linked_person_id,
            meta=schema.metadata,
        )
        db.add(db_memory)
        await db.commit()
        await db.refresh(db_memory)
        return db_memory

    @staticmethod
    async def get_memory(db: AsyncSession, user_id: UUID, memory_id: UUID) -> Memory:
        query = select(Memory).where(
            and_(Memory.id == memory_id, Memory.user_id == user_id, Memory.deleted_at.is_(None))
        )
        result = await db.execute(query)
        db_memory = result.scalar_one_or_none()
        if not db_memory:
            raise NotFoundError("Memory not found or access denied.")
        return db_memory

    @staticmethod
    async def list_memories(
        db: AsyncSession,
        user_id: UUID,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        linked_venture_id: Optional[UUID] = None,
        linked_person_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Memory], int]:
        query = select(Memory).where(and_(Memory.user_id == user_id, Memory.deleted_at.is_(None)))

        if category:
            query = query.where(Memory.category == category)
        if tag:
            if db.bind and db.bind.dialect.name == "sqlite":
                query = query.where(cast(Memory.tags, String).like(f"%{tag}%"))
            else:
                query = query.where(Memory.tags.any(tag))
        if linked_venture_id:
            query = query.where(Memory.linked_venture_id == linked_venture_id)
        if linked_person_id:
            query = query.where(Memory.linked_person_id == linked_person_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Sorting
        sort_attr = getattr(Memory, sort_by, Memory.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def update_memory(
        db: AsyncSession, user_id: UUID, memory_id: UUID, schema: MemoryUpdate
    ) -> Memory:
        db_memory = await MemoriesRepository.get_memory(db, user_id, memory_id)

        # Validate linked person if updated
        if schema.linked_person_id:
            p_query = select(Person).where(
                and_(Person.id == schema.linked_person_id, Person.user_id == user_id)
            )
            p_result = await db.execute(p_query)
            if not p_result.scalar_one_or_none():
                raise NotFoundError(f"Linked contact with ID {schema.linked_person_id} not found.")

        update_data = schema.dict(exclude_unset=True)
        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")
        for key, value in update_data.items():
            setattr(db_memory, key, value)

        db_memory.updated_at = datetime.utcnow()
        # Modifying content trigger background re-embedding logic (mocked/notified via meta or state)
        if "content" in update_data:
            if not db_memory.meta:
                db_memory.meta = {}
            db_memory.meta["needs_embedding_reindex"] = True

        await db.commit()
        await db.refresh(db_memory)
        return db_memory

    @staticmethod
    async def soft_delete_memory(db: AsyncSession, user_id: UUID, memory_id: UUID) -> Memory:
        db_memory = await MemoriesRepository.get_memory(db, user_id, memory_id)
        db_memory.deleted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_memory)
        return db_memory
