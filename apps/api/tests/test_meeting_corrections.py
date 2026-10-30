"""Saved detail correction reconciliation; providers and data are synthetic."""
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.ai.indexing import record_text
from app.models.entities import AuditLog, Commitment, ContextEvent, Meeting, Task
from tests.conftest import TestingSessionLocal
from tests.test_meeting_intelligence import (  # noqa: F401
    audio_stub,
    process,
    processing_stub,
    reviewed,
    uploaded,
)

pytestmark = pytest.mark.usefixtures('audio_stub', 'processing_stub')


async def saved(client, headers, owner):
    meeting = await uploaded(client, headers)
    await process(meeting['id'], owner)
    path = '/api/v1/meetings/' + meeting['id']
    response = await client.post(path + '/confirm', headers=headers,
        json=await reviewed(client, headers, path, confirmed=True))
    assert response.status_code == 200, response.text
    return path, response.json()


async def edit_payload(client, headers, path, **overrides):
    preview = await client.get(path + '/corrections', headers=headers)
    assert preview.status_code == 200, preview.text
    state = preview.json()
    return {'request_id': str(uuid4()), 'expected_review_token': state['review_token'],
        'expected_records_token': state['records_token'], 'confirmed': True,
        'candidate_id': 'commitments:0', 'description': 'Send the revised estimate',
        'due_at': '2026-11-15T12:00:00Z', 'reason': 'I corrected the extracted deliverable and agreed date.', **overrides}


async def test_correction_updates_same_record_preserves_source_and_invalidates_summary(async_client, auth_headers, test_user_id):
    path, receipt = await saved(async_client, auth_headers, test_user_id)
    original = (await async_client.get(path, headers=auth_headers)).json()
    payload = await edit_payload(async_client, auth_headers, path)
    response = await async_client.post(path + '/corrections', headers=auth_headers, json=payload)
    assert response.status_code == 200, response.text
    current = (await async_client.get(path, headers=auth_headers)).json()
    assert current['transcript_text'] == original['transcript_text']
    assert current['capture']['transcript_segments'] == original['capture']['transcript_segments']
    assert current['capture']['intelligence']['commitments'][0]['evidence_text'] == 'I will send the report.'
    assert current['metadata']['summary_needs_review']
    assert current['capture']['receipt']['original_intelligence'] == original['capture']['intelligence']
    assert current['capture']['receipt']['corrections'][0]['before']['description'] == 'Send the report'
    async with TestingSessionLocal() as db:
        promise = await db.get(Commitment, receipt['commitments'][0])
        assert promise.description == 'Send the revised estimate'
        assert promise.due_at.date().isoformat() == '2026-11-15'
        assert await db.scalar(select(func.count()).select_from(Commitment)) == 1
        assert await db.scalar(select(func.count()).select_from(Task)) == 1
        meeting = await db.get(Meeting, path.rsplit('/', 1)[1])
        assert 'Owner corrections supersede' in record_text(meeting, 'meeting')
        assert all(row.summary.startswith('Meeting details were corrected') for row in (await db.scalars(select(ContextEvent))).all())
        assert await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.event_type == 'meeting_detail_corrected')) == 1
    export = await async_client.get(path + '/export/markdown', headers=auth_headers)
    assert 'Owner corrections' in export.text and 'Send the revised estimate' in export.text


async def test_retry_is_idempotent_and_modified_retry_conflicts(async_client, auth_headers, test_user_id):
    path, _ = await saved(async_client, auth_headers, test_user_id)
    payload = await edit_payload(async_client, auth_headers, path)
    first = await async_client.post(path + '/corrections', headers=auth_headers, json=payload)
    again = await async_client.post(path + '/corrections', headers=auth_headers, json=payload)
    assert first.status_code == again.status_code == 200
    assert first.json() == again.json()
    wrong = await async_client.post(path + '/corrections', headers=auth_headers, json={**payload, 'description': 'Different edit'})
    assert wrong.status_code == 409


async def test_linked_record_edit_invalidates_correction_preview(async_client, auth_headers, test_user_id):
    path, receipt = await saved(async_client, auth_headers, test_user_id)
    payload = await edit_payload(async_client, auth_headers, path)
    async with TestingSessionLocal() as db:
        promise = await db.get(Commitment, receipt['commitments'][0])
        promise.description = 'Changed in another tab'
        await db.commit()
    response = await async_client.post(path + '/corrections', headers=auth_headers, json=payload)
    assert response.status_code == 409, response.text
    async with TestingSessionLocal() as db:
        assert (await db.get(Commitment, receipt['commitments'][0])).description == 'Changed in another tab'


async def test_foreign_owner_cannot_preview_or_correct(async_client, auth_headers, other_auth_headers, test_user_id):
    path, _ = await saved(async_client, auth_headers, test_user_id)
    payload = await edit_payload(async_client, auth_headers, path)
    assert (await async_client.get(path + '/corrections', headers=other_auth_headers)).status_code == 404
    assert (await async_client.post(path + '/corrections', headers=other_auth_headers, json=payload)).status_code == 404


async def test_closed_commitment_cannot_be_silently_rewritten(async_client, auth_headers, test_user_id):
    path, receipt = await saved(async_client, auth_headers, test_user_id)
    async with TestingSessionLocal() as db:
        promise = await db.get(Commitment, receipt['commitments'][0])
        promise.status = 'completed'
        await db.commit()
    payload = await edit_payload(async_client, auth_headers, path)
    response = await async_client.post(path + '/corrections', headers=auth_headers, json=payload)
    assert response.status_code == 409
    current = (await async_client.get(path, headers=auth_headers)).json()
    assert not current['capture']['receipt'].get('corrections')
