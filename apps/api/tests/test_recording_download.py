"""Actual local storage bytes and API authorization; not hosted RLS proof."""
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.models.meeting_intelligence import MeetingCapture
from app.services.meeting_audio import MIMES, AudioStorage
from tests.conftest import TestingSessionLocal
from tests.test_meeting_intelligence import capture


async def stored_recording(client, headers, tmp_path, monkeypatch, mime='audio/webm'):
    # Bind storage to a test-owned folder without touching a hosted bucket.
    original = AudioStorage.__init__
    def local_storage(self):
        original(self)
        self.use_supabase = False
        self.base_path = str(tmp_path)
    monkeypatch.setattr(AudioStorage, '__init__', local_storage)
    meeting = await capture(client, headers)
    endpoint = f'/api/v1/meetings/{meeting["id"]}'
    response = await client.post(endpoint + '/upload-authorization', headers=headers, json={'mime_type': mime})
    assert response.status_code == 200, response.text
    async with TestingSessionLocal() as db:
        row = await db.get(MeetingCapture, meeting['id'])
        target = Path(tmp_path) / row.audio_path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = bytes(range(256)) * 29
        target.write_bytes(content)
        row.retained_until = datetime.now(timezone.utc) + timedelta(days=1)
        await db.commit()
    return meeting['id'], endpoint, content


@pytest.mark.parametrize('mime', list(MIMES))
async def test_download_preserves_original_bytes_mime_and_safe_filename(async_client, auth_headers, tmp_path, monkeypatch, mime):
    identity, endpoint, content = await stored_recording(async_client, auth_headers, tmp_path, monkeypatch, mime)
    for _ in range(2):
        response = await async_client.get(endpoint + '/recording/download', headers=auth_headers)
        assert response.status_code == 200, response.text
        assert hashlib.sha256(response.content).digest() == hashlib.sha256(content).digest()
        assert response.headers['content-type'] == mime
        assert response.headers['content-disposition'] == f'attachment; filename="meeting-{identity}{MIMES[mime]}"'
        assert response.headers['cache-control'] == 'private, no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['content-length'] == str(len(content))


async def test_download_denies_other_account_and_anonymous_before_storage(async_client, auth_headers, other_auth_headers, tmp_path, monkeypatch):
    _, endpoint, _ = await stored_recording(async_client, auth_headers, tmp_path, monkeypatch)
    async def forbidden_read(*args):
        pytest.fail('Unauthorized request reached private storage')
    monkeypatch.setattr(AudioStorage, 'read_bounded', forbidden_read)
    assert (await async_client.get(endpoint + '/recording/download', headers=other_auth_headers)).status_code == 404
    assert (await async_client.get(endpoint + '/recording/download')).status_code == 401


@pytest.mark.parametrize('state', ['expired', 'deleted', 'missing', 'wrong_owner'])
async def test_unavailable_recordings_never_reach_storage(async_client, auth_headers, tmp_path, monkeypatch, state):
    identity, endpoint, _ = await stored_recording(async_client, auth_headers, tmp_path, monkeypatch)
    async with TestingSessionLocal() as db:
        row = await db.get(MeetingCapture, identity)
        if state == 'expired':
            row.retained_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        if state == 'deleted':
            row.audio_deleted_at = datetime.now(timezone.utc)
        if state == 'missing':
            row.audio_path = None
        if state == 'wrong_owner':
            row.audio_path = 'another-owner/private.webm'
        await db.commit()
    async def forbidden_read(*args):
        pytest.fail('Unavailable recording reached private storage')
    monkeypatch.setattr(AudioStorage, 'read_bounded', forbidden_read)
    for suffix in ['/recording', '/recording/download']:
        assert (await async_client.get(endpoint + suffix, headers=auth_headers)).status_code == 409


async def test_playback_link_cannot_outlive_retention(async_client, auth_headers, tmp_path, monkeypatch):
    identity, endpoint, _ = await stored_recording(async_client, auth_headers, tmp_path, monkeypatch)
    async with TestingSessionLocal() as db:
        row = await db.get(MeetingCapture, identity)
        row.retained_until = datetime.now(timezone.utc) + timedelta(seconds=45)
        await db.commit()
    def hosted_storage(self):
        self.use_supabase = True
    async def sign(self, path, ttl):
        assert 1 <= ttl <= 45
        return 'https://storage.example.invalid/synthetic-short-lived'
    monkeypatch.setattr(AudioStorage, '__init__', hosted_storage)
    monkeypatch.setattr(AudioStorage, 'get_signed_url', sign)
    response = await async_client.get(endpoint + '/recording', headers=auth_headers)
    assert response.status_code == 200
    assert 1 <= response.json()['expires_seconds'] <= 45


async def test_meeting_deletion_denies_download(async_client, auth_headers, tmp_path, monkeypatch):
    _, endpoint, _ = await stored_recording(async_client, auth_headers, tmp_path, monkeypatch)
    assert (await async_client.delete(endpoint, headers=auth_headers)).status_code == 204
    assert (await async_client.get(endpoint + '/recording/download', headers=auth_headers)).status_code == 404
