from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import Select, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Commitment,
    Interaction,
    Meeting,
    Organization,
    Person,
    PersonOrganizationRole,
)
from app.repositories.base import BaseRepository

# Commitment direction vocabulary (mirrors the CHECK constraint in migration 0022).
DIRECTION_OWED_TO_ME = "owed_to_me"  # they promised me
DIRECTION_OWED_BY_ME = "owed_by_me"  # I owe them
DIRECTION_UNSPECIFIED = "unspecified"  # legacy import; direction was never recorded

COMMITMENT_STATUS_OPEN = "open"

# Substring used to identify founder-type affiliations. Deliberately a literal match on the
# recorded role text, not an inferred score.
# "founder" also matches "co-founder", "cofounder" and "founding engineer" is excluded on purpose.
FOUNDER_ROLE_MARKERS: Tuple[str, ...] = ("founder",)


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


class PersonOrganizationRoleRepository(BaseRepository[PersonOrganizationRole]):
    def __init__(self):
        super().__init__(PersonOrganizationRole)

    async def list_for_person(
        self, db: AsyncSession, user_id: str, person_id: str, include_ended: bool = True
    ) -> List[PersonOrganizationRole]:
        stmt = _live_roles(user_id).where(PersonOrganizationRole.person_id == person_id)
        if not include_ended:
            stmt = stmt.where(PersonOrganizationRole.ended_at.is_(None))
        stmt = stmt.order_by(
            desc(PersonOrganizationRole.is_primary), desc(PersonOrganizationRole.created_at)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class CommitmentRepository(BaseRepository[Commitment]):
    def __init__(self):
        super().__init__(Commitment)


def _live_roles(user_id: str) -> Select:
    return select(PersonOrganizationRole).where(
        PersonOrganizationRole.user_id == user_id,
        PersonOrganizationRole.deleted_at.is_(None),
    )


def _role_is_founder(column: Any) -> Any:
    """Literal role-text match. No inferred or scored relationship signal is used anywhere."""
    return or_(*[func.lower(column).like(f"%{marker}%") for marker in FOUNDER_ROLE_MARKERS])


class NetworkIntelligenceRepository:
    """
    Read-side of the relationship graph.

    Every query is owner-scoped in SQL as well as by RLS, and every returned number is a direct
    count or timestamp from the stored rows — there are no derived relationship scores here.
    """

    async def organization_person_ids(
        self, db: AsyncSession, user_id: str, organization_id: str, current_only: bool = False
    ) -> List[str]:
        stmt = select(PersonOrganizationRole.person_id).where(
            PersonOrganizationRole.user_id == user_id,
            PersonOrganizationRole.deleted_at.is_(None),
            PersonOrganizationRole.organization_id == organization_id,
        )
        if current_only:
            stmt = stmt.where(PersonOrganizationRole.ended_at.is_(None))
        result = await db.execute(stmt.distinct())
        return [row[0] for row in result.fetchall()]

    async def people_at_organization(
        self, db: AsyncSession, user_id: str, organization_id: str, include_ended: bool = True
    ) -> List[Tuple[Person, PersonOrganizationRole]]:
        """Who do I know at organization X, and in what role."""
        stmt = (
            select(Person, PersonOrganizationRole)
            .join(PersonOrganizationRole, PersonOrganizationRole.person_id == Person.id)
            .where(
                Person.user_id == user_id,
                Person.deleted_at.is_(None),
                PersonOrganizationRole.user_id == user_id,
                PersonOrganizationRole.deleted_at.is_(None),
                PersonOrganizationRole.organization_id == organization_id,
            )
        )
        if not include_ended:
            stmt = stmt.where(PersonOrganizationRole.ended_at.is_(None))
        stmt = stmt.order_by(desc(PersonOrganizationRole.is_primary), Person.name)
        result = await db.execute(stmt)
        return [(row[0], row[1]) for row in result.fetchall()]

    async def last_interaction_for_person(
        self, db: AsyncSession, user_id: str, person_id: str
    ) -> Optional[Interaction]:
        """When did I last speak to them, and what was discussed."""
        stmt = (
            select(Interaction)
            .where(
                Interaction.user_id == user_id,
                Interaction.deleted_at.is_(None),
                Interaction.person_id == person_id,
            )
            .order_by(desc(Interaction.date))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def connected_organizations(
        self, db: AsyncSession, user_id: str, industry: Optional[str] = None
    ) -> List[Tuple[Organization, int]]:
        """
        Organizations in the network, with the number of people connected to each.

        "How many startups are in my network?" is answered by filtering on the recorded
        `industry` — the schema stores no company-stage field, so none is invented.
        """
        stmt = (
            select(Organization, func.count(func.distinct(PersonOrganizationRole.person_id)))
            .join(
                PersonOrganizationRole,
                PersonOrganizationRole.organization_id == Organization.id,
            )
            .where(
                Organization.user_id == user_id,
                Organization.deleted_at.is_(None),
                PersonOrganizationRole.user_id == user_id,
                PersonOrganizationRole.deleted_at.is_(None),
            )
        )
        if industry:
            stmt = stmt.where(func.lower(Organization.industry) == industry.lower())
        stmt = stmt.group_by(Organization.id).order_by(Organization.name)
        result = await db.execute(stmt)
        return [(row[0], int(row[1] or 0)) for row in result.fetchall()]

    async def organization_summary(
        self, db: AsyncSession, user_id: str, organization_id: str, now: datetime
    ) -> Dict[str, Any]:
        """Structured, directly-counted metrics for one organization."""
        person_ids = await self.organization_person_ids(db, user_id, organization_id)

        founders_stmt = select(
            func.count(func.distinct(PersonOrganizationRole.person_id))
        ).where(
            PersonOrganizationRole.user_id == user_id,
            PersonOrganizationRole.deleted_at.is_(None),
            PersonOrganizationRole.organization_id == organization_id,
            _role_is_founder(PersonOrganizationRole.role),
        )
        founders_known = int((await db.execute(founders_stmt)).scalar() or 0)

        last_interaction_at: Optional[datetime] = None
        if person_ids:
            last_stmt = select(func.max(Interaction.date)).where(
                Interaction.user_id == user_id,
                Interaction.deleted_at.is_(None),
                Interaction.person_id.in_(person_ids),
            )
            last_interaction_at = (await db.execute(last_stmt)).scalar()

        open_stmt = select(func.count()).select_from(Commitment).where(
            *_organization_commitment_filters(user_id, organization_id, person_ids),
            Commitment.status == COMMITMENT_STATUS_OPEN,
        )
        open_commitments = int((await db.execute(open_stmt)).scalar() or 0)

        overdue_stmt = select(func.count()).select_from(Commitment).where(
            *_organization_commitment_filters(user_id, organization_id, person_ids),
            Commitment.status == COMMITMENT_STATUS_OPEN,
            Commitment.due_at.is_not(None),
            Commitment.due_at < now,
        )
        overdue_commitments = int((await db.execute(overdue_stmt)).scalar() or 0)

        return {
            "organization_id": str(organization_id),
            "connected_people_count": len(person_ids),
            "founders_known": founders_known,
            "last_interaction_at": last_interaction_at,
            "open_commitments": open_commitments,
            "overdue_commitments": overdue_commitments,
        }

    async def list_commitments(
        self,
        db: AsyncSession,
        user_id: str,
        *,
        now: datetime,
        person_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        venture_id: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        overdue_only: bool = False,
        limit: int = 100,
    ) -> List[Commitment]:
        """
        The commitment ledger. `direction` answers "what did they promise me"
        (`owed_to_me`) and "what do I owe them" (`owed_by_me`).
        """
        stmt = select(Commitment).where(
            Commitment.user_id == user_id, Commitment.deleted_at.is_(None)
        )
        if person_id:
            stmt = stmt.where(
                or_(
                    Commitment.from_person_id == person_id,
                    Commitment.to_person_id == person_id,
                    Commitment.interaction_id.in_(
                        select(Interaction.id).where(
                            Interaction.user_id == user_id,
                            Interaction.person_id == person_id,
                        )
                    ),
                )
            )
        if organization_id:
            stmt = stmt.where(Commitment.organization_id == organization_id)
        if venture_id:
            stmt = stmt.where(Commitment.venture_id == venture_id)
        if direction:
            stmt = stmt.where(Commitment.direction == direction)
        if status:
            stmt = stmt.where(Commitment.status == status)
        if overdue_only:
            stmt = stmt.where(
                Commitment.status == COMMITMENT_STATUS_OPEN,
                Commitment.due_at.is_not(None),
                Commitment.due_at < now,
            )
        stmt = stmt.order_by(Commitment.due_at.is_(None), Commitment.due_at, Commitment.created_at)
        result = await db.execute(stmt.limit(limit))
        return list(result.scalars().all())

    async def stale_contacts(
        self,
        db: AsyncSession,
        user_id: str,
        *,
        cutoff: datetime,
        role_contains: Optional[str] = None,
        founders_only: bool = False,
        limit: int = 100,
    ) -> List[Tuple[Person, Optional[datetime]]]:
        """
        "Which founders haven't I spoken to in 30 days?"

        A contact with no interaction at all is stale by definition and is included, with a
        null last-interaction timestamp rather than a fabricated one.
        """
        last_seen = (
            select(
                Interaction.person_id.label("person_id"),
                func.max(Interaction.date).label("last_at"),
            )
            .where(Interaction.user_id == user_id, Interaction.deleted_at.is_(None))
            .group_by(Interaction.person_id)
            .subquery()
        )

        stmt = (
            select(Person, last_seen.c.last_at)
            .outerjoin(last_seen, last_seen.c.person_id == Person.id)
            .where(Person.user_id == user_id, Person.deleted_at.is_(None))
            .where(or_(last_seen.c.last_at.is_(None), last_seen.c.last_at < cutoff))
        )

        role_predicates = []
        if founders_only:
            role_predicates.append(_role_is_founder(Person.role))
            role_predicates.append(
                Person.id.in_(
                    select(PersonOrganizationRole.person_id).where(
                        PersonOrganizationRole.user_id == user_id,
                        PersonOrganizationRole.deleted_at.is_(None),
                        _role_is_founder(PersonOrganizationRole.role),
                    )
                )
            )
        elif role_contains:
            needle = f"%{role_contains.lower()}%"
            role_predicates.append(func.lower(Person.role).like(needle))
            role_predicates.append(
                Person.id.in_(
                    select(PersonOrganizationRole.person_id).where(
                        PersonOrganizationRole.user_id == user_id,
                        PersonOrganizationRole.deleted_at.is_(None),
                        func.lower(PersonOrganizationRole.role).like(needle),
                    )
                )
            )
        if role_predicates:
            stmt = stmt.where(or_(*role_predicates))

        stmt = stmt.order_by(last_seen.c.last_at.is_not(None), last_seen.c.last_at, Person.name)
        result = await db.execute(stmt.limit(limit))
        return [(row[0], row[1]) for row in result.fetchall()]

    async def people_relevant_to_venture(
        self, db: AsyncSession, user_id: str, venture_id: str, limit: int = 100
    ) -> List[Tuple[Person, int, int]]:
        """
        "Who is relevant to Venture X?" — relevance is *evidence*, not a score: the count of
        interactions logged against the venture plus the count of commitments tied to it.
        """
        interaction_counts = (
            select(
                Interaction.person_id.label("person_id"),
                func.count().label("interaction_count"),
            )
            .where(
                Interaction.user_id == user_id,
                Interaction.deleted_at.is_(None),
                Interaction.venture_id == venture_id,
                Interaction.person_id.is_not(None),
            )
            .group_by(Interaction.person_id)
            .subquery()
        )

        commitment_people = (
            select(Commitment.from_person_id.label("person_id"))
            .where(
                Commitment.user_id == user_id,
                Commitment.deleted_at.is_(None),
                Commitment.venture_id == venture_id,
                Commitment.from_person_id.is_not(None),
            )
            .union_all(
                select(Commitment.to_person_id.label("person_id")).where(
                    Commitment.user_id == user_id,
                    Commitment.deleted_at.is_(None),
                    Commitment.venture_id == venture_id,
                    Commitment.to_person_id.is_not(None),
                )
            )
            .subquery()
        )
        commitment_counts = (
            select(
                commitment_people.c.person_id.label("person_id"),
                func.count().label("commitment_count"),
            )
            .group_by(commitment_people.c.person_id)
            .subquery()
        )

        stmt = (
            select(
                Person,
                func.coalesce(interaction_counts.c.interaction_count, 0),
                func.coalesce(commitment_counts.c.commitment_count, 0),
            )
            .outerjoin(interaction_counts, interaction_counts.c.person_id == Person.id)
            .outerjoin(commitment_counts, commitment_counts.c.person_id == Person.id)
            .where(Person.user_id == user_id, Person.deleted_at.is_(None))
            .where(
                or_(
                    interaction_counts.c.interaction_count.is_not(None),
                    commitment_counts.c.commitment_count.is_not(None),
                )
            )
            .order_by(
                desc(func.coalesce(interaction_counts.c.interaction_count, 0)),
                desc(func.coalesce(commitment_counts.c.commitment_count, 0)),
                Person.name,
            )
        )
        result = await db.execute(stmt.limit(limit))
        return [(row[0], int(row[1] or 0), int(row[2] or 0)) for row in result.fetchall()]


def _organization_commitment_filters(
    user_id: str, organization_id: str, person_ids: Sequence[str]
) -> List[Any]:
    """A commitment counts against an organization directly, or through one of its people."""
    reach: List[Any] = [Commitment.organization_id == organization_id]
    if person_ids:
        reach.append(Commitment.from_person_id.in_(person_ids))
        reach.append(Commitment.to_person_id.in_(person_ids))
    return [
        Commitment.user_id == user_id,
        Commitment.deleted_at.is_(None),
        or_(*reach),
    ]
