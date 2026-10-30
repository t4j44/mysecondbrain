"""Prevent private memory and CRM responses from entering shared caches."""


async def test_private_api_responses_cannot_be_cached(async_client, auth_headers):
    public_health = await async_client.get('/api/v1/health')
    assert public_health.status_code == 200
    assert 'no-store' in public_health.headers.get('cache-control', '')

    authenticated = await async_client.get('/api/v1/people', headers=auth_headers)
    assert authenticated.status_code == 200, authenticated.text
    assert authenticated.headers.get('cache-control') == 'private, no-store'

    unauthorized = await async_client.get('/api/v1/people')
    assert unauthorized.status_code == 401
    assert 'no-store' in unauthorized.headers.get('cache-control', '')


async def test_unprotected_liveness_not_subject_to_private_cache_rules(async_client):
    result = await async_client.get('/health/live')
    assert result.status_code == 200
    assert result.headers.get('cache-control') != 'private, no-store'
