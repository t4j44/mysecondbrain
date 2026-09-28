import io
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import func, select

from app.ai.provider import GeminiLLMProvider
from app.models.entities import (
    ContextEvent,
    ContextMedia,
    EntityEdge,
    Interaction,
    JobRecord,
    Person,
)
from app.services.context_media import compress_photo
from app.services.outreach import composer_url
from tests.conftest import TestingSessionLocal


def event_payload(**values):
    return {'confirmed': True, 'request_id': str(uuid4()), 'title': 'Fundraising meeting',
        'summary': 'Discussed fundraising after reaching paying customers.', 'raw_text': 'Original exact note.',
        'occurred_at': '2026-09-01T09:00:00+06:00', 'timezone': 'Asia/Dhaka', **values}


@pytest.mark.asyncio
async def test_events_time_replay_privacy_export_and_owner(async_client, auth_headers, other_auth_headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    payload = event_payload()
    result = await async_client.post('/api/v1/context-events', headers=auth_headers, json=payload)
    assert result.status_code == 200, result.text
    event = result.json()
    assert event['timezone'] == 'Asia/Dhaka'
    assert datetime.fromisoformat(event['occurred_at']).astimezone(timezone.utc).hour == 3
    replay = await async_client.post('/api/v1/context-events', headers=auth_headers, json=payload)
    assert replay.json()['id'] == event['id']
    assert (await async_client.get('/api/v1/context-events/' + event['id'], headers=other_auth_headers)).status_code == 404
    assert (await async_client.get('/api/v1/context-events', headers=other_auth_headers)).json() == []
    query = await async_client.post('/api/v1/ai/search', headers=auth_headers, json={'query': 'fundraising'})
    assert any(row['id'] == event['id'] for row in query.json()['results'])
    restricted = await async_client.post('/api/v1/context-events', headers=auth_headers, json=event_payload(privacy_class='restricted', summary='Quasar restricted context'))
    query = await async_client.post('/api/v1/ai/search', headers=auth_headers, json={'query': 'Quasar'})
    assert query.json()['total_matches'] == 0
    assert (await async_client.get('/api/v1/context-events/' + restricted.json()['id'], headers=auth_headers)).status_code == 200
    await async_client.delete('/api/v1/context-events/' + event['id'], headers=auth_headers)
    assert (await async_client.post('/api/v1/context-events', headers=auth_headers, json=payload)).status_code == 409


@pytest.mark.asyncio
async def test_event_rejects_cross_owner_reference_and_naive_time(async_client, auth_headers, other_auth_headers):
    person = (await async_client.post('/api/v1/people', headers=other_auth_headers, json={'name': 'Other owner'})).json()
    result = await async_client.post('/api/v1/context-events', headers=auth_headers, json=event_payload(person_id=person['id']))
    assert result.status_code == 404
    for change in ({'occurred_at': '2026-09-01T09:00:00'}, {'timezone': 'not/a-zone'}, {'confirmed': False}):
        response = await async_client.post('/api/v1/context-events', headers=auth_headers, json=event_payload(**change))
        assert response.status_code == 422


def make_photo():
    output = io.BytesIO()
    photo = Image.new('RGB', (1800, 1200), 'white')
    exif = Image.Exif()
    exif[270] = 'Private original metadata'
    photo.save(output, 'JPEG', exif=exif)
    return output.getvalue()


def test_compression_removes_metadata_and_bounds_images():
    photo, thumb, dimensions = compress_photo(make_photo())
    assert max(dimensions) <= 1600 and len(photo) <= 500 * 1024
    for content, edge in ((photo, 1600), (thumb, 320)):
        with Image.open(io.BytesIO(content)) as image:
            assert max(image.size) <= edge and not image.getexif()
    from app.core.errors import ConflictError
    with pytest.raises(ConflictError):
        compress_photo(b'not an image')


@pytest.mark.asyncio
async def test_capture_photo_event_replay_and_erasure(async_client, auth_headers, other_auth_headers, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    draft = (await async_client.post('/api/v1/capture/propose', headers=auth_headers,
        json={'text': 'Ahmed discussed fundraising at the AI summit.'})).json()
    path = '/api/v1/capture/' + draft['draft_id']
    upload_id = str(uuid4())
    def form():
        return {'data': {'request_id': upload_id, 'kind': 'business_card'}, 'files': {'file': ('card.jpg', make_photo(), 'image/jpeg')}}
    assert (await async_client.post(path + '/media', headers=other_auth_headers, **form())).status_code == 404
    media = await async_client.post(path + '/media', headers=auth_headers, **form())
    assert media.status_code == 200, media.text
    assert (await async_client.post(path + '/media', headers=auth_headers, **form())).json() == media.json()
    photo_path = '/api/v1/capture/media/' + media.json()['id']
    assert (await async_client.get(photo_path, headers=other_auth_headers)).status_code == 404
    image = await async_client.get(photo_path, headers=auth_headers)
    assert image.status_code == 200 and image.headers['cache-control'] == 'private, no-store'
    saved = await async_client.post(path + '/confirm', headers=auth_headers, json={'confirmed': True,
        'event_type': 'business_card_scan', 'occurred_at': '2026-09-01T10:00:00Z',
        'proposal': {**draft['proposal'], 'person_name': 'Ahmed', 'topics': ['fundraising']}})
    assert saved.status_code == 200, saved.text
    event_id = saved.json()['context_event_id']
    async with TestingSessionLocal() as db:
        row = await db.scalar(select(ContextMedia))
        assert str(row.event_id) == event_id
    person_id = next(row['id'] for row in saved.json()['records'] if row['type'] == 'person')
    profile = (await async_client.get('/api/v1/relationships/people/' + person_id, headers=auth_headers)).json()
    assert profile['moments'][0]['media'][0]['id'] == media.json()['id']
    removed = await async_client.delete('/api/v1/context-events/' + event_id, headers=auth_headers)
    assert removed.status_code == 200, removed.text
    assert (await async_client.get(photo_path, headers=auth_headers)).status_code == 404
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(ContextMedia)) == 0
        assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type == 'storage_delete')) == 2
        assert await db.scalar(select(func.count()).select_from(EntityEdge).where(EntityEdge.source_event_id == event_id)) == 0
        assert (await db.scalar(select(Interaction))).deleted_at is not None
        assert (await db.scalar(select(ContextEvent))).raw_text is None


@pytest.mark.parametrize('phone', ['01712345678', '123', '+012345678', '+880123abc'])
def test_whatsapp_requires_explicit_country_code(phone):
    from app.core.errors import ConflictError
    with pytest.raises(ConflictError):
        composer_url('whatsapp', phone, None, 'hello')


def test_outreach_encodes_reviewed_text():
    from urllib.parse import parse_qs, urlparse
    message = 'Hello Ahmed! A&B + funding?\nবাংলা'
    whatsapp = urlparse(composer_url('whatsapp', '+880 1712-345678', None, message))
    assert whatsapp.netloc == 'wa.me' and whatsapp.path == '/8801712345678'
    assert parse_qs(whatsapp.query)['text'] == [message]
    email = urlparse(composer_url('email', None, 'a+test@example.com', message, 'A&B?'))
    assert parse_qs(email.query) == {'subject': ['A&B?'], 'body': [message]}


@pytest.mark.asyncio
async def test_open_is_not_sent_and_confirmation_is_idempotent(async_client, auth_headers, other_auth_headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    person = (await async_client.post('/api/v1/people', headers=auth_headers,
        json={'name': 'Ahmed', 'phone': '+8801712345678'})).json()
    prefix = '/api/v1/relationships/people/' + person['id'] + '/outreach/'
    opened = await async_client.post(prefix + 'open', headers=auth_headers, json={
        'confirmed': True, 'request_id': str(uuid4()), 'channel': 'whatsapp', 'message': 'Reviewed fundraising update'})
    assert opened.status_code == 200, opened.text
    assert opened.json()['sent'] is False
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Interaction)) == 0
        assert (await db.scalar(select(Person))).last_interaction_at is None
    sent = {'confirmed': True, 'request_id': str(uuid4()), 'opened_id': opened.json()['id'], 'outcome': 'Sent my fundraising update.'}
    assert (await async_client.post(prefix + 'sent', headers=other_auth_headers, json=sent)).status_code == 404
    confirmed = await async_client.post(prefix + 'sent', headers=auth_headers, json=sent)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()['sent'] is True
    sent['request_id'] = str(uuid4())
    assert (await async_client.post(prefix + 'sent', headers=auth_headers, json=sent)).json() == confirmed.json()
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Interaction)) == 1
        assert await db.scalar(select(func.count()).select_from(ContextEvent)) == 1
        assert (await db.scalar(select(Person))).last_interaction_at is not None
    event_id = confirmed.json()['context_event_id']
    assert (await async_client.delete('/api/v1/context-events/' + event_id, headers=auth_headers)).status_code == 200
    assert (await async_client.post(prefix + 'sent', headers=auth_headers, json=sent)).status_code == 409
    async with TestingSessionLocal() as db:
        assert (await db.scalar(select(Person))).last_interaction_at is None


@pytest.mark.asyncio
async def test_contact_literals_stay_server_side_when_ai_unavailable(async_client, auth_headers, monkeypatch):
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    note = 'Ahmed\nahmed@example.com\n+880 1712-345678\nhttps://www.linkedin.com/in/synthetic-ahmed'
    result = await async_client.post('/api/v1/capture/propose', headers=auth_headers, json={'text': note, 'source': 'image_text'})
    assert result.status_code == 200
    proposal = result.json()['proposal']
    assert proposal['email'] == 'ahmed@example.com'
    assert proposal['phone'] == '+880 1712-345678'
    assert proposal['linkedin_url'] == 'https://www.linkedin.com/in/synthetic-ahmed'


@pytest.mark.asyncio
async def test_removed_pending_photo_is_not_attached_by_confirmation(async_client, auth_headers, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(GeminiLLMProvider, '_is_unconfigured', lambda self: True)
    draft = (await async_client.post('/api/v1/capture/propose', headers=auth_headers, json={'text': 'Synthetic moment.'})).json()
    path = '/api/v1/capture/' + draft['draft_id']
    uploaded = await async_client.post(path + '/media', headers=auth_headers,
        data={'kind': 'moment', 'request_id': str(uuid4())}, files={'file': ('moment.jpg', make_photo(), 'image/jpeg')})
    assert uploaded.status_code == 200
    saved = await async_client.post(path + '/confirm', headers=auth_headers,
        json={'confirmed': True, 'proposal': draft['proposal'], 'media_ids': []})
    assert saved.status_code == 200, saved.text
    assert (await async_client.get('/api/v1/capture/media/' + uploaded.json()['id'], headers=auth_headers)).status_code == 404
