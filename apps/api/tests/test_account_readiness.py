import io
import json
import zipfile
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.integrations.storage_client import StorageService
from app.models.entities import AccountClosure, Memory, Person, Profile
from app.services.account import close_account, portable_export, request_closure
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_portable_export_is_complete_owner_scoped_and_strips_credentials(test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        db.add_all([Memory(user_id=test_user_id, title='Own', content='=formula'),
            Memory(user_id=other_user_id, title='Other', content='private foreign'),
            Profile(id=test_user_id, email='synthetic@example.test', settings={'mcp_credentials': [{'key_hash': 'secret'}]})])
        await db.commit()
        content = await portable_export(db, test_user_id)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            data = json.loads(archive.read('data.json'))
            assert [r['title'] for r in data['tables']['memories']] == ['Own']
            assert 'mcp_credentials' not in str(data)
            assert 'private foreign' not in str(data)
            assert "'=formula" in archive.read('csv/memories.csv').decode()
            assert data['tables']['memories'][0]['body'] == '=formula'


@pytest.mark.asyncio
async def test_closure_blocks_sessions_then_erases_only_owner(async_client, auth_headers, other_auth_headers,
                                                          test_user_id, other_user_id, monkeypatch):
    storage = AsyncMock(return_value=1)
    auth_delete = AsyncMock()
    monkeypatch.setattr(StorageService, 'delete_owner_files', storage)
    monkeypatch.setattr('app.services.account.delete_auth_user', auth_delete)
    async with TestingSessionLocal() as db:
        db.add_all([Person(user_id=test_user_id, name='Erase'), Person(user_id=other_user_id, name='Keep')])
        await db.commit()
    assert (await async_client.post('/api/v1/account/delete', headers=auth_headers,
        json={'confirmation':'yes'})).status_code == 422
    response = await async_client.post('/api/v1/account/delete', headers=auth_headers,
        json={'confirmation':'DELETE MY ACCOUNT'})
    assert response.status_code == 202
    assert (await async_client.get('/api/v1/people', headers=auth_headers)).status_code == 401
    assert (await async_client.get('/api/v1/people', headers=other_auth_headers)).status_code == 200
    await close_account(test_user_id)
    storage.assert_awaited_once_with(test_user_id)
    auth_delete.assert_awaited_once_with(test_user_id)
    async with TestingSessionLocal() as db:
        assert [p.name for p in (await db.execute(select(Person))).scalars()] == ['Keep']
        assert (await db.get(AccountClosure, test_user_id)).status == 'completed'
    await close_account(test_user_id)
    storage.assert_awaited_once()


@pytest.mark.asyncio
async def test_storage_failure_does_not_claim_account_erasure(test_user_id, monkeypatch):
    monkeypatch.setattr(StorageService, 'delete_owner_files', AsyncMock(side_effect=RuntimeError('offline')))
    auth_delete = AsyncMock()
    monkeypatch.setattr('app.services.account.delete_auth_user', auth_delete)
    await request_closure(test_user_id)
    with pytest.raises(RuntimeError):
        await close_account(test_user_id)
    auth_delete.assert_not_awaited()
    async with TestingSessionLocal() as db:
        assert (await db.get(AccountClosure, test_user_id)).status != 'completed'
