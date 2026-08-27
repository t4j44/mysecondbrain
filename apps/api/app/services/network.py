from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import PaginatedResult, PaginationParams
from app.models.entities import (
    Commitment,
    Interaction,
    Meeting,
    Organization,
    Person,
    PersonOrganizationRole,
)
from app.repositories.network import (
    COMMITMENT_STATUS_OPEN,
    DIRECTION_OWED_BY_ME,
    DIRECTION_OWED_TO_ME,
    CommitmentRepository,
    InteractionRepository,
    MeetingRepository,
    NetworkIntelligenceRepository,
    OrganizationRepository,
    PersonOrganizationRoleRepository,
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
    ) -> PaginatedResult[Person]:
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
    ) -> PaginatedResult[Organization]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)

    async def get_organization(self, id: str) -> Organization:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Organization record not found.")
        return res

    async def update_organization(self, id: str, data: Dict[str, Any]) -> Organization:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Organization record not found.")
        await self.db.commit()
        return res

    async def delete_organization(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Organization record not found.")
        await self.db.commit()
        return res


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
        self, pagination: PaginationParams, person_id: Any = None, venture_id: Any = None
    ) -> PaginatedResult[Interaction]:
        filters: Dict[str, Any] = {}
        if person_id:
            filters["person_id"] = person_id
        if venture_id:
            filters["venture_id"] = venture_id
        return await self.repo.list(self.db, self.user_id, pagination=pagination, **filters)

    async def get_interaction(self, id: str) -> Interaction:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Interaction record not found.")
        return res

    async def update_interaction(self, id: str, data: Dict[str, Any]) -> Interaction:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Interaction record not found.")
        await self.db.commit()
        return res

    async def delete_interaction(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Interaction record not found.")
        await self.db.commit()
        return res


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

    async def list_meetings(self, pagination: PaginationParams) -> PaginatedResult[Meeting]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)

    async def get_meeting(self, id: str) -> Meeting:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Meeting record not found.")
        return res

    async def update_meeting(self, id: str, data: Dict[str, Any]) -> Meeting:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Meeting record not found.")
        await self.db.commit()
        return res

    async def delete_meeting(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Meeting record not found.")
        await self.db.commit()
        return res


class PersonOrganizationRoleService:
    """Multi-organization affiliation. Supersedes the single-valued people.organization_id."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = PersonOrganizationRoleRepository()
        self.people = PersonRepository()
        self.organizations = OrganizationRepository()

    async def create_role(self, data: Dict[str, Any]) -> PersonOrganizationRole:
        # SQLite has no ownership trigger, so the same rule migration 0022 enforces in
        # PostgreSQL is enforced here: both endpoints of the affiliation must be ours.
        if not await self.people.get_by_id(self.db, self.user_id, data["person_id"]):
            raise NotFoundError("Contact record not found.")
        if not await self.organizations.get_by_id(self.db, self.user_id, data["organization_id"]):
            raise NotFoundError("Organization record not found.")

        res = await self.repo.create(self.db, obj_in_data={"user_id": self.user_id, **data})
        await self.db.commit()
        return res

    async def list_roles_for_person(
        self, person_id: str, include_ended: bool = True
    ) -> List[PersonOrganizationRole]:
        if not await self.people.get_by_id(self.db, self.user_id, person_id):
            raise NotFoundError("Contact record not found.")
        return await self.repo.list_for_person(
            self.db, self.user_id, person_id, include_ended=include_ended
        )

    async def update_role(self, id: str, data: Dict[str, Any]) -> PersonOrganizationRole:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Organization role record not found.")
        await self.db.commit()
        return res

    async def end_role(self, id: str, ended_at: Optional[datetime] = None) -> PersonOrganizationRole:
        """Close an affiliation without deleting it — relationship history is the product."""
        return await self.update_role(id, {"ended_at": ended_at or _utc_now()})

    async def delete_role(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Organization role record not found.")
        await self.db.commit()
        return res


class CommitmentService:
    """First-class commitments. Supersedes the free-text interactions.commitments array."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = CommitmentRepository()
        self.intelligence = NetworkIntelligenceRepository()

    async def create_commitment(self, data: Dict[str, Any]) -> Commitment:
        res = await self.repo.create(self.db, obj_in_data={"user_id": self.user_id, **data})
        await self.db.commit()
        return res

    async def get_commitment(self, id: str) -> Commitment:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Commitment record not found.")
        return res

    async def update_commitment(self, id: str, data: Dict[str, Any]) -> Commitment:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Commitment record not found.")
        await self.db.commit()
        return res

    async def complete_commitment(self, id: str, completed_at: Optional[datetime] = None) -> Commitment:
        return await self.update_commitment(
            id, {"status": "completed", "completed_at": completed_at or _utc_now()}
        )

    async def delete_commitment(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Commitment record not found.")
        await self.db.commit()
        return res

    async def list_commitments(
        self,
        *,
        person_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        venture_id: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        overdue_only: bool = False,
        limit: int = 100,
    ) -> List[Commitment]:
        return await self.intelligence.list_commitments(
            self.db,
            self.user_id,
            now=_utc_now(),
            person_id=person_id,
            organization_id=organization_id,
            venture_id=venture_id,
            direction=direction,
            status=status,
            overdue_only=overdue_only,
            limit=limit,
        )


class NetworkIntelligenceService:
    """
    Answers relationship questions from stored facts only.

    Every number returned here is a count, a timestamp or a stored field. No inferred
    relationship strength or AI score is produced.
    """

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = NetworkIntelligenceRepository()
        self.organizations = OrganizationRepository()
        self.people = PersonRepository()

    async def network_overview(self, industry: Optional[str] = None) -> Dict[str, Any]:
        """"How many startups are in my network?" — filtered by the recorded industry."""
        connected = await self.repo.connected_organizations(self.db, self.user_id, industry)
        by_industry: Dict[str, int] = {}
        for organization, _ in connected:
            key = (organization.industry or "unspecified").lower()
            by_industry[key] = by_industry.get(key, 0) + 1
        return {
            "industry_filter": industry,
            "organizations_count": len(connected),
            "connected_people_count": sum(count for _, count in connected),
            "organizations_by_industry": dict(sorted(by_industry.items())),
            "organizations": [
                {
                    "organization_id": str(organization.id),
                    "name": organization.name,
                    "industry": organization.industry,
                    "connected_people_count": count,
                }
                for organization, count in connected
            ],
        }

    async def organization_summary(self, organization_id: str) -> Dict[str, Any]:
        organization = await self.organizations.get_by_id(self.db, self.user_id, organization_id)
        if not organization:
            raise NotFoundError("Organization record not found.")
        summary = await self.repo.organization_summary(
            self.db, self.user_id, organization_id, _utc_now()
        )
        summary["name"] = organization.name
        summary["industry"] = organization.industry
        return summary

    async def organization_people(
        self, organization_id: str, include_ended: bool = True
    ) -> List[Dict[str, Any]]:
        """Who do I know at organization X, in what role, and when did we last speak."""
        organization = await self.organizations.get_by_id(self.db, self.user_id, organization_id)
        if not organization:
            raise NotFoundError("Organization record not found.")

        rows = await self.repo.people_at_organization(
            self.db, self.user_id, organization_id, include_ended=include_ended
        )
        return [await self._person_relationship(person, role) for person, role in rows]

    async def person_relationship(self, person_id: str) -> Dict[str, Any]:
        """The full picture for one contact: affiliations, last contact, and both ledgers."""
        person = await self.people.get_by_id(self.db, self.user_id, person_id)
        if not person:
            raise NotFoundError("Contact record not found.")

        roles = await PersonOrganizationRoleRepository().list_for_person(
            self.db, self.user_id, person_id
        )
        now = _utc_now()
        owed_to_me = await self.repo.list_commitments(
            self.db,
            self.user_id,
            now=now,
            person_id=person_id,
            direction=DIRECTION_OWED_TO_ME,
            status=COMMITMENT_STATUS_OPEN,
        )
        owed_by_me = await self.repo.list_commitments(
            self.db,
            self.user_id,
            now=now,
            person_id=person_id,
            direction=DIRECTION_OWED_BY_ME,
            status=COMMITMENT_STATUS_OPEN,
        )
        overdue = await self.repo.list_commitments(
            self.db, self.user_id, now=now, person_id=person_id, overdue_only=True
        )

        detail = await self._person_relationship(person, None)
        detail["roles"] = [
            {
                "id": str(role.id),
                "organization_id": str(role.organization_id),
                "role": role.role,
                "relationship_type": role.relationship_type,
                "is_primary": bool(role.is_primary),
                "started_at": role.started_at,
                "ended_at": role.ended_at,
                "is_current": role.ended_at is None,
            }
            for role in roles
        ]
        detail["they_promised_me"] = [_commitment_brief(c) for c in owed_to_me]
        detail["i_owe_them"] = [_commitment_brief(c) for c in owed_by_me]
        detail["overdue_commitments"] = [_commitment_brief(c) for c in overdue]
        return detail

    async def stale_contacts(
        self,
        *,
        days: int = 30,
        role_contains: Optional[str] = None,
        founders_only: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        cutoff = _utc_now() - timedelta(days=days)
        rows = await self.repo.stale_contacts(
            self.db,
            self.user_id,
            cutoff=cutoff,
            role_contains=role_contains,
            founders_only=founders_only,
            limit=limit,
        )
        return [
            {
                "person_id": str(person.id),
                "name": person.name,
                "role": person.role,
                "relationship_type": person.relationship_type,
                "last_interaction_at": last_at,
                "days_since_last_interaction": (
                    None if last_at is None else (_utc_now() - _as_utc(last_at)).days
                ),
            }
            for person, last_at in rows
        ]

    async def venture_network(self, venture_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        rows = await self.repo.people_relevant_to_venture(
            self.db, self.user_id, venture_id, limit=limit
        )
        return [
            {
                "person_id": str(person.id),
                "name": person.name,
                "role": person.role,
                "interaction_count": interaction_count,
                "commitment_count": commitment_count,
            }
            for person, interaction_count, commitment_count in rows
        ]

    async def _person_relationship(
        self, person: Person, role: Optional[PersonOrganizationRole]
    ) -> Dict[str, Any]:
        last = await self.repo.last_interaction_for_person(self.db, self.user_id, str(person.id))
        detail: Dict[str, Any] = {
            "person_id": str(person.id),
            "name": person.name,
            "person_role": person.role,
            "relationship_type": person.relationship_type,
            "last_interaction_at": last.date if last else None,
            "last_interaction_title": last.title if last else None,
            "last_interaction_summary": last.summary if last else None,
        }
        if role is not None:
            detail.update(
                {
                    "role_id": str(role.id),
                    "role": role.role,
                    "organization_relationship_type": role.relationship_type,
                    "is_primary": bool(role.is_primary),
                    "started_at": role.started_at,
                    "ended_at": role.ended_at,
                    "is_current": role.ended_at is None,
                }
            )
        return detail


def _commitment_brief(commitment: Commitment) -> Dict[str, Any]:
    return {
        "id": str(commitment.id),
        "direction": commitment.direction,
        "description": commitment.description,
        "status": commitment.status,
        "due_at": commitment.due_at,
        "completed_at": commitment.completed_at,
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; PostgreSQL returns aware ones."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
