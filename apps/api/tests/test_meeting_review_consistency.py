"""Review snapshots bind consent to the actual proposals; no real providers."""
import pytest
from sqlalchemy import func, select

from app.models.entities import Commitment, ContextEvent, Task
from app.models.meeting_intelligence import MeetingCapture
from tests.conftest import TestingSessionLocal
from tests.test_meeting_intelligence import (  # noqa: F401
    audio_stub,
    process,
    processing_stub,
    reviewed,
    uploaded,
)

pytestmark = pytest.mark.usefixtures('audio_stub', 'processing_stub')


async def ready(client, headers, owner):
    meeting = await uploaded(client, headers)
    await process(meeting['id'], owner)
    return '/api/v1/meetings/' + meeting['id']


async def assert_no_canonical_writes():
    async with TestingSessionLocal() as db:
        for model in (Commitment, Task, ContextEvent):
            assert await db.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.parametrize('change', ['speaker', 'context', 'proposal'])
async def test_stale_review_cannot_confirm_changed_meaning(async_client, auth_headers, test_user_id, change):
    path = await ready(async_client, auth_headers, test_user_id)
    original = await reviewed(async_client, auth_headers, path, confirmed=True)
    if change == 'speaker':
        result = await async_client.post(path + '/speakers', headers=auth_headers,
            json={**original, 'speaker': 'c0:spk_1', 'kind': 'me'})
        assert result.status_code == 200, result.text
    elif change == 'context':
        result = await async_client.put(path + '/review', headers=auth_headers,
            json={'expected_version': 0, 'expected_review_token': original['expected_review_token'],
                'title': 'Revised meeting context', 'timezone': 'Asia/Dhaka'})
        assert result.status_code == 200, result.text
    else:
        async with TestingSessionLocal() as db:
            capture = await db.get(MeetingCapture, path.rsplit('/', 1)[1])
            capture.intelligence = {**capture.intelligence, 'commitments': []}
            await db.commit()
    rejected = await async_client.post(path + '/confirm', headers=auth_headers, json=original)
    assert rejected.status_code == 409, rejected.text
    await assert_no_canonical_writes()
    current = await reviewed(async_client, auth_headers, path, confirmed=True)
    assert current['expected_review_token'] != original['expected_review_token']
    accepted = await async_client.post(path + '/confirm', headers=auth_headers, json=current)
    assert accepted.status_code == 200, accepted.text


async def test_same_request_replays_but_different_selection_conflicts(async_client, auth_headers, test_user_id):
    path = await ready(async_client, auth_headers, test_user_id)
    payload = await reviewed(async_client, auth_headers, path, confirmed=True, selections=['commitments:0'])
    first = await async_client.post(path + '/confirm', headers=auth_headers, json=payload)
    assert first.status_code == 200, first.text
    same = await async_client.post(path + '/confirm', headers=auth_headers, json=payload)
    assert same.status_code == 200 and same.json() == first.json()
    changed = await async_client.post(path + '/confirm', headers=auth_headers, json={**payload, 'selections': []})
    assert changed.status_code == 409, changed.text
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Commitment)) == 1
        assert await db.scalar(select(func.count()).select_from(Task)) == 0


async def test_missing_snapshot_fails_closed_and_notes_do_not_change_consent(async_client, auth_headers, test_user_id):
    path = await ready(async_client, auth_headers, test_user_id)
    payload = await reviewed(async_client, auth_headers, path, confirmed=True)
    for suffix, method, body in (
        ('/confirm', 'post', {'confirmed': True}),
        ('/speakers', 'post', {'speaker': 'c0:spk_1', 'kind': 'me', 'confirmed': True}),
        ('/review', 'put', {'expected_version': 0, 'title': 'Unreviewed rename'}),
    ):
        response = await getattr(async_client, method)(path + suffix, headers=auth_headers, json=body)
        assert response.status_code == 409, response.text
    await assert_no_canonical_writes()
    notes = await async_client.put(path + '/notes', headers=auth_headers,
        json={'expected_version': 0, 'markdown': 'Personal notes do not change source proposals.'})
    assert notes.status_code == 200, notes.text
    assert (await reviewed(async_client, auth_headers, path, confirmed=True)) == payload


async def test_stale_speaker_and_context_edits_are_rejected(async_client, auth_headers, test_user_id):
    path = await ready(async_client, auth_headers, test_user_id)
    old = await reviewed(async_client, auth_headers, path)
    changed = await async_client.post(path + '/speakers', headers=auth_headers,
        json={**old, 'speaker': 'c0:spk_1', 'kind': 'me', 'confirmed': True})
    assert changed.status_code == 200, changed.text
    stale = await async_client.post(path + '/speakers', headers=auth_headers,
        json={**old, 'speaker': 'c0:spk_1', 'kind': 'unknown', 'confirmed': True})
    assert stale.status_code == 409, stale.text
    stale_context = await async_client.put(path + '/review', headers=auth_headers,
        json={**old, 'expected_version': 0, 'title': 'Old context'})
    assert stale_context.status_code == 409, stale_context.text
    current = (await async_client.get(path, headers=auth_headers)).json()
    assert current['capture']['speaker_mappings']['c0:spk_1']['kind'] == 'me'
