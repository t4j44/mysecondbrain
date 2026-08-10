from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Interaction, Meeting, Organization, Person
from app.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    def __init__(self):
        super().__init__(Person)

    async def get_follow_ups(self, db: AsyncSession, user_id: str, now: datetime) -> List[Person]:
        stmt = select(Person).where(
            Person.user_id == user_id, Person.deleted_at.is_(None), Person.follow_up_date <= now
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self):
        super().__init__(Organization)


class InteractionRepository(BaseRepository[Interaction]):
    def __init__(self):
        super().__init__(Interaction)

    async def get_by_entity(
        self,
        db: AsyncSession,
        user_id: str,
        person_id: Optional[str] = None,
        venture_id: Optional[str] = None,
    ) -> List[Interaction]:
        stmt = select(Interaction).where(
            Interaction.user_id == user_id, Interaction.deleted_at.is_(None)
        )
        if person_id:
            stmt = stmt.where(Interaction.person_id == person_id)
        if venture_id:
            stmt = stmt.where(Interaction.venture_id == venture_id)
        stmt = stmt.order_by(desc(Interaction.date))
        result = await db.execute(stmt)
        return list(result.scalars().all())


class MeetingRepository(BaseRepository[Meeting]):
    def __init__(self):
        super().__init__(Meeting)

    async def get_by_external_event(
        self, db: AsyncSession, user_id: str, event_id: str
    ) -> Optional[Meeting]:
        stmt = select(Meeting).where(
            Meeting.user_id == user_id, Meeting.external_event_id == event_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
