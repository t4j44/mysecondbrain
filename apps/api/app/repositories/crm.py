from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import String, and_, asc, cast, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import ConflictError, NotFoundError
from app.models.crm import Organization, Person, Relationship
from app.schemas.crm import OrganizationCreate, OrganizationUpdate, PersonCreate, PersonUpdate


class CRMRepository:
    # --- Organization CRUD ---

    @staticmethod
    async def create_organization(
        db: AsyncSession, user_id: UUID, schema: OrganizationCreate
    ) -> Organization:
        # Check for unique name under the same user scope (active)
        query = select(Organization).where(
            and_(
                Organization.user_id == user_id,
                Organization.name == schema.name,
                Organization.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("An organization with this name already exists in your workspace.")

        db_org = Organization(
            user_id=user_id,
            name=schema.name,
            domain=schema.domain,
            industry=schema.industry,
            location=schema.location,
            website_url=schema.website_url,
            description=schema.description,
            meta=schema.metadata,
        )
        db.add(db_org)
        await db.commit()
        await db.refresh(db_org)
        return db_org

    @staticmethod
    async def get_organization(db: AsyncSession, user_id: UUID, org_id: UUID) -> Organization:
        query = select(Organization).where(
            and_(
                Organization.id == org_id,
                Organization.user_id == user_id,
                Organization.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        db_org = result.scalar_one_or_none()
        if not db_org:
            raise NotFoundError("Organization not found or you do not have permission to view it.")
        return db_org

    @staticmethod
    async def list_organizations(
        db: AsyncSession,
        user_id: UUID,
        industry: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> Tuple[List[Organization], int]:
        query = select(Organization).where(
            and_(Organization.user_id == user_id, Organization.deleted_at.is_(None))
        )

        if industry:
            query = query.where(Organization.industry.ilike(f"%{industry}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Sorting
        sort_attr = getattr(Organization, sort_by, Organization.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def update_organization(
        db: AsyncSession, user_id: UUID, org_id: UUID, schema: OrganizationUpdate
    ) -> Organization:
        db_org = await CRMRepository.get_organization(db, user_id, org_id)

        update_data = schema.dict(exclude_unset=True)
        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")
        for key, value in update_data.items():
            setattr(db_org, key, value)

        await db.commit()
        await db.refresh(db_org)
        return db_org

    @staticmethod
    async def soft_delete_organization(
        db: AsyncSession, user_id: UUID, org_id: UUID
    ) -> Organization:
        db_org = await CRMRepository.get_organization(db, user_id, org_id)
        db_org.deleted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_org)
        return db_org

    # --- Person CRUD ---

    @staticmethod
    async def create_person(db: AsyncSession, user_id: UUID, schema: PersonCreate) -> Person:
        # Check if organization_id is valid
        if schema.organization_id:
            await CRMRepository.get_organization(db, user_id, schema.organization_id)

        db_person = Person(
            user_id=user_id,
            organization_id=schema.organization_id,
            name=schema.name,
            role=schema.role,
            company=schema.company,
            industry=schema.industry,
            location=schema.location,
            email=schema.email,
            phone=schema.phone,
            linkedin_url=schema.linkedin_url,
            relationship_type=schema.relationship_type,
            notes=schema.notes,
            tags=schema.tags,
            meta=schema.metadata,
        )
        db.add(db_person)
        await db.commit()
        await db.refresh(db_person)
        return db_person

    @staticmethod
    async def get_person(db: AsyncSession, user_id: UUID, person_id: UUID) -> Person:
        query = select(Person).where(
            and_(Person.id == person_id, Person.user_id == user_id, Person.deleted_at.is_(None))
        )
        result = await db.execute(query)
        db_person = result.scalar_one_or_none()
        if not db_person:
            raise NotFoundError("Person not found or you do not have permission to view it.")
        return db_person

    @staticmethod
    async def list_people(
        db: AsyncSession,
        user_id: UUID,
        q: Optional[str] = None,
        relationship_type: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> Tuple[List[Person], int]:
        query = select(Person).where(and_(Person.user_id == user_id, Person.deleted_at.is_(None)))

        if q:
            query = query.where(
                or_(
                    Person.name.ilike(f"%{q}%"),
                    Person.role.ilike(f"%{q}%"),
                    Person.company.ilike(f"%{q}%"),
                    Person.location.ilike(f"%{q}%"),
                    Person.notes.ilike(f"%{q}%"),
                )
            )

        if relationship_type:
            query = query.where(Person.relationship_type == relationship_type)

        if tag:
            if db.bind and db.bind.dialect.name == "sqlite":
                query = query.where(cast(Person.tags, String).like(f"%{tag}%"))
            else:
                query = query.where(Person.tags.any(tag))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Sorting
        sort_attr = getattr(Person, sort_by, Person.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def update_person(
        db: AsyncSession, user_id: UUID, person_id: UUID, schema: PersonUpdate
    ) -> Person:
        db_person = await CRMRepository.get_person(db, user_id, person_id)

        # Validate organization_id if updated
        if schema.organization_id:
            await CRMRepository.get_organization(db, user_id, schema.organization_id)

        update_data = schema.dict(exclude_unset=True)
        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")
        for key, value in update_data.items():
            setattr(db_person, key, value)

        await db.commit()
        await db.refresh(db_person)
        return db_person

    @staticmethod
    async def soft_delete_person(db: AsyncSession, user_id: UUID, person_id: UUID) -> Person:
        db_person = await CRMRepository.get_person(db, user_id, person_id)
        db_person.deleted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_person)
        return db_person

    # --- Relationship CRUD ---

    @staticmethod
    async def create_relationship(
        db: AsyncSession,
        user_id: UUID,
        source_person_id: UUID,
        target_person_id: UUID,
        relationship_nature: str,
        notes: Optional[str] = None,
    ) -> Relationship:
        # Check owners
        await CRMRepository.get_person(db, user_id, source_person_id)
        await CRMRepository.get_person(db, user_id, target_person_id)

        # Avoid duplicates
        query = select(Relationship).where(
            and_(
                Relationship.user_id == user_id,
                Relationship.source_person_id == source_person_id,
                Relationship.target_person_id == target_person_id,
                Relationship.relationship_nature == relationship_nature,
            )
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ConflictError("This specific relationship configuration already exists.")

        db_rel = Relationship(
            user_id=user_id,
            source_person_id=source_person_id,
            target_person_id=target_person_id,
            relationship_nature=relationship_nature,
            notes=notes,
        )
        db.add(db_rel)
        await db.commit()
        await db.refresh(db_rel)
        return db_rel

    @staticmethod
    async def list_relationships(
        db: AsyncSession, user_id: UUID, person_id: UUID
    ) -> List[Relationship]:
        query = select(Relationship).where(
            and_(
                Relationship.user_id == user_id,
                or_(
                    Relationship.source_person_id == person_id,
                    Relationship.target_person_id == person_id,
                ),
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())
