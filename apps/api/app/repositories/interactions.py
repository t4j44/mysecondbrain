from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import NotFoundError
from app.jobs.index_queue import delete_index, queue_index
from app.models.entities import Interaction
from app.schemas.interactions import InteractionCreate, InteractionUpdate


class InteractionsRepository:
    @staticmethod
    async def create_interaction(
        db: AsyncSession, user_id: UUID, schema: InteractionCreate
    ) -> Interaction:
        db_interaction = Interaction(
            user_id=user_id,
            person_id=schema.person_id,
            venture_id=schema.venture_id,
            interaction_type=schema.interaction_type,
            title=schema.title,
            summary=schema.summary,
            date=schema.date,
            key_takeaways=schema.key_takeaways,
            next_actions=schema.next_actions,
            markdown_path=schema.markdown_path,
            meta=schema.metadata,
        )
        db.add(db_interaction)
        await db.flush()
        if db_interaction.deleted_at or db_interaction.archived_at:
            await delete_index(db, db_interaction)
        else:
            queue_index(db, db_interaction)
        await db.commit()
        await db.refresh(db_interaction)
        return db_interaction

    @staticmethod
    async def get_interaction(db: AsyncSession, user_id: UUID, interaction_id: UUID) -> Interaction:
        query = select(Interaction).where(
            and_(
                Interaction.id == interaction_id,
                Interaction.user_id == user_id,
                Interaction.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        db_interaction = result.scalar_one_or_none()
        if not db_interaction:
            raise NotFoundError("Interaction record not found or access denied.")
        return db_interaction

    @staticmethod
    async def list_interactions(
        db: AsyncSession,
        user_id: UUID,
        person_id: Optional[UUID] = None,
        venture_id: Optional[UUID] = None,
        interaction_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> Tuple[List[Interaction], int]:
        query = select(Interaction).where(
            and_(Interaction.user_id == user_id, Interaction.deleted_at.is_(None))
        )

        if person_id:
            query = query.where(Interaction.person_id == person_id)
        if venture_id:
            query = query.where(Interaction.venture_id == venture_id)
        if interaction_type:
            query = query.where(Interaction.interaction_type == interaction_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Sorting
        sort_attr = getattr(Interaction, sort_by, Interaction.date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def update_interaction(
        db: AsyncSession, user_id: UUID, interaction_id: UUID, schema: InteractionUpdate
    ) -> Interaction:
        db_interaction = await InteractionsRepository.get_interaction(db, user_id, interaction_id)

        update_data = schema.dict(exclude_unset=True)
        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")
        for key, value in update_data.items():
            setattr(db_interaction, key, value)

        db_interaction.updated_at = datetime.utcnow()
        await db.flush()
        if db_interaction.deleted_at or db_interaction.archived_at:
            await delete_index(db, db_interaction)
        else:
            queue_index(db, db_interaction)
        await db.commit()
        await db.refresh(db_interaction)
        return db_interaction

    @staticmethod
    async def soft_delete_interaction(
        db: AsyncSession, user_id: UUID, interaction_id: UUID
    ) -> Interaction:
        db_interaction = await InteractionsRepository.get_interaction(db, user_id, interaction_id)
        db_interaction.deleted_at = datetime.utcnow()
        await db.flush()
        if db_interaction.deleted_at or db_interaction.archived_at:
            await delete_index(db, db_interaction)
        else:
            queue_index(db, db_interaction)
        await db.commit()
        await db.refresh(db_interaction)
        return db_interaction
