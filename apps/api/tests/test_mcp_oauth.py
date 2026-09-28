"""OAuth through HTTP handlers and the mounted SDK, including adversarial reuse."""
import base64
import hashlib
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.mcp.oauth_provider import DEFAULT_SCOPES, SCOPES, digest, issuer, now, oauth_provider, resource
from app.mcp.server import mcp_server
from app.models.entities import Memory
from app.models.oauth import OAuthClient, OAuthCode, OAuthGrant, OAuthTokenRecord
from tests.conftest import TestingSessionLocal

pytestmark = pytest.mark.asyncio
CALLBACK = 'https://client.example.test/callback'
VERIFIER = 'v' * 64
CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip('=')


async def register(client, method='none', **extra):
    response = await client.post('/oauth/register', json={'client_name': 'Synthetic connector',
        'redirect_uris': [CALLBACK], 'token_endpoint_auth_method': method,
        'grant_types': ['authorization_code', 'refresh_token'], 'response_types': ['code'],
        'scope': ' '.join(DEFAULT_SCOPES + ['offline_access', 'mcp:tasks:write']), **extra})
    assert response.status_code == 201, response.text
    return response.json()


async def authorize(client, registered, **extra):
    return await client.get('/oauth/authorize', params={'client_id': registered['client_id'],
        'redirect_uri': CALLBACK, 'response_type': 'code', 'resource': resource(),
        'code_challenge': CHALLENGE, 'code_challenge_method': 'S256', 'state': 'opaque-state',
        'scope': ' '.join(DEFAULT_SCOPES + ['offline_access']), **extra})


async def consent(client, headers, registered=None, scopes=None):
    registered = registered or await register(client)
    response = await authorize(client, registered)
    assert response.status_code in (302, 303, 307), response.text
    pending = parse_qs(urlparse(response.headers['location']).fragment)['request'][0]
    details = await client.post('/oauth/consent/details', headers=headers, json={'request': pending})
    assert details.status_code == 200, details.text
    response = await client.post('/oauth/consent/decision', headers=headers, json={
        'request': pending, 'confirmed': True, 'approve': True, 'scopes': scopes or DEFAULT_SCOPES + ['offline_access']})
    assert response.status_code == 200, response.text
    query = parse_qs(urlparse(response.json()['redirect_to']).query)
    assert query['state'] == ['opaque-state'] and query['iss'] == [issuer()]
    return registered, query['code'][0]


async def exchange(client, registered, code, **extra):
    return await client.post('/oauth/token', data={'client_id': registered['client_id'],
        'grant_type': 'authorization_code', 'code': code, 'code_verifier': VERIFIER,
        'redirect_uri': CALLBACK, 'resource': resource(), **extra})


async def test_oauth_transport_owner_scopes_refresh_and_reuse(async_client, auth_headers, test_user_id, other_user_id, fresh_mcp_transport):
    registered, code = await consent(async_client, auth_headers)
    response = await exchange(async_client, registered, code)
    assert response.status_code == 200, response.text
    token = response.json()
    assert response.headers['cache-control'] == 'no-store'
    assert (await exchange(async_client, registered, code)).status_code == 400
    async with TestingSessionLocal() as db:
        db.add_all([Memory(user_id=test_user_id, title='Owned context', content='oranges owned'),
                    Memory(user_id=other_user_id, title='Foreign context', content='oranges foreign')])
        await db.commit()
        assert await db.get(OAuthCode, digest(code))
        assert await db.get(OAuthTokenRecord, digest(token['access_token']))
        assert not await db.get(OAuthTokenRecord, token['access_token'])
    headers = {'Authorization': 'Bearer ' + token['access_token'], 'Accept': 'application/json, text/event-stream'}
    async with mcp_server.session_manager.run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://localhost') as client:
            unauthenticated = await client.get('/mcp', headers={'Accept': headers['Accept']})
            assert unauthenticated.status_code == 401
            assert 'resource_metadata=' in unauthenticated.headers['www-authenticate']
            response = await client.post('/mcp', headers=headers, json={'jsonrpc': '2.0', 'id': 1,
                'method': 'tools/call', 'params': {'name': 'search_context', 'arguments': {'query': 'oranges'}}})
            assert response.status_code == 200 and 'oranges owned' in response.text and 'oranges foreign' not in response.text
            denied = await client.post('/mcp', headers=headers, json={'jsonrpc': '2.0', 'id': 2,
                'method': 'tools/call', 'params': {'name': 'create_task', 'arguments': {'title': 'Unapproved'}}})
            assert denied.json()['result']['isError']
    data = {'client_id': registered['client_id'], 'grant_type': 'refresh_token',
            'refresh_token': token['refresh_token'], 'resource': resource()}
    escalated = await async_client.post('/oauth/token', data={**data, 'scope': 'mcp:tasks:write'})
    assert escalated.status_code == 400
    rotated = await async_client.post('/oauth/token', data=data)
    assert rotated.status_code == 200, rotated.text
    fresh = rotated.json()
    assert fresh['refresh_token'] != token['refresh_token']
    assert await oauth_provider.load_access_token(fresh['access_token'])
    assert (await async_client.post('/oauth/token', data=data)).status_code == 400
    assert await oauth_provider.load_access_token(fresh['access_token']) is None
    assert await oauth_provider.load_access_token(token['access_token']) is None


async def test_consent_owner_binding_denial_and_scope_escalation(async_client, auth_headers, other_auth_headers):
    registered = await register(async_client)
    response = await authorize(async_client, registered)
    pending = parse_qs(urlparse(response.headers['location']).fragment)['request'][0]
    body = {'request': pending}
    assert (await async_client.post('/oauth/consent/details', json=body)).status_code == 401
    assert (await async_client.post('/oauth/consent/details', headers=auth_headers, json=body)).status_code == 200
    assert (await async_client.post('/oauth/consent/details', headers=other_auth_headers, json=body)).status_code == 400
    decision = {**body, 'confirmed': True, 'approve': True, 'scopes': ['mcp:tasks:write']}
    assert (await async_client.post('/oauth/consent/decision', headers=auth_headers, json=decision)).status_code == 400
    denied = await async_client.post('/oauth/consent/decision', headers=auth_headers,
                                    json={**body, 'confirmed': True, 'approve': False})
    assert 'error=access_denied' in denied.json()['redirect_to']
    assert (await async_client.post('/oauth/consent/decision', headers=auth_headers, json=decision)).status_code == 400
    async with TestingSessionLocal() as db:
        assert not (await db.execute(select(OAuthGrant))).scalars().all()


@pytest.mark.parametrize('bad', [
    {'code_verifier': 'x' * 64}, {'redirect_uri': 'https://evil.example/callback'},
    {'resource': resource() + '/other'}, {'scope': 'mcp:tasks:write'},
])
async def test_token_binding_rejects_without_consuming_valid_code(async_client, auth_headers, bad):
    registered, code = await consent(async_client, auth_headers)
    assert (await exchange(async_client, registered, code, **bad)).status_code == 400
    assert (await exchange(async_client, registered, code)).status_code == 200


async def test_expiry_read_consent_disconnect_and_discovery(async_client, auth_headers, other_auth_headers):
    registered, code = await consent(async_client, auth_headers, scopes=DEFAULT_SCOPES)
    token = (await exchange(async_client, registered, code)).json()
    assert not token.get('refresh_token')
    listing = await async_client.get('/api/v1/mcp/oauth/connections', headers=auth_headers)
    grant = listing.json()[0]
    assert (await async_client.get('/api/v1/mcp/oauth/connections', headers=other_auth_headers)).json() == []
    path = '/api/v1/mcp/oauth/connections/' + grant['id']
    assert (await async_client.delete(path, headers=other_auth_headers)).status_code == 404
    assert (await async_client.delete(path, headers=auth_headers)).status_code == 200
    assert await oauth_provider.load_access_token(token['access_token']) is None
    registered, code = await consent(async_client, auth_headers)
    async with TestingSessionLocal() as db:
        row = await db.get(OAuthCode, digest(code))
        row.expires_at = now() - timedelta(seconds=1)
        await db.commit()
    assert (await exchange(async_client, registered, code)).status_code == 400
    protected = (await async_client.get('/.well-known/oauth-protected-resource/mcp')).json()
    assert protected['resource'] == resource() and set(protected['scopes_supported']) == set(SCOPES) - {'offline_access'}
    metadata = (await async_client.get('/.well-known/oauth-authorization-server')).json()
    assert metadata['code_challenge_methods_supported'] == ['S256']
    assert metadata['issuer'] == issuer()


async def test_confidential_client_hash_and_revocation(async_client, auth_headers):
    registered = await register(async_client, 'client_secret_post')
    registered, code = await consent(async_client, auth_headers, registered=registered)
    assert (await exchange(async_client, registered, code, client_secret='wrong')).status_code == 401
    result = await exchange(async_client, registered, code, client_secret=registered['client_secret'])
    assert result.status_code == 200, result.text
    async with TestingSessionLocal() as db:
        row = await db.get(OAuthClient, registered['client_id'])
        assert row.secret_hash == digest(registered['client_secret'])
        assert 'client_secret' not in row.metadata_payload
    token = result.json()['access_token']
    revoked = await async_client.post('/oauth/revoke', data={'client_id': registered['client_id'],
        'client_secret': registered['client_secret'], 'token': token})
    assert revoked.status_code == 200
    assert await oauth_provider.load_access_token(token) is None


async def test_basic_client_header_and_expired_access(async_client, auth_headers):
    registered = await register(async_client, 'client_secret_basic')
    registered, code = await consent(async_client, auth_headers, registered=registered)
    basic = base64.b64encode((registered['client_id'] + ':' + registered['client_secret']).encode()).decode()
    response = await async_client.post('/oauth/token', headers={'Authorization': 'Basic ' + basic}, data={
        'grant_type': 'authorization_code', 'code': code, 'code_verifier': VERIFIER,
        'redirect_uri': CALLBACK, 'resource': resource()})
    assert response.status_code == 200, response.text
    token = response.json()['access_token']
    async with TestingSessionLocal() as db:
        row = await db.get(OAuthTokenRecord, digest(token))
        row.expires_at = now() - timedelta(seconds=1)
        await db.commit()
    assert await oauth_provider.load_access_token(token) is None


@pytest.mark.parametrize('callback', ['http://public.example/callback', 'https://*.example/callback', 'https://client.example/callback#fragment'])
async def test_registration_rejects_unsafe_callbacks(async_client, callback):
    result = await async_client.post('/oauth/register', json={'client_name': 'Unsafe', 'redirect_uris': [callback],
        'token_endpoint_auth_method': 'none', 'grant_types': ['authorization_code'], 'response_types': ['code']})
    assert result.status_code == 400
