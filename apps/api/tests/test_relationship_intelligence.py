from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.ai.provider import GeminiLLMProvider
from app.ai.structured import structured_answer
from app.models.entities import (
    Commitment,
    EntityEdge,
    Interaction,
    Person,
    Project,
    RelationshipAction,
    Task,
)
from app.services.relationships import RelationshipService, recency
from tests.conftest import TestingSessionLocal


async def capture(client, headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    draft = (await client.post('/api/v1/capture/propose', headers=headers, json={'text': 'Met Ahmed at Agami. We discussed fundraising. I promised the deck.'})).json()
    proposal = {**draft['proposal'], 'person_name': 'Ahmed', 'organization_name': 'ABC Ventures',
        'summary': 'Discussed Justor AI fundraising.', 'where_met': 'Agami', 'topics': ['fundraising'],
        'commitment': 'Send the deck', 'direction': 'owed_by_me',
        'due_at': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}
    saved = await client.post(f"/api/v1/capture/{draft['draft_id']}/confirm", headers=headers, json={'confirmed': True, 'proposal': proposal})
    assert saved.status_code == 200, saved.text
    return {row['type']: row['id'] for row in saved.json()['records']}


@pytest.mark.asyncio
async def test_profile_followup_outcome_replay_and_deletion(async_client, auth_headers, other_auth_headers, monkeypatch):
    ids = await capture(async_client, auth_headers, monkeypatch)
    path = f"/api/v1/relationships/people/{ids['person']}"
    assert (await async_client.get(path, headers=other_auth_headers)).status_code == 404
    profile = await async_client.get(path, headers=auth_headers)
    assert profile.status_code == 200, profile.text
    data = profile.json()
    assert data['topics'] == ['fundraising']
    assert data['timeline'][0]['location'] == 'Agami'
    assert data['commitments'][0]['direction'] == 'owed_by_me'
    async with TestingSessionLocal() as db:
        owner = str((await db.get(Person, ids['person'])).user_id)
        discussion = await structured_answer(db, owner, 'What did I discuss with Ahmed?')
        assert ids['interaction'] in discussion['source_citations']
        promise = await structured_answer(db, owner, 'What did I promise Ahmed?')
        assert ids['commitment'] in promise['source_citations']
        relevant = await structured_answer(db, owner, 'Who could help with Justor AI fundraising?')
        assert ids['person'] in relevant['source_citations']
        open_promises = await structured_answer(db, owner, 'show open commitments')
        assert ids['commitment'] in open_promises['source_citations']
    home = await async_client.get('/api/v1/relationships/home', headers=auth_headers)
    assert home.status_code == 200, home.text
    suggestion = home.json()['followups'][0]
    assert suggestion['evidence']['id'] == ids['commitment']
    draft = await async_client.post(path + '/draft', headers=auth_headers, json={'suggestion_key': suggestion['key']})
    assert draft.status_code == 200 and 'Nothing has been sent' in draft.json()['notice']
    action = {'confirmed': True, 'request_id': str(uuid4()), 'suggestion_key': suggestion['key'], 'action': 'completed', 'outcome': 'Sent the deck. Ahmed offered an introduction.'}
    assert (await async_client.post(path + '/actions', headers=other_auth_headers, json=action)).status_code == 404
    assert (await async_client.post(path + '/actions', headers=auth_headers, json={**action, 'confirmed': False})).status_code == 422
    assert (await async_client.post(path + '/actions', headers=auth_headers, json={**action, 'outcome': ''})).status_code == 422
    completed = await async_client.post(path + '/actions', headers=auth_headers, json=action)
    assert completed.status_code == 200, completed.text
    assert (await async_client.post(path + '/actions', headers=auth_headers, json=action)).json() == completed.json()
    assert (await async_client.post(path + '/actions', headers=auth_headers, json={**action, 'request_id': str(uuid4())})).status_code == 409
    async with TestingSessionLocal() as db:
        assert (await db.get(Commitment, ids['commitment'])).status == 'completed'
        assert (await db.get(Task, ids['task'])).status == 'done'
        assert await db.scalar(select(func.count()).select_from(RelationshipAction)) == 1
        assert await db.scalar(select(func.count()).select_from(Interaction)) == 2
    assert (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()['followups'] == []
    assert (await async_client.delete(f"/api/v1/people/{ids['person']}", headers=auth_headers)).status_code in (200, 204)
    assert (await async_client.get(path, headers=auth_headers)).status_code == 404
    assert (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()['recent_activity'] == []
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(RelationshipAction)) == 0


@pytest.mark.asyncio
async def test_schedule_dismiss_and_private_home(async_client, auth_headers, other_auth_headers, monkeypatch):
    ids = await capture(async_client, auth_headers, monkeypatch)
    path = f"/api/v1/relationships/people/{ids['person']}"
    item = (await async_client.get(path, headers=auth_headers)).json()['followups'][0]
    payload = {'confirmed': True, 'request_id': str(uuid4()), 'suggestion_key': item['key'], 'action': 'scheduled', 'scheduled_at': (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()}
    response = await async_client.post(path + '/actions', headers=auth_headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()['records'][0]['kind'] == 'task'
    assert (await async_client.get(path, headers=auth_headers)).json()['followups'] == []
    foreign = (await async_client.get('/api/v1/relationships/home', headers=other_auth_headers)).json()
    assert not foreign['followups'] and not foreign['recent_activity']


def test_recency_is_explainable_not_a_confidence_score():
    now = datetime.now(timezone.utc)
    assert recency(None, 0, now)['label'] == 'Unknown'
    for days, label in ((0, 'Active'), (14, 'Active'), (15, 'Warm'), (46, 'Cooling'), (91, 'Dormant')):
        result = recency(now - timedelta(days=days), 3, now)
        assert result['label'] == label and result['days_since'] == days
        assert 'closeness' in result['rule']


@pytest.mark.asyncio
async def test_explicit_links_drive_home_and_ask_without_cross_owner_connections(async_client, auth_headers, test_user_id, other_user_id, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    async with TestingSessionLocal() as db:
        person = Person(user_id=test_user_id, name='Salma', last_interaction_at=datetime.now(timezone.utc) - timedelta(days=80),
            follow_up_date=datetime.now(timezone.utc) + timedelta(days=7))
        project = Project(user_id=test_user_id, name='Saudi Arabia market entry', status='active')
        foreign = Project(user_id=other_user_id, name='Foreign private project', status='active')
        db.add_all([person, project, foreign])
        await db.commit()
        person_id, project_id, foreign_id = str(person.id), str(project.id), str(foreign.id)
        assert await RelationshipService(db, test_user_id).followups(person_id) == []
    path = f'/api/v1/relationships/people/{person_id}/connections'
    payload = {'confirmed': True, 'kind': 'project', 'record_id': project_id, 'reason': 'Salma offered to review the Saudi Arabia market plan.'}
    assert (await async_client.post(path, headers=auth_headers, json={**payload, 'record_id': foreign_id})).status_code == 404
    assert (await async_client.post(path, headers=auth_headers, json={**payload, 'confirmed': False})).status_code == 422
    assert (await async_client.post(path, headers=auth_headers, json=payload)).status_code == 200
    assert (await async_client.post(path, headers=auth_headers, json=payload)).status_code == 200
    home = (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()
    assert home['projects'][0]['people'][0]['person_id'] == person_id
    async with TestingSessionLocal() as db:
        result = await structured_answer(db, test_user_id, 'Who is connected to Saudi Arabia?')
        assert person_id in result['source_citations'] and project_id in result['source_citations']
    await async_client.delete('/api/v1/people/' + person_id, headers=auth_headers)
    async with TestingSessionLocal() as db:
        result = await structured_answer(db, test_user_id, 'Who is connected to Saudi Arabia?')
        assert person_id not in result['source_citations']


@pytest.mark.asyncio
async def test_deleted_interaction_cannot_support_a_contact_recommendation(test_user_id, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    async with TestingSessionLocal() as db:
        person = Person(user_id=test_user_id, name='Salma')
        project = Project(user_id=test_user_id, name='Saudi Arabia expansion', status='active')
        db.add_all([person, project])
        await db.flush()
        interaction = Interaction(user_id=test_user_id, person_id=person.id, project_id=project.id,
            title='Private context', summary='Recorded introduction', interaction_type='note', date=datetime.now(timezone.utc))
        db.add(interaction)
        await db.flush()
        db.add(EntityEdge(user_id=test_user_id, source_entity_type='person', source_entity_id=person.id,
            target_entity_type='project', target_entity_id=project.id, relationship_type='discussed',
            metadata_payload={'interaction_id': str(interaction.id)}))
        await db.commit()
        assert str(person.id) in (await structured_answer(db, test_user_id, 'Who is connected to Saudi Arabia?'))['source_citations']
        interaction.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        assert not (await structured_answer(db, test_user_id, 'Who is connected to Saudi Arabia?'))['source_citations']
