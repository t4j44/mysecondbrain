from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self):
        super().__init__(Profile)

    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Optional[Profile]:
        stmt = select(Profile).where(Profile.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self, db: AsyncSession, user_id: str, email: str, **kwargs
    ) -> Profile:
        existing = await self.get_by_user_id(db, user_id)
        if existing:
            for k, v in kwargs.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await db.flush()
            await db.refresh(existing)
            return existing
        else:
            new_profile = Profile(id=user_id, email=email, **kwargs)
            db.add(new_profile)
            await db.flush()
            await db.refresh(new_profile)
            return new_profile
