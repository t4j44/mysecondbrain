import pytest

from app.ai.provider import GeminiLLMProvider


@pytest.mark.asyncio
async def test_publication_exact_snapshot_owner_checks_and_revocation(async_client, auth_headers, other_auth_headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    memory = await async_client.post('/api/v1/memories', headers=auth_headers,
        json={'title': 'Built a prototype', 'body': 'Private research note for Ahmed', 'category': 'general'})
    assert memory.status_code == 201, memory.text
    payload = {'title': 'Prototype work', 'sources': [{'kind': 'memory', 'id': memory.json()['id']}]}
    denied = await async_client.post('/api/v1/portfolio/drafts', headers=other_auth_headers, json=payload)
    assert denied.status_code == 404
    draft = await async_client.post('/api/v1/portfolio/drafts', headers=auth_headers, json=payload)
    assert draft.status_code == 201, draft.text
    draft_id = draft.json()['id']
    snapshot = {'title': 'Approved title', 'body': 'I built a prototype; impact is not yet measured.'}
    path = f'/api/v1/portfolio/drafts/{draft_id}/publish'
    assert (await async_client.post(path, headers=auth_headers, json=snapshot)).status_code == 422
    snapshot['confirmed_public'] = True
    assert (await async_client.post(path, headers=other_auth_headers, json=snapshot)).status_code == 404
    published = await async_client.post(path, headers=auth_headers, json=snapshot)
    assert published.status_code == 201, published.text
    token = published.json()['share_path'].split('/')[-1]
    public_path = f'/api/v1/public/portfolio/{token}'
    public = await async_client.get(public_path)
    assert public.json() == {'title': snapshot['title'], 'body': snapshot['body']}
    assert 'Ahmed' not in public.text and 'user_id' not in public.text
    assert public.headers['cache-control'] == 'no-store'
    edit_path = f'/api/v1/portfolio/drafts/{draft_id}'
    edit = {'title': 'Private revised title', 'body': 'Private work in progress'}
    assert (await async_client.patch(edit_path, headers=other_auth_headers, json=edit)).status_code == 404
    saved = await async_client.patch(edit_path, headers=auth_headers, json=edit)
    assert saved.status_code == 200 and saved.json()['body'] == edit['body']
    assert (await async_client.get(public_path)).json()['body'] == snapshot['body']
    revoke = f"/api/v1/portfolio/publications/{published.json()['publication_id']}"
    assert (await async_client.delete(revoke, headers=other_auth_headers)).status_code == 404
    assert (await async_client.delete(revoke, headers=auth_headers)).status_code == 204
    assert (await async_client.get(public_path)).status_code == 404


@pytest.mark.asyncio
async def test_feedback_does_not_authorize_a_testimonial(async_client, auth_headers):
    response = await async_client.post('/api/v1/beta/feedback', headers=auth_headers, json={'outcome': 'useful'})
    assert response.status_code == 201
    assert 'not permission' in response.json()['message']
