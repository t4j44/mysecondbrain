import pytest
from sqlalchemy import func, select

from app.ai.provider import GeminiLLMProvider
from app.models.entities import (
    Commitment,
    EntityEdge,
    Interaction,
    JobRecord,
    Memory,
    Organization,
    Person,
    Task,
)
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_review_capture_atomic_replay_and_owner_boundary(async_client, auth_headers, other_auth_headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    draft = await async_client.post('/api/v1/capture/propose', headers=auth_headers,
        json={'text': 'Met Ahmed at the launch. Promised the deck.', 'source': 'manual'})
    assert draft.status_code == 200, draft.text
    data = draft.json()
    assert data['mode'] == 'manual_review'
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Person)) == 0
    proposal = {**data['proposal'], 'person_name': 'Ahmed', 'organization_name': 'Acme',
                'commitment': 'Send the deck', 'direction': 'owed_by_me', 'where_met': 'Launch'}
    path = f"/api/v1/capture/{data['draft_id']}/confirm"
    payload = {'confirmed': True, 'proposal': proposal}
    foreign = await async_client.post(path, headers=other_auth_headers, json=payload)
    assert foreign.status_code == 404
    saved = await async_client.post(path, headers=auth_headers, json=payload)
    assert saved.status_code == 200, saved.text
    replay = await async_client.post(path, headers=auth_headers, json=payload)
    assert replay.json() == saved.json()
    async with TestingSessionLocal() as db:
        for model in (Person, Organization, Interaction, Memory, Commitment, Task):
            assert await db.scalar(select(func.count()).select_from(model)) == 1
        assert await db.scalar(select(func.count()).select_from(EntityEdge)) == 5
        assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type == 'index_record')) == 6
    source = next(record for record in saved.json()['records'] if record['type'] == 'memory')
    source_path = f"/api/v1/sources/memory/{source['id']}"
    assert (await async_client.get(source_path, headers=auth_headers)).status_code == 200
    assert (await async_client.get(source_path, headers=other_auth_headers)).status_code == 404
    search = await async_client.post('/api/v1/ai/search', headers=auth_headers, json={'query': 'Ahmed deck'})
    assert search.status_code == 200, search.text
    assert search.json()['total_matches'] >= 2
    foreign_search = await async_client.post('/api/v1/ai/search', headers=other_auth_headers, json={'query': 'Ahmed deck'})
    assert foreign_search.json()['total_matches'] == 0
    counts = (await async_client.get('/api/v1/beta/value', headers=auth_headers)).json()['counts']
    assert counts == {'capture_confirmed': 1, 'beta_retrieval': 1, 'beta_source_opened': 1}
    other_counts = (await async_client.get('/api/v1/beta/value', headers=other_auth_headers)).json()['counts']
    assert other_counts == {'capture_confirmed': 0, 'beta_retrieval': 1, 'beta_source_opened': 0}
    await async_client.delete(f"/api/v1/memories/{source['id']}", headers=auth_headers)
    assert (await async_client.get(source_path, headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_failed_capture_rolls_back_all_created_records(async_client, auth_headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    draft = (await async_client.post('/api/v1/capture/propose', headers=auth_headers, json={'text': 'A note'})).json()
    response = await async_client.post(f"/api/v1/capture/{draft['draft_id']}/confirm", headers=auth_headers,
        json={'confirmed': True, 'proposal': {**draft['proposal'], 'organization_name': 'Unsaved',
              'person_name': 'Unsaved', 'project_name': 'Missing project'}})
    assert response.status_code == 409
    async with TestingSessionLocal() as db:
        for model in (Organization, Person, Memory):
            assert await db.scalar(select(func.count()).select_from(model)) == 0
