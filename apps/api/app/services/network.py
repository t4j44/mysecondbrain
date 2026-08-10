from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.models.entities import Interaction, Meeting, Organization, Person
from app.repositories.network import (
    InteractionRepository,
    MeetingRepository,
    OrganizationRepository,
    PersonRepository,
)


class PersonService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = PersonRepository()

    async def create_person(self, data: Dict[str, Any]) -> Person:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_people(
        self, pagination: PaginationParams, **filters
    ) -> PaginatedResponse[Person]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination, **filters)

    async def get_person(self, id: str) -> Person:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Contact record not found.")
        return res

    async def update_person(self, id: str, data: Dict[str, Any]) -> Person:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Contact record not found.")
        await self.db.commit()
        return res

    async def delete_person(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Contact record not found.")
        await self.db.commit()
        return res


class OrganizationService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = OrganizationRepository()

    async def create_organization(self, data: Dict[str, Any]) -> Organization:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_organizations(
        self, pagination: PaginationParams
    ) -> PaginatedResponse[Organization]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)


class InteractionService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = InteractionRepository()

    async def create_interaction(self, data: Dict[str, Any]) -> Interaction:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_interactions(
        self, pagination: PaginationParams
    ) -> PaginatedResponse[Interaction]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)


class MeetingService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = MeetingRepository()

    async def create_meeting(self, data: Dict[str, Any]) -> Meeting:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_meetings(self, pagination: PaginationParams) -> PaginatedResponse[Meeting]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)
