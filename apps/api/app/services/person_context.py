"""Invalidate linked private context when a contact is removed or corrected."""
from datetime import datetime, timezone

from sqlalchemy import delete, or_, select, update

from app.core.errors import NotFoundError
from app.jobs.index_queue import delete_index, queue_index
from app.models.entities import (
    Commitment,
    ContentItem,
    EntityEdge,
    Interaction,
    Memory,
    Organization,
    PersonOrganizationRole,
    RelationshipAction,
    Task,
)
from app.models.publication import PortfolioPublication


def references_identity(value, identity):
    if isinstance(value, dict):
        return any(references_identity(item, identity) for item in value.values())
    if isinstance(value, list):
        return any(references_identity(item, identity) for item in value)
    return str(value) == identity


async def invalidate_drafts(db, owner, person_id):
    drafts = (await db.execute(select(ContentItem).where(ContentItem.user_id == owner,
        ContentItem.deleted_at.is_(None)))).scalars().all()
    for draft in drafts:
        # Source manifests are trusted server-created structures, never substring body matching.
        if references_identity(draft.source_records or [], person_id):
            draft.archived_at = datetime.now(timezone.utc)
            await db.execute(update(PortfolioPublication).where(PortfolioPublication.user_id == owner,
                PortfolioPublication.draft_id == draft.id).values(revoked_at=datetime.now(timezone.utc)))


async def delete_person_context(db, person):
    owner, identity = str(person.user_id), str(person.id)
    now = datetime.now(timezone.utc)
    linked = []
    for model, columns in ((Interaction, [Interaction.person_id]),
                           (Commitment, [Commitment.from_person_id, Commitment.to_person_id]),
                           (Task, [Task.person_id])):
        linked += (await db.execute(select(model).where(model.user_id == owner,
            or_(*(col == identity for col in columns))))).scalars().all()
    # Array representations differ on SQLite and PostgreSQL; owner-scope first.
    memories = (await db.execute(select(Memory).where(Memory.user_id == owner))).scalars().all()
    linked += [row for row in memories if str(row.linked_person_id) == identity or identity in
               [str(value) for value in (row.related_people or [])]]
    for row in linked:
        row.deleted_at = now
        await delete_index(db, row)
        await invalidate_drafts(db, owner, str(row.id))
    await db.execute(delete(PersonOrganizationRole).where(PersonOrganizationRole.user_id == owner,
        PersonOrganizationRole.person_id == identity))
    await db.execute(delete(RelationshipAction).where(RelationshipAction.user_id == owner,
        RelationshipAction.person_id == identity))
    await invalidate_drafts(db, owner, identity)
    person.metadata_payload = {}
    # BaseRepository subsequently removes the person's own vectors and graph edges.


async def correct_person_context(db, person, changes):
    owner, identity = str(person.user_id), str(person.id)
    if not {'organization_id', 'company', 'role'}.intersection(changes):
        return
    organization = None
    if person.organization_id:
        organization = (await db.execute(select(Organization).where(Organization.id == person.organization_id,
            Organization.user_id == owner, Organization.deleted_at.is_(None)))).scalar_one_or_none()
        if organization is None:
            raise NotFoundError('Choose an organization from your own workspace.')
    if 'organization_id' not in changes and ('company' in changes or (person.company and not person.organization_id)):
        organization = (await db.execute(select(Organization).where(Organization.user_id == owner,
            Organization.name == person.company, Organization.deleted_at.is_(None)))).scalars().first() if person.company else None
        if person.company and organization is None:
            organization = Organization(user_id=owner, name=person.company)
            db.add(organization)
            await db.flush()
        person.organization_id = organization.id if organization else None
    person.company = organization.name if organization else None
    roles = (await db.execute(select(PersonOrganizationRole).where(PersonOrganizationRole.user_id == owner,
        PersonOrganizationRole.person_id == identity, PersonOrganizationRole.ended_at.is_(None)))).scalars().all()
    for role in roles:
        role.ended_at = datetime.now(timezone.utc)
        role.is_primary = False
    if organization:
        db.add(PersonOrganizationRole(user_id=owner, person_id=identity, organization_id=organization.id,
            role=person.role, is_primary=True, relationship_type='employee'))
        queue_index(db, organization)
    await db.execute(delete(EntityEdge).where(EntityEdge.user_id == owner,
        EntityEdge.relationship_type == 'current_affiliation',
        EntityEdge.source_entity_type == 'person', EntityEdge.source_entity_id == identity))
    if organization:
        db.add(EntityEdge(user_id=owner, source_entity_type='person', source_entity_id=identity,
            target_entity_type='organization', target_entity_id=organization.id,
            relationship_type='current_affiliation'))
    person.metadata_payload = {k: v for k, v in (person.metadata_payload or {}).items()
                               if k not in {'ai_summary', 'relationship_summary', 'summary'}}
    await invalidate_drafts(db, owner, identity)
