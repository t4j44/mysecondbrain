from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.ai.provider import GeminiLLMProvider
from app.models.entities import Commitment, Interaction, RelationshipAction, Task
from app.services.relationships import recency
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
