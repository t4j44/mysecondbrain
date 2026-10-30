import base64
import json
import time
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.errors import IntegrationError
from app.integrations.google_client import SCOPES, GoogleIntegrationService, account_from_id_token
from app.models.entities import Integration, JobRecord, Task
from tests.conftest import TestingSessionLocal


def id_token(email='taj@example.test', **claims):
    payload = {'iss': 'https://accounts.google.com', 'aud': settings.GOOGLE_CLIENT_ID, 'email': email,
               'email_verified': True, 'exp': time.time() + 600, **claims}
    segment = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    return f'header.{segment}.signature'


@pytest.fixture
def google(monkeypatch):
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_ID', 'test-client')
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setattr(GoogleIntegrationService, '_store_tokens', AsyncMock())
    issued = {'id_token': None}

    async def post(_client, url, **kwargs):
        return httpx.Response(200, request=httpx.Request('POST', url), json={
            'access_token': 'test-access', 'refresh_token': 'test-refresh', 'scope': SCOPES['google_drive'] + ' ' + SCOPES['google_calendar'],
            'id_token': issued['id_token']})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    return issued


async def connect(db, owner, issued, provider, email):
    issued['id_token'] = id_token(email) if email else None
    service = GoogleIntegrationService(db, owner)
    state = parse_qs(urlparse((await service.authorize(provider))['url']).query)['state'][0]
    return await service.connect_oauth_callback('code', state)


@pytest.mark.parametrize('token', [
    None, '', 'garbage', 'a.b.c', id_token(email_verified=False), id_token(aud='someone-else'),
    id_token(iss='https://evil.example'), id_token(exp=time.time() - 5), id_token(email='no-at-sign')])
def test_untrusted_identity_tokens_yield_no_account(token, monkeypatch):
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_ID', 'test-client')
    assert account_from_id_token(token) is None


def test_trusted_identity_token_yields_a_lowercase_email(monkeypatch):
    monkeypatch.setattr(settings, 'GOOGLE_CLIENT_ID', 'test-client')
    assert account_from_id_token(id_token('Taj@Example.TEST')) == 'taj@example.test'
    assert account_from_id_token(id_token(iss='accounts.google.com', email_verified='true')) == 'taj@example.test'


@pytest.mark.asyncio
async def test_authorization_asks_for_identity_and_an_account_chooser(google, test_user_id):
    async with TestingSessionLocal() as db:
        params = parse_qs(urlparse((await GoogleIntegrationService(db, test_user_id).authorize('google_drive'))['url']).query)
    assert params['scope'] == [f"openid email {SCOPES['google_drive']}"]
    assert params['prompt'] == ['select_account consent'] and params['access_type'] == ['offline']


@pytest.mark.asyncio
@pytest.mark.parametrize('hint, expected', [('Taj@Example.test', ['taj@example.test']), ('not an email', None), ('a b@c.d', None), (None, None)])
async def test_login_hint_preselects_a_known_account_but_never_a_malformed_one(google, test_user_id, hint, expected):
    async with TestingSessionLocal() as db:
        params = parse_qs(urlparse((await GoogleIntegrationService(db, test_user_id).authorize('google_calendar', hint))['url']).query)
    assert params.get('login_hint') == expected


@pytest.mark.asyncio
async def test_each_google_account_is_its_own_connection_and_reconnecting_reuses_it(google, test_user_id):
    async with TestingSessionLocal() as db:
        first = await connect(db, test_user_id, google, 'google_drive', 'one@example.test')
        second = await connect(db, test_user_id, google, 'google_drive', 'two@example.test')
        again = await connect(db, test_user_id, google, 'google_drive', 'ONE@example.test')
        assert first['account_identifier'] == 'one@example.test' and 'one@example.test' in first['message']
        assert first['integration_id'] == again['integration_id'] != second['integration_id']
        rows = (await db.execute(select(Integration).order_by(Integration.created_at))).scalars().all()
        assert [row.account_identifier for row in rows] == ['one@example.test', 'two@example.test'] and all(row.is_connected for row in rows)
        await connect(db, test_user_id, google, 'google_calendar', 'one@example.test')
        assert await db.scalar(select(func.count()).select_from(Integration)) == 3


@pytest.mark.asyncio
async def test_connection_without_a_verified_account_keeps_the_single_legacy_slot(google, test_user_id):
    async with TestingSessionLocal() as db:
        first = await connect(db, test_user_id, google, 'google_drive', None)
        second = await connect(db, test_user_id, google, 'google_drive', None)
        assert first['account_identifier'] is None and first['integration_id'] == second['integration_id']
        assert await db.scalar(select(func.count()).select_from(Integration)) == 1


@pytest.mark.asyncio
async def test_database_rejects_a_duplicate_account_even_in_another_case(test_user_id):
    async with TestingSessionLocal() as db:
        db.add(Integration(user_id=test_user_id, provider_name='google_drive', account_identifier='a@example.test'))
        await db.commit()
        db.add(Integration(user_id=test_user_id, provider_name='google_drive', account_identifier='A@EXAMPLE.test'))
        with pytest.raises(IntegrityError):
            await db.commit()


@pytest.mark.asyncio
async def test_account_must_be_chosen_when_several_are_connected(google, test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        one = await connect(db, test_user_id, google, 'google_calendar', 'one@example.test')
        service = GoogleIntegrationService(db, test_user_id)
        assert str((await service.select_integration('google_calendar')).id) == one['integration_id']
        two = await connect(db, test_user_id, google, 'google_calendar', 'two@example.test')
        with pytest.raises(IntegrationError) as ambiguous:
            await service.select_integration('google_calendar')
        assert ambiguous.value.code == 'GOOGLE_ACCOUNT_REQUIRED'
        assert str((await service.select_integration('google_calendar', two['integration_id'])).id) == two['integration_id']
        foreign = GoogleIntegrationService(db, other_user_id)
        with pytest.raises(IntegrationError) as stranger:
            await foreign.select_integration('google_calendar', two['integration_id'])
        assert stranger.value.code == 'GOOGLE_ACCOUNT_NOT_FOUND'
        with pytest.raises(IntegrationError):
            await service.select_integration('google_drive')


@pytest.mark.asyncio
async def test_disconnect_removes_only_the_chosen_account(google, test_user_id, monkeypatch):
    monkeypatch.setattr('app.integrations.google_client.admin_db_session', lambda reason: _NoVault())
    async with TestingSessionLocal() as db:
        one = await connect(db, test_user_id, google, 'google_drive', 'one@example.test')
        two = await connect(db, test_user_id, google, 'google_drive', 'two@example.test')
        service = GoogleIntegrationService(db, test_user_id)
        with pytest.raises(IntegrationError) as ambiguous:
            await service.disconnect_provider('google_drive')
        assert ambiguous.value.code == 'GOOGLE_ACCOUNT_REQUIRED'
        assert await service.disconnect_provider('google_drive', one['integration_id']) is True
        states = {row.account_identifier: row.is_connected for row in (await db.execute(select(Integration))).scalars()}
        assert states == {'one@example.test': False, 'two@example.test': True}
        assert await service.disconnect_provider('google_drive', one['integration_id']) is False
        assert str((await service.select_integration('google_drive')).id) == two['integration_id']


class _NoVault:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, *args, **kwargs):
        return None

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_jobs_are_pinned_to_one_account_when_queued(google, test_user_id, monkeypatch):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    async with TestingSessionLocal() as db:
        one = await connect(db, test_user_id, google, 'google_drive', 'one@example.test')
        service = GoogleIntegrationService(db, test_user_id)
        job = await service.trigger_drive_sync_job(None, 'one_way')
        assert job.result_payload['integration_id'] == one['integration_id']
        two = await connect(db, test_user_id, google, 'google_drive', 'two@example.test')
        with pytest.raises(IntegrationError):
            await service.trigger_drive_sync_job(None, 'one_way')
        pinned = await service.trigger_drive_sync_job(None, 'one_way', two['integration_id'])
        assert pinned.result_payload['integration_id'] == two['integration_id']


@pytest.mark.asyncio
async def test_each_drive_account_keeps_its_own_archive_file(monkeypatch, test_user_id):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    generated = iter(['file-for-one', 'file-for-two'])
    created = []

    async def request(_client, method, url, **kwargs):
        data = {}
        if url.endswith('generateIds'):
            data = {'ids': [next(generated)]}
        code = 404 if method == 'GET' and not url.endswith('generateIds') else 200
        if method == 'POST':
            created.append(kwargs['json']['id'])
        return httpx.Response(code, json=data, request=httpx.Request(method, url))
    monkeypatch.setattr(httpx.AsyncClient, 'request', request)
    async with TestingSessionLocal() as db:
        rows = [Integration(user_id=test_user_id, provider_name='google_drive', account_identifier=name, scopes=[SCOPES['google_drive']])
                for name in ('one@example.test', 'two@example.test')]
        db.add_all(rows)
        await db.commit()
        service = GoogleIntegrationService(db, test_user_id)
        one = await service.export_drive({'integration_id': str(rows[0].id)})
        two = await service.export_drive({'integration_id': str(rows[1].id)})
        again = await service.export_drive({'integration_id': str(rows[0].id)})
        assert (one['file_id'], two['file_id'], again['file_id']) == ('file-for-one', 'file-for-two', 'file-for-one')
        kinds = set((await db.execute(select(JobRecord.job_type).where(JobRecord.job_type.like('drive_archive_identity%')))).scalars())
        assert kinds == {f'drive_archive_identity:{rows[0].id}', f'drive_archive_identity:{rows[1].id}'}


@pytest.mark.asyncio
async def test_existing_archive_is_adopted_by_the_only_drive_connection(monkeypatch, test_user_id):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))

    async def request(_client, method, url, **kwargs):
        return httpx.Response(200, json={}, request=httpx.Request(method, url))
    monkeypatch.setattr(httpx.AsyncClient, 'request', request)
    async with TestingSessionLocal() as db:
        row = Integration(user_id=test_user_id, provider_name='google_drive', account_identifier='one@example.test', scopes=[SCOPES['google_drive']])
        db.add_all([row, JobRecord(user_id=test_user_id, job_type='drive_archive_identity', status='completed', result_payload={'file_id': 'existing-file'})])
        await db.commit()
        result = await GoogleIntegrationService(db, test_user_id).export_drive({'integration_id': str(row.id)})
        assert result['file_id'] == 'existing-file'
        assert await db.scalar(select(JobRecord.job_type).where(JobRecord.job_type.like('drive_archive_identity%'))) == f'drive_archive_identity:{row.id}'


@pytest.mark.asyncio
async def test_task_scheduling_requires_a_choice_and_never_moves_an_existing_event(async_client, auth_headers, test_user_id, monkeypatch):
    monkeypatch.setattr(GoogleIntegrationService, 'access_token', AsyncMock(return_value='test-access'))
    async with TestingSessionLocal() as db:
        rows = [Integration(user_id=test_user_id, provider_name='google_calendar', account_identifier=name, scopes=[SCOPES['google_calendar']])
                for name in ('one@example.test', 'two@example.test')]
        task = Task(user_id=test_user_id, title='Send deck')
        db.add_all([*rows, task])
        await db.commit()
        one, two, task_id = str(rows[0].id), str(rows[1].id), str(task.id)
    path = f'/api/v1/integrations/google/tasks/{task_id}/schedule'
    body = {'start': '2026-11-02T10:00:00+06:00', 'timezone': 'Asia/Dhaka'}

    ambiguous = await async_client.post(path, headers=auth_headers, json=body)
    assert ambiguous.status_code == 409 and ambiguous.json()['error']['code'] == 'GOOGLE_ACCOUNT_REQUIRED'

    queued = await async_client.post(path, headers=auth_headers, json={**body, 'integration_id': one})
    assert queued.status_code == 202, queued.text
    async with TestingSessionLocal() as db:
        job = await db.get(JobRecord, queued.json()['job_id'])
        assert job.result_payload['integration_id'] == one
        stored = await db.get(Task, task_id)
        assert stored.calendar_sync_metadata['integration_id'] == one
        stored.gcal_event_id = 'event-on-account-one'
        await db.commit()

    moved = await async_client.post(path, headers=auth_headers, json={**body, 'integration_id': two})
    assert moved.status_code == 409 and 'another Google account' in moved.json()['error']['message']
    assert (await async_client.post(path, headers=auth_headers, json={**body, 'integration_id': one})).status_code == 202
