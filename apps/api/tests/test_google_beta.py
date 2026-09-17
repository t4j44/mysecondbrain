from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import select

from app.config import settings
from app.core.errors import IntegrationError
from app.integrations.google_client import SCOPES, GoogleIntegrationService
from app.models.entities import Integration, Task
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_oauth_state_is_owner_bound_single_use_and_pkce(monkeypatch, test_user_id, other_user_id):
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_ID', 'test-client')
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_SECRET', 'test-secret')
    store = AsyncMock()
    monkeypatch.setattr(GoogleIntegrationService, '_store_tokens', store)
    calls = []
    async def post(_client, url, **kwargs):
        calls.append(kwargs['data'])
        return httpx.Response(200, request=httpx.Request('POST', url), json={
            'access_token': 'test-access', 'refresh_token': 'test-refresh', 'scope': SCOPES['google_drive']})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    async with TestingSessionLocal() as db:
        service = GoogleIntegrationService(db, test_user_id)
        authorization = await service.authorize('google_drive')
        params = parse_qs(urlparse(authorization['url']).query)
        state = params['state'][0]
        assert params['code_challenge_method'] == ['S256']
        with pytest.raises(IntegrationError):
            await GoogleIntegrationService(db, other_user_id).connect_oauth_callback('code', state)
        assert calls == []
        result = await service.connect_oauth_callback('code', state)
        assert result['status'] == 'connected'
        assert calls[0]['code_verifier'] and calls[0]['redirect_uri'] == settings.GOOGLE_REDIRECT_URI
        assert store.await_count == 1
        assert (await db.scalar(select(Integration))).is_connected
        with pytest.raises(IntegrationError):
            await service.connect_oauth_callback('code', state)
        assert len(calls) == 1


@pytest.mark.asyncio
async def test_calendar_retries_update_and_cancellation_recreates_with_new_id(monkeypatch, test_user_id):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    requests = []
    active = set()
    async def request(_client, method, url, **kwargs):
        requests.append((method, url, kwargs))
        assert kwargs['params']['sendUpdates'] == 'none'
        assert kwargs['headers']['Authorization'] == 'Bearer test-access'
        if method == 'POST':
            identity = kwargs['json']['id']
            code = 409 if identity in active else 200
            active.add(identity)
        else:
            code = 200
        return httpx.Response(code, json={}, request=httpx.Request(method, url))
    monkeypatch.setattr(httpx.AsyncClient, 'request', request)
    async with TestingSessionLocal() as db:
        task = Task(user_id=test_user_id, title='Send deck', calendar_sync_metadata={
            'enabled': True, 'start': '2026-09-20T10:00:00+06:00', 'end': '2026-09-20T10:30:00+06:00', 'timezone': 'Asia/Dhaka'})
        db.add(task)
        await db.commit()
        service = GoogleIntegrationService(db, test_user_id)
        payload = {'task_id': str(task.id), 'calendar_id': 'primary'}
        assert (await service.sync_calendar(payload))['events_synced'] == 1
        original_id = task.gcal_event_id
        assert 'attendees' not in requests[0][2]['json']
        await service.sync_calendar(payload)
        assert requests[-1][0] == 'PATCH'
        assert task.gcal_event_id == original_id
        task.calendar_sync_metadata = {**task.calendar_sync_metadata, 'cancel': True}
        await db.commit()
        await service.sync_calendar(payload)
        assert requests[-1][0] == 'DELETE'
        assert task.gcal_event_id is None
        task.calendar_sync_metadata = {**task.calendar_sync_metadata, 'enabled': True, 'cancel': False}
        await db.commit()
        await service.sync_calendar(payload)
        assert task.gcal_event_id != original_id


@pytest.mark.asyncio
async def test_drive_reuses_archive_identity_on_retry(monkeypatch, test_user_id):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    calls = []
    exists = False
    async def request(_client, method, url, **kwargs):
        nonlocal exists
        calls.append((method, url))
        code, data = 200, {}
        if url.endswith('generateIds'):
            data = {'ids': ['drive-file-fixture']}
        elif method == 'GET':
            code = 200 if exists else 404
        elif method == 'POST':
            exists = True
        return httpx.Response(code, json=data, request=httpx.Request(method, url))
    monkeypatch.setattr(httpx.AsyncClient, 'request', request)
    async with TestingSessionLocal() as db:
        db.add(Integration(user_id=test_user_id, provider_name='google_drive', status='connected', scopes=[SCOPES['google_drive']]))
        await db.commit()
        service = GoogleIntegrationService(db, test_user_id)
        first = await service.export_drive({})
        second = await service.export_drive({})
        assert first['file_id'] == second['file_id']
        assert sum(url.endswith('generateIds') for _, url in calls) == 1
        assert sum(method == 'POST' for method, _ in calls) == 1
