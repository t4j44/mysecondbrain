import pytest
from sqlalchemy import select

from app.ai.retrieval import perform_keyword_search
from app.models.entities import Interaction, Memory, Organization, Person, PersonOrganizationRole
from app.services.network import PersonService
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_person_delete_removes_linked_search_context(test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        person = Person(user_id=test_user_id, name='Ahmed Synthetic')
        db.add(person)
        await db.flush()
        db.add_all([Interaction(user_id=test_user_id, person_id=person.id, title='Ahmed promise', summary='Ahmed deck'),
            Memory(user_id=test_user_id, linked_person_id=person.id, title='Ahmed note', content='Ahmed deck'),
            Memory(user_id=other_user_id, title='Ahmed foreign', content='Ahmed')])
        await db.commit()
        await PersonService(db, test_user_id).delete_person(str(person.id))
        assert await perform_keyword_search(db, test_user_id, 'Ahmed') == []
        assert len(await perform_keyword_search(db, other_user_id, 'Ahmed')) == 1


@pytest.mark.asyncio
async def test_company_correction_updates_current_role_and_canonical_person(test_user_id):
    async with TestingSessionLocal() as db:
        old = Organization(user_id=test_user_id, name='Company A')
        db.add(old)
        await db.flush()
        person = Person(user_id=test_user_id, name='Ahmed', company=old.name, organization_id=old.id)
        db.add(person)
        await db.flush()
        db.add(PersonOrganizationRole(user_id=test_user_id, person_id=person.id, organization_id=old.id, role='Founder'))
        await db.commit()
        await PersonService(db, test_user_id).update_person(str(person.id), {'company': 'Company B'})
        active = (await db.execute(select(PersonOrganizationRole).where(PersonOrganizationRole.person_id == person.id,
            PersonOrganizationRole.ended_at.is_(None)))).scalars().all()
        assert len(active) == 1 and str(active[0].organization_id) == str(person.organization_id)
        assert person.company == 'Company B' and person.organization_id != old.id
