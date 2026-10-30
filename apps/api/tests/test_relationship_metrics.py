import pytest

from app.models.entities import Commitment, Interaction, Person, Project
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_activation_uses_real_density_and_evidence_backed_ask(async_client, auth_headers, other_auth_headers, test_user_id):
    initial = (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()
    assert not initial['activation']['activated']
    assert initial['activation']['counts']['people'] == 0
    async with TestingSessionLocal() as db:
        db.add_all([Person(user_id=test_user_id, name=f'Synthetic contact {i}') for i in range(5)])
        db.add_all([Interaction(user_id=test_user_id, title=f'Synthetic discussion {i}') for i in range(3)])
        db.add(Project(user_id=test_user_id, name='Synthetic project'))
        db.add(Commitment(user_id=test_user_id, description='Synthetic promise'))
        await db.commit()
    density = (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()['activation']
    assert not density['activated'] and density['counts']['ask_answers'] == 0
    query = await async_client.post('/api/v1/ai/content-generate', headers=auth_headers, json={'prompt': 'show open commitments'})
    assert query.status_code == 200, query.text
    activated = (await async_client.get('/api/v1/relationships/home', headers=auth_headers)).json()['activation']
    assert activated['activated'] and activated['first_activated_at']
    assert activated['successful_actions_last_7_days'] == 0
    assert (await async_client.get('/api/v1/relationships/home', headers=other_auth_headers)).json()['activation']['counts']['people'] == 0
    response = await async_client.post('/api/v1/relationships/willingness-to-pay', headers=auth_headers, json={'response': 'yes'})
    assert response.status_code == 200
    activity = (await async_client.get('/api/v1/relationships/activity', headers=auth_headers)).json()
    assert activity['willingness_to_pay'] == 'yes'
    assert sum(item['followups_completed'] for item in activity['weeks']) == 0
