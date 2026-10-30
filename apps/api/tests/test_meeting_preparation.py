from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.errors import NotFoundError
from app.models.entities import Commitment, Interaction, Meeting, Person
from app.models.meetings import MeetingParticipant
from app.services.meeting_preparation import prepare
from tests.conftest import TestingSessionLocal


async def seed_preparation(db, owner):
    now = datetime.now(timezone.utc)
    meeting = Meeting(user_id=owner, title='Review', start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=1))
    person = Person(user_id=owner, name='Synthetic contact', role='Saved role', company='Saved company', notes='Prefers a short agenda.')
    db.add_all([meeting, person])
    await db.flush()
    db.add(MeetingParticipant(user_id=owner, meeting_id=meeting.id, person_id=person.id))
    interaction = Interaction(user_id=owner, person_id=person.id, title='Last conversation', summary='Review the proposal.', date=now - timedelta(days=2))
    promise = Commitment(user_id=owner, to_person_id=person.id, direction='owed_by_me', description='Send proposal', status='in_progress')
    db.add_all([interaction, promise])
    await db.commit()
    return meeting, person, interaction, promise


async def test_preparation_uses_linked_sources_without_inference(test_user_id):
    async with TestingSessionLocal() as db:
        meeting, person, interaction, promise = await seed_preparation(db, test_user_id)
        result = await prepare(db, test_user_id, meeting.id)
        assert len(result['people']) == 1
        card = result['people'][0]
        assert card['person']['id'] == str(person.id) and card['notes'] == person.notes
        assert card['last_interaction']['source']['uri'] == f'/sources/interaction/{interaction.id}'
        assert card['commitments'][0]['source']['uri'] == f'/sources/commitment/{promise.id}'
        assert card['commitments'][0]['status'] == 'in_progress'
        assert 'not verified' in result['basis']
        empty = Meeting(user_id=test_user_id, title='AI name is not a participant', start_time=meeting.start_time,
            end_time=meeting.end_time, summary=person.name, meta={'people_mentions': [person.name]})
        db.add(empty)
        await db.commit()
        assert (await prepare(db, test_user_id, empty.id))['people'] == []


async def test_preparation_reloads_corrections_and_excludes_deleted_closed_future_context(test_user_id):
    async with TestingSessionLocal() as db:
        meeting, person, interaction, promise = await seed_preparation(db, test_user_id)
        db.add(Interaction(user_id=test_user_id, person_id=person.id, title='Future speculation', date=datetime.now(timezone.utc) + timedelta(days=2)))
        for state in ('completed', 'cancelled'):
            db.add(Commitment(user_id=test_user_id, to_person_id=person.id, description=state, status=state))
        person.notes = 'Corrected note'
        promise.description = 'Updated promise'
        await db.commit()
        result = (await prepare(db, test_user_id, meeting.id))['people'][0]
        assert result['notes'] == 'Corrected note' and len(result['commitments']) == 1
        assert result['commitments'][0]['description'] == 'Updated promise'
        assert result['last_interaction']['source']['id'] == str(interaction.id)
        interaction.deleted_at = promise.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        result = (await prepare(db, test_user_id, meeting.id))['people'][0]
        assert result['last_interaction'] is None and result['commitments'] == []
        person.archived_at = datetime.now(timezone.utc)
        await db.commit()
        assert (await prepare(db, test_user_id, meeting.id))['people'] == []


async def test_preparation_rejects_foreign_meeting_and_poisoned_links(test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        own, person, _, _ = await seed_preparation(db, test_user_id)
        other, foreign, _, _ = await seed_preparation(db, other_user_id)
        db.add(MeetingParticipant(user_id=test_user_id, meeting_id=own.id, person_id=foreign.id))
        db.add(Interaction(user_id=other_user_id, person_id=person.id, title='Foreign secret'))
        db.add(Commitment(user_id=other_user_id, to_person_id=person.id, description='Foreign secret', status='open'))
        await db.commit()
        result = await prepare(db, test_user_id, own.id)
        assert len(result['people']) == 1 and 'Foreign secret' not in str(result)
        for identity in (other.id, str(uuid4())):
            with pytest.raises(NotFoundError):
                await prepare(db, test_user_id, identity)


async def test_preparation_bounds_people_promises_and_excerpts(test_user_id):
    async with TestingSessionLocal() as db:
        meeting, _, _, _ = await seed_preparation(db, test_user_id)
        for index in range(7):
            person = Person(user_id=test_user_id, name=f'Person {index}', notes='x' * 2000)
            db.add(person)
            await db.flush()
            db.add(MeetingParticipant(user_id=test_user_id, meeting_id=meeting.id, person_id=person.id))
            for _count in range(5):
                db.add(Commitment(user_id=test_user_id, from_person_id=person.id, description='y' * 3000, status='waiting'))
        await db.commit()
        result = await prepare(db, test_user_id, meeting.id)
        assert result['more_people'] and len(result['people']) == 5
        for card in result['people']:
            assert card['more_commitments'] and len(card['commitments']) == 3
            assert len(card['notes']) == 301 and len(card['commitments'][0]['description']) == 301
            assert len(card['commitments'][0]['source']['title']) == 121


async def test_preparation_endpoint_private_response_and_owner_denial(async_client, auth_headers, other_auth_headers, test_user_id):
    async with TestingSessionLocal() as db:
        meeting, _, _, _ = await seed_preparation(db, test_user_id)
    path = f'/api/v1/meetings/{meeting.id}/preparation'
    response = await async_client.get(path, headers=auth_headers)
    assert response.status_code == 200 and response.headers['cache-control'] == 'private, no-store'
    assert (await async_client.get(path, headers=other_auth_headers)).status_code == 404
    async with TestingSessionLocal() as db:
        row = await db.get(Meeting, meeting.id)
        row.deleted_at = datetime.now(timezone.utc)
        await db.commit()
    assert (await async_client.get(path, headers=auth_headers)).status_code == 404
