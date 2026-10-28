from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.ai.structured import structured_answer
from app.integrations.storage_client import StorageService
from app.models.assistant import CommitmentAction
from app.models.entities import AuditLog, Commitment, EntityEdge, Task
from app.services.account import close_account, request_closure
from tests.conftest import TestingSessionLocal


async def create(client, headers, **values):
    response = await client.post('/api/v1/commitments', headers=headers,
        json={'description': 'Send the reviewed proposal', 'direction': 'owed_by_me', **values})
    assert response.status_code == 201, response.text
    return response.json()


async def test_unfinished_states_remain_in_source_backed_answers(async_client, auth_headers, test_user_id):
    working = await create(async_client, auth_headers)
    snoozed = await create(async_client, auth_headers)
    assert (await act(async_client, auth_headers, working, payload(working, 'working'))).status_code == 200
    assert (await act(async_client, auth_headers, snoozed, payload(snoozed, 'snooze',
        snoozed_until=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), timezone='Asia/Dhaka'))).status_code == 200
    async with TestingSessionLocal() as db:
        answer = await structured_answer(db, test_user_id, 'Show open commitments')
        assert answer['provider_used'] == 'database'
        assert set(answer['source_citations']) == {working['id'], snoozed['id']}


async def test_erasure_removes_only_owner_action_receipts(async_client, auth_headers, other_auth_headers,
                                                         test_user_id, other_user_id, monkeypatch):
    monkeypatch.setattr(StorageService, 'delete_owner_files', AsyncMock(return_value=0))
    auth_delete = AsyncMock()
    monkeypatch.setattr('app.services.account.delete_auth_user', auth_delete)
    for headers in (auth_headers, other_auth_headers):
        row = await create(async_client, headers)
        assert (await act(async_client, headers, row, payload(row, 'done'))).status_code == 200
    await request_closure(test_user_id)
    await close_account(test_user_id)
    auth_delete.assert_awaited_once_with(test_user_id)
    async with TestingSessionLocal() as db:
        rows = (await db.scalars(select(CommitmentAction))).all()
        assert len(rows) == 1 and str(rows[0].user_id) == other_user_id


def payload(row, action, **values):
    return {'expected_revision': row['revision'], 'request_id': str(uuid4()), 'action': action, **values}


async def act(client, headers, row, data):
    return await client.post(f"/api/v1/commitments/{row['id']}/action", headers=headers, json=data)


async def test_done_is_self_confirmed_and_identical_retry_has_one_receipt(async_client, auth_headers):
    row = await create(async_client, auth_headers)
    data = payload(row, 'done')
    first = await act(async_client, auth_headers, row, data)
    assert first.status_code == 200, first.text
    assert first.headers['cache-control'] == 'private, no-store'
    assert first.json()['self_reported'] is True
    assert first.json()['commitment']['status'] == 'completed'
    assert first.json()['commitment']['revision'] == row['revision'] + 1
    assert (await act(async_client, auth_headers, row, data)).json() == first.json()
    assert (await act(async_client, auth_headers, row, {**data, 'action': 'working'})).status_code == 409
    async with TestingSessionLocal() as db:
        assert len((await db.scalars(select(CommitmentAction))).all()) == 1
        assert len((await db.scalars(select(AuditLog).where(AuditLog.event_type == 'commitment_action'))).all()) == 1


async def test_old_revision_after_legacy_edit_conflicts_and_foreign_owner_stays_hidden(async_client, auth_headers, other_auth_headers):
    row = await create(async_client, auth_headers)
    updated = await async_client.patch(f"/api/v1/commitments/{row['id']}", headers=auth_headers, json={'description': 'Corrected promise'})
    assert updated.status_code == 200, updated.text
    assert updated.json()['revision'] == row['revision'] + 1
    assert (await act(async_client, auth_headers, row, payload(row, 'done'))).status_code == 409
    assert (await act(async_client, other_auth_headers, row, payload(row, 'done'))).status_code == 404
    assert (await act(async_client, {}, row, payload(row, 'done'))).status_code == 401


async def test_snooze_preserves_deadline_and_requires_explicit_zone_and_future_time(async_client, auth_headers):
    due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    row = await create(async_client, auth_headers, due_at=due)
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    for invalid in ({}, {'snoozed_until': future}, {'snoozed_until': future, 'timezone': 'Unknown/Zone'},
                    {'snoozed_until': '2027-01-01T10:00:00', 'timezone': 'UTC'}):
        assert (await act(async_client, auth_headers, row, payload(row, 'snooze', **invalid))).status_code == 422
    old = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    assert (await act(async_client, auth_headers, row, payload(row, 'snooze', snoozed_until=old, timezone='UTC'))).status_code == 400
    response = await act(async_client, auth_headers, row, payload(row, 'snooze', snoozed_until=future, timezone='Asia/Dhaka'))
    assert response.status_code == 200, response.text
    result = response.json()['commitment']
    assert result['status'] == 'snoozed' and result['source_timezone'] == 'Asia/Dhaka'
    assert datetime.fromisoformat(result['due_at'].replace('Z', '+00:00')).replace(tzinfo=None) == datetime.fromisoformat(due).replace(tzinfo=None)
    assert result['reminder_at'] is not None


async def test_working_remains_in_active_ledger_and_help_never_changes_progress(async_client, auth_headers):
    row = await create(async_client, auth_headers)
    response = await act(async_client, auth_headers, row, payload(row, 'working'))
    row = response.json()['commitment']
    active = await async_client.get('/api/v1/commitments?commitment_status=active', headers=auth_headers)
    assert active.status_code == 200 and active.json()[0]['status'] == 'in_progress'
    result = (await act(async_client, auth_headers, row, payload(row, 'help'))).json()
    assert result['commitment']['revision'] == row['revision']
    assert result['commitment']['status'] == 'in_progress' and not result['self_reported']
    assert result['help']['label'] == 'Draft to review'
    assert result['help']['sources'][0]['uri'] == f"/sources/commitment/{row['id']}"


async def test_deleted_commitment_cannot_replay_receipt(async_client, auth_headers):
    row = await create(async_client, auth_headers)
    data = payload(row, 'help')
    assert (await act(async_client, auth_headers, row, data)).status_code == 200
    assert (await async_client.delete(f"/api/v1/commitments/{row['id']}", headers=auth_headers)).status_code == 204
    assert (await act(async_client, auth_headers, row, data)).status_code == 404


async def test_shared_task_is_done_only_after_all_linked_promises(async_client, auth_headers, test_user_id):
    rows = [await create(async_client, auth_headers) for _ in range(2)]
    async with TestingSessionLocal() as db:
        task = Task(user_id=test_user_id, title='Fulfil both promises')
        db.add(task)
        await db.flush()
        identity = task.id
        for row in rows:
            db.add(EntityEdge(user_id=test_user_id, source_entity_type='task', source_entity_id=identity,
                target_entity_type='commitment', target_entity_id=row['id'], relationship_type='fulfills'))
        await db.commit()
    for index, row in enumerate(rows):
        response = await act(async_client, auth_headers, row, payload(row, 'done'))
        assert response.status_code == 200, response.text
        async with TestingSessionLocal() as db:
            assert (await db.get(Task, identity)).status == ('todo' if index == 0 else 'done')


@pytest.mark.parametrize('value', [0, -1, True])
async def test_actions_require_a_real_reviewed_revision(async_client, auth_headers, value):
    row = await create(async_client, auth_headers)
    assert (await act(async_client, auth_headers, row, payload(row, 'done', expected_revision=value))).status_code == 422


async def test_same_request_id_cannot_be_reused_on_another_commitment(async_client, auth_headers):
    first, second = await create(async_client, auth_headers), await create(async_client, auth_headers)
    data = payload(first, 'help')
    await act(async_client, auth_headers, first, data)
    assert (await act(async_client, auth_headers, second, data)).status_code == 409
    async with TestingSessionLocal() as db:
        assert (await db.get(Commitment, second['id'])).status == 'open'
