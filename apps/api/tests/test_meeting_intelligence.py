"""Mocked-provider API acceptance; real RLS/concurrency lives in PostgreSQL suite."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.ai.meeting_provider import GeminiMeetingProvider, extract_intelligence, parse_transcription
from app.ai.provider import GeminiLLMProvider
from app.core.config import settings
from app.core.errors import AIProviderError
from app.models.entities import Commitment, ContextEvent, Interaction, JobRecord, Meeting, Task
from app.models.meeting_intelligence import MeetingCapture
from app.schemas.meeting_intelligence import Candidate, MeetingIntelligence
from app.services.meeting_audio import AudioStorage, audio_mime
from app.services.meeting_intelligence import expire_audio
from app.services.meeting_usage import month_start, quota_view
from tests.conftest import TestingSessionLocal


async def capture(client, headers, request_id=None):
    response = await client.post('/api/v1/meetings/captures', headers=headers, json={
        'request_id': request_id or str(uuid4()), 'title': 'Customer meeting',
        'meeting_date': datetime.now(timezone.utc).isoformat(),
        'recording_permission': True, 'provider_terms_accepted': True, 'non_sensitive_recording': True})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def audio_stub(monkeypatch):
    async def authorize(self, owner, meeting_id, mime):
        return f'{owner}/{meeting_id}-synthetic.webm', None
    async def read(self, path):
        return b'synthetic-private-audio'
    async def inspect(content, mime):
        return 17
    monkeypatch.setattr(AudioStorage, 'authorize', authorize)
    monkeypatch.setattr(AudioStorage, 'read_bounded', read)
    monkeypatch.setattr('app.services.meeting_intelligence.inspect_audio', inspect)


async def uploaded(client, headers):
    meeting = await capture(client, headers)
    path = f'/api/v1/meetings/{meeting["id"]}'
    auth = await client.post(path+'/upload-authorization', headers=headers, json={'mime_type': 'audio/webm;codecs=opus'})
    assert auth.status_code == 200
    response = await client.post(path+'/finalize-upload', headers=headers, json={'duration_seconds': 99999})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize('value,expected', [('audio/mp3','audio/mpeg'), ('audio/x-m4a','audio/mp4'), ('audio/m4a','audio/mp4'),
    ('audio/wav','audio/wav'), ('audio/webm;codecs=opus','audio/webm'), ('audio/opus','audio/opus'),
    ('audio/flac','audio/flac'), ('audio/aac','audio/aac'), ('audio/ogg','audio/ogg')])
def test_audio_aliases(value, expected):
    assert audio_mime(value) == expected


@pytest.mark.parametrize('mime', ['text/plain', 'video/mp4', 'image/png', 'application/octet-stream'])
def test_rejects_non_audio_mime(mime):
    from app.core.errors import ValidationError as UploadError
    with pytest.raises(UploadError):
        audio_mime(mime)


async def test_capture_and_finalize_replays_do_not_duplicate_or_double_charge(async_client, auth_headers, audio_stub):
    request_id = str(uuid4())
    first = await capture(async_client, auth_headers, request_id)
    second = await capture(async_client, auth_headers, request_id)
    assert first['id'] == second['id'] and first['capture']['state'] == 'draft'
    assert 'audio_path' not in first['capture']
    path = f'/api/v1/meetings/{first["id"]}'
    await async_client.post(path+'/upload-authorization', headers=auth_headers, json={'mime_type':'audio/webm'})
    for _ in range(2):
        result = await async_client.post(path+'/finalize-upload', headers=auth_headers)
        assert result.status_code == 200, result.text
    usage = (await async_client.get('/api/v1/meetings/usage', headers=auth_headers)).json()
    assert usage['used_seconds'] == 17 and usage['remaining_seconds'] == 17983
    listed = (await async_client.get('/api/v1/meetings', headers=auth_headers)).json()
    assert listed['total'] == 1 and listed['items'][0]['meeting_date']
    assert listed['items'][0]['capture']['state'] == 'uploaded'
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type == 'meeting_processing')) == 1


async def test_meeting_participants_use_canonical_junction(async_client, auth_headers, other_auth_headers):
    person = (await async_client.post('/api/v1/people', headers=auth_headers, json={'name':'Sarah'})).json()
    response = await async_client.post('/api/v1/meetings', headers=auth_headers, json={'title':'Notes',
        'meeting_date':datetime.now(timezone.utc).isoformat(), 'participant_person_ids':[person['id'],person['id']]})
    assert response.status_code == 201, response.text
    meeting = response.json()
    assert meeting['participant_person_ids'] == [person['id']]
    assert (await async_client.get('/api/v1/meetings/'+meeting['id'], headers=other_auth_headers)).status_code == 404
    response = await async_client.patch('/api/v1/meetings/'+meeting['id'], headers=auth_headers, json={'participant_person_ids': []})
    assert response.status_code == 200 and response.json()['participant_person_ids'] == []


@pytest.mark.parametrize('suffix,method,body', [('', 'get', None), ('/recording','get',None),
    ('/retry','post',None), ('/finalize-upload','post',None), ('/upload-authorization','post',{'mime_type':'audio/wav'}),
    ('/speakers','post',{'speaker':'c0:spk_1','kind':'me','confirmed':True}), ('/confirm','post',{'confirmed':True})])
async def test_other_user_cannot_read_or_mutate_capture(async_client, auth_headers, other_auth_headers, suffix, method, body):
    meeting = await capture(async_client, auth_headers)
    response = await getattr(async_client, method)('/api/v1/meetings/'+meeting['id']+suffix, headers=other_auth_headers,
        **({'json':body} if body is not None else {}))
    assert response.status_code == 404, response.text


async def test_quota_uses_measured_duration_and_fails_without_charge(async_client, auth_headers, audio_stub, monkeypatch):
    monkeypatch.setattr(settings, 'MEETING_AUDIO_MONTHLY_LIMIT_SECONDS', 20)
    await uploaded(async_client, auth_headers)
    meeting = await capture(async_client, auth_headers)
    path = '/api/v1/meetings/'+meeting['id']
    await async_client.post(path+'/upload-authorization', headers=auth_headers, json={'mime_type':'audio/webm'})
    assert (await async_client.post(path+'/finalize-upload', headers=auth_headers)).status_code == 429
    assert (await async_client.get('/api/v1/meetings/usage', headers=auth_headers)).json()['used_seconds'] == 17


async def test_failed_inspection_does_not_charge_or_queue(async_client, auth_headers, audio_stub, monkeypatch):
    async def invalid(*args):
        from app.core.errors import ValidationError as UploadError
        raise UploadError('Invalid audio')
    monkeypatch.setattr('app.services.meeting_intelligence.inspect_audio', invalid)
    meeting = await capture(async_client, auth_headers)
    path = '/api/v1/meetings/'+meeting['id']
    await async_client.post(path+'/upload-authorization', headers=auth_headers, json={'mime_type':'audio/webm'})
    assert (await async_client.post(path+'/finalize-upload', headers=auth_headers)).status_code == 400
    assert (await async_client.get('/api/v1/meetings/usage', headers=auth_headers)).json()['used_seconds'] == 0


def test_calendar_month_is_utc():
    from zoneinfo import ZoneInfo
    assert month_start(datetime(2026, 11, 1, 1, tzinfo=ZoneInfo('Asia/Dhaka'))) == datetime(2026, 10, 1, tzinfo=timezone.utc)


async def test_new_month_counter_resets_view(async_client, auth_headers, audio_stub, monkeypatch, test_user_id):
    await uploaded(async_client, auth_headers)
    monkeypatch.setattr('app.services.meeting_usage.month_start', lambda: datetime(2026,12,1,tzinfo=timezone.utc))
    async with TestingSessionLocal() as db:
        assert (await quota_view(db, test_user_id))['used_seconds'] == 0


def test_diarization_speakers_are_chunk_local_and_offsets_absolute():
    response = {'steps':[{'content':[{'type':'text','text':'Hello', 'annotations':[
        {'type':'word_info','text':'Hello','speaker':'spk_1','start_offset':'1.2s','end_offset':'1.8s'}]}]}]}
    a, b = parse_transcription(response, 0, 0)[0], parse_transcription(response, 1, 1740)[0]
    assert a['speaker_local_id'] != b['speaker_local_id']
    assert b['start_offset'] == 1741.2 and not b['identity_resolved']


def test_candidate_cannot_invent_deadline_without_evidence():
    with pytest.raises(ValidationError):
        Candidate(description='Send recap', evidence_text='send recap', confidence=.9, due_at='2026-10-10T00:00:00Z')


@pytest.mark.parametrize('output', ['not json', '{"summary":"done","extra":"secret"}',
    '{"summary":"done","commitments":[{"description":"Help","evidence_text":"made up","confidence":0.9}]}'])
async def test_malformed_or_unsupported_ai_details_fail(output, monkeypatch):
    async def generate(*args, **kwargs):
        return output
    monkeypatch.setattr(GeminiLLMProvider, 'generate_content', generate)
    with pytest.raises(AIProviderError):
        await extract_intelligence('actual words', date='2026-10-08', speakers=['c0:spk_1'])


@pytest.fixture
def processing_stub(monkeypatch):
    async def chunks(*args):
        yield 0, 0, Path('synthetic.flac')
    async def transcribe(*args):
        return [{'segment_id':'c0:0','chunk_index':0,'speaker_local_id':'c0:spk_1','start_offset':0.,'end_offset':5.,'text':'I will send the report.', 'identity_resolved':False},
            {'segment_id':'c0:1','chunk_index':0,'speaker_local_id':'c0:spk_2','start_offset':5.,'end_offset':10.,'text':'We decided to test the beta.', 'identity_resolved':False}]
    async def extract(*args, **kwargs):
        return MeetingIntelligence(summary='Discussed beta and report', commitments=[Candidate(description='Send the report',
            evidence_text='I will send the report.', confidence=.93, from_speaker='c0:spk_1', to_speaker='c0:spk_2')],
            action_items=[Candidate(description='Send report', evidence_text='I will send the report.', confidence=.9)],
            decisions=[Candidate(description='Test the beta', evidence_text='We decided to test the beta.', confidence=.9)])
    monkeypatch.setattr('app.jobs.handlers.meeting_processing.audio_chunks', chunks)
    monkeypatch.setattr(GeminiMeetingProvider, 'transcribe', transcribe)
    monkeypatch.setattr('app.jobs.handlers.meeting_processing.extract_intelligence', extract)


async def process(meeting_id, owner):
    from app.jobs.handlers.meeting_processing import process_meeting
    async with TestingSessionLocal() as db:
        return await process_meeting(db, owner, {'meeting_id':meeting_id,'processing_version':1})


async def test_end_to_end_review_confirmation_and_retry_once(async_client, auth_headers, audio_stub, processing_stub, test_user_id):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting['id'], test_user_id)
    await process(meeting['id'], test_user_id)
    path = '/api/v1/meetings/'+meeting['id']
    ready = (await async_client.get(path, headers=auth_headers)).json()
    assert ready['capture']['state'] == 'awaiting_review' and ready['transcript_text']
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Commitment)) == 0
    person = (await async_client.post('/api/v1/people', headers=auth_headers, json={'name':'Sarah'})).json()
    assert (await async_client.post(path+'/speakers', headers=auth_headers, json={'speaker':'c0:spk_1','kind':'me','confirmed':True})).status_code == 200
    assert (await async_client.post(path+'/speakers', headers=auth_headers, json={'speaker':'c0:spk_2','kind':'person','person_id':person['id'],'confirmed':True})).status_code == 200
    responses = [await async_client.post(path+'/confirm', headers=auth_headers, json={'confirmed':True}) for _ in range(2)]
    assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
    assert responses[0].json() == responses[1].json()
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Commitment)) == 1
        assert await db.scalar(select(func.count()).select_from(Task)) == 1
        assert await db.scalar(select(func.count()).select_from(Interaction)) == 1
        promise = await db.scalar(select(Commitment))
        assert promise.direction == 'owed_by_me' and promise.due_at is None
        assert await db.scalar(select(func.count()).select_from(ContextEvent)) == 2
        assert await db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.job_type=='index_record')) >= 4
    search = await async_client.get('/api/v1/search', headers=auth_headers, params={'query':'report'})
    assert search.status_code == 200, search.text
    assert 'report' in search.text.lower()
    assert (await async_client.get('/api/v1/meetings/usage', headers=auth_headers)).json()['used_seconds'] == 17


async def test_extraction_failure_preserves_transcript_and_retry_skips_transcription(async_client, auth_headers, audio_stub, processing_stub, test_user_id, monkeypatch):
    meeting = await uploaded(async_client, auth_headers)
    import app.jobs.handlers.meeting_processing as handler
    original = handler.extract_intelligence
    async def fail(*args, **kwargs):
        raise AIProviderError('Malformed response')
    monkeypatch.setattr(handler, 'extract_intelligence', fail)
    with pytest.raises(AIProviderError):
        await process(meeting['id'], test_user_id)
    async with TestingSessionLocal() as db:
        assert (await db.get(Meeting, meeting['id'])).notes
        assert (await db.get(MeetingCapture, meeting['id'])).state == 'failed'
    monkeypatch.setattr(handler, 'extract_intelligence', original)
    async def never(*args):
        raise AssertionError('transcription must not repeat')
    monkeypatch.setattr(GeminiMeetingProvider, 'transcribe', never)
    assert (await process(meeting['id'], test_user_id))['state'] == 'awaiting_review'


async def test_audio_expiry_enqueues_private_erasure(async_client, auth_headers, audio_stub, processing_stub, test_user_id):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting['id'], test_user_id)
    async with TestingSessionLocal() as db:
        capture_row = await db.get(MeetingCapture, meeting['id'])
        capture_row.retained_until = datetime.now(timezone.utc)-timedelta(days=1)
        await db.commit()
        await expire_audio(db)
        await db.commit()
        job = await db.scalar(select(JobRecord).where(JobRecord.job_type=='storage_delete'))
        assert job.result_payload['bucket']=='meeting-audio' and job.result_payload['path'].startswith(test_user_id+'/')
    assert (await async_client.get('/api/v1/meetings/'+meeting['id']+'/recording',headers=auth_headers)).status_code==409


async def test_account_erasure_includes_audio_bucket(monkeypatch, test_user_id):
    from app.services.account import close_account, request_closure
    deleted = []
    async def erase(self, owner):
        deleted.append((self.bucket_name, owner))
    async def erase_auth(owner):
        return None
    monkeypatch.setattr('app.services.account.StorageService.delete_owner_files', erase)
    monkeypatch.setattr('app.services.account.delete_auth_user', erase_auth)
    await request_closure(test_user_id)
    await close_account(test_user_id)
    assert ('meeting-audio',test_user_id) in deleted


async def test_speaker_mapping_rejects_foreign_person(async_client, auth_headers, other_auth_headers, audio_stub, processing_stub, test_user_id):
    meeting=await uploaded(async_client,auth_headers)
    await process(meeting['id'],test_user_id)
    person=(await async_client.post('/api/v1/people',headers=other_auth_headers,json={'name':'Private'})).json()
    response=await async_client.post('/api/v1/meetings/'+meeting['id']+'/speakers',headers=auth_headers,
        json={'speaker':'c0:spk_1','kind':'person','person_id':person['id'],'confirmed':True})
    assert response.status_code==404


@pytest.mark.parametrize('evidence', ['2026-10-10', 'October 10, 2026', '10th October 2026', '১০ অক্টোবর ২০২৬'])
def test_deadline_accepts_only_matching_explicit_calendar_date(evidence):
    item = Candidate(description='Send report', evidence_text=evidence, confidence=.9,
        due_at='2026-10-10T00:00:00Z', due_evidence=evidence)
    assert item.due_at.day == 10


@pytest.mark.parametrize('evidence', ['tomorrow', 'October 10', '2026-10-11'])
def test_relative_ambiguous_or_mismatched_deadline_is_rejected(evidence):
    with pytest.raises(ValidationError):
        Candidate(description='Send report', evidence_text=evidence, confidence=.9,
            due_at='2026-10-10T00:00:00Z', due_evidence=evidence)


async def test_selective_save_keeps_deselected_promises_out_of_canonical_crm(async_client, auth_headers, audio_stub, processing_stub, test_user_id):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting['id'], test_user_id)
    path = '/api/v1/meetings/'+meeting['id']
    response = await async_client.post(path+'/confirm', headers=auth_headers,
        json={'confirmed':True,'selections':['decisions:0']})
    assert response.status_code == 200, response.text
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Commitment)) == 0
        assert await db.scalar(select(func.count()).select_from(Task)) == 0
    saved = (await async_client.get(path, headers=auth_headers)).json()
    assert saved['capture']['receipt']['selected'] == ['decisions:0']
    assert (await async_client.post(path+'/speakers',headers=auth_headers,
        json={'speaker':'c0:spk_1','kind':'me','confirmed':True})).status_code == 409


async def test_deleting_meeting_erases_derived_context_and_queues_audio(async_client, auth_headers, audio_stub, processing_stub, test_user_id):
    meeting = await uploaded(async_client, auth_headers)
    await process(meeting['id'], test_user_id)
    path = '/api/v1/meetings/'+meeting['id']
    await async_client.post(path+'/confirm', headers=auth_headers, json={'confirmed':True})
    response = await async_client.delete(path, headers=auth_headers)
    assert response.status_code == 204, response.text
    async with TestingSessionLocal() as db:
        assert (await db.scalar(select(Commitment))).deleted_at is not None
        assert (await db.scalar(select(Task))).deleted_at is not None
        assert all(event.deleted_at is not None for event in (await db.scalars(select(ContextEvent))).all())
        job = await db.scalar(select(JobRecord).where(JobRecord.job_type == 'storage_delete'))
        assert job.result_payload['bucket'] == 'meeting-audio'


async def test_provider_rest_upload_transcription_and_cleanup_contract(tmp_path, monkeypatch):
    import httpx

    import app.ai.meeting_provider as module
    calls = []
    path = tmp_path/'synthetic.flac'
    path.write_bytes(b'synthetic')
    base = 'https://generativelanguage.googleapis.com'
    def respond(request):
        calls.append(request)
        if request.url.path == '/upload/v1beta/files':
            return httpx.Response(200,headers={'x-goog-upload-url':base+'/upload/session'})
        if request.url.path == '/upload/session':
            return httpx.Response(200,json={'file':{'name':'files/synthetic','uri':base+'/v1beta/files/synthetic','state':'ACTIVE'}})
        if request.method == 'DELETE':
            return httpx.Response(200,json={})
        return httpx.Response(200,json={'output_text':'বাংলা and English'})
    client_type = httpx.AsyncClient
    monkeypatch.setattr(module.httpx,'AsyncClient',lambda **kwargs: client_type(**kwargs,transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(GeminiLLMProvider,'_is_unconfigured',lambda self:False)
    result = await GeminiMeetingProvider().transcribe(path,1,1740)
    assert result[0]['speaker_local_id'] == 'c1:unknown' and result[0]['start_offset'] == 1740
    import json
    payload = json.loads(calls[2].content)
    assert payload['store'] is False and payload['model'] == settings.GEMINI_TRANSCRIBE_MODEL
    assert payload['generation_config']['transcription_config']['mode']['diarization_mode'] == 'speaker'
    assert calls[-1].method == 'DELETE'


async def test_signed_upload_and_playback_use_private_paths_and_short_expiry(monkeypatch, test_user_id):
    import httpx

    import app.services.meeting_audio as module
    monkeypatch.setattr(settings,'SUPABASE_URL','https://mock.supabase.co')
    monkeypatch.setattr(settings,'SUPABASE_SERVICE_ROLE_KEY','synthetic-server-only-test-key')
    requests = []
    def respond(request):
        requests.append(request)
        key = 'url' if '/upload/sign/' in request.url.path else 'signedURL'
        return httpx.Response(200,json={key:request.url.path.removeprefix('/storage/v1')+'?token=synthetic'})
    client_type = httpx.AsyncClient
    monkeypatch.setattr(module.httpx,'AsyncClient',lambda **kwargs: client_type(**kwargs,transport=httpx.MockTransport(respond)))
    storage = AudioStorage()
    storage.use_supabase = True
    path, url = await storage.authorize(test_user_id,str(uuid4()),'audio/x-m4a')
    assert path.startswith(test_user_id+'/') and path.endswith('.m4a')
    assert '/object/upload/sign/meeting-audio/' in url and '/object/public/' not in url
    signed = await storage.get_signed_url(path,86400)
    import json
    assert json.loads(requests[-1].content)['expiresIn'] == 300
    assert '/object/sign/meeting-audio/' in signed and '/object/public/' not in signed


async def test_decoded_samples_override_forged_container_duration(tmp_path, monkeypatch):
    import asyncio
    import tempfile

    from app.services import meeting_audio as module
    monkeypatch.setattr(tempfile,'tempdir',str(tmp_path))
    async def probe(*args):
        return b'{"streams":[{"codec_type":"audio"}],"format":{"duration":"0.001"}}'
    monkeypatch.setattr(module,'run_audio_tool',probe)
    class Decoded:
        def __init__(self):
            self.stdout = asyncio.StreamReader()
            self.stdout.feed_data(b'\0'*48000)
            self.stdout.feed_eof()
            self.returncode = None
        async def wait(self):
            self.returncode = 0
        def kill(self):
            self.returncode = -1
    async def decode(*args,**kwargs):
        assert '-protocol_whitelist' in args and '-map' in args
        return Decoded()
    monkeypatch.setattr(module.asyncio,'create_subprocess_exec',decode)
    assert await module.inspect_audio(b'synthetic','audio/webm') == 2


async def test_live_relay_accepts_empty_setup_ack_and_meters_before_provider(async_client, auth_headers, test_user_id, monkeypatch):
    import asyncio
    import json
    from contextlib import asynccontextmanager
    from types import SimpleNamespace

    from app.services import meeting_live as module
    meeting = await capture(async_client,auth_headers)
    arrived = asyncio.Event()
    sent = []
    class Socket:
        headers = {}
        scope = {'type':'websocket'}
        messages = []
        async def accept(self): pass
        async def close(self,**kwargs): pass
        async def receive_json(self): return {'token':'synthetic-user-token'}
        async def send_json(self,value): self.messages.append(value)
        async def receive_bytes(self):
            if not arrived.is_set():
                return b'\0'*32000
            await asyncio.Event().wait()
    class Remote:
        async def send(self,value):
            packet = json.loads(value)
            sent.append(packet)
            if 'realtimeInput' in packet:
                async with TestingSessionLocal() as db:
                    assert (await quota_view(db,test_user_id))['used_seconds'] == 1
                arrived.set()
        async def recv(self): return '{"setupComplete":{}}'
        def __aiter__(self): return self.receive()
        async def receive(self):
            await arrived.wait()
            yield json.dumps({'serverContent':{'inputTranscription':{'text':'বাংলা English'}}})
            yield json.dumps({'goAway':{}})
    @asynccontextmanager
    async def connection(*args,**kwargs):
        assert 'key=' not in args[0] and 'x-goog-api-key' in kwargs['additional_headers']
        yield Remote()
    @asynccontextmanager
    async def session(owner):
        assert owner == test_user_id
        async with TestingSessionLocal() as db:
            yield db
    async def user(request,credentials):
        assert credentials.credentials == 'synthetic-user-token'
        return SimpleNamespace(id=test_user_id)
    monkeypatch.setattr(module,'connect',connection)
    monkeypatch.setattr(module,'rls_db_session',session)
    monkeypatch.setattr(module,'get_current_user',user)
    monkeypatch.setattr(GeminiLLMProvider,'_is_unconfigured',lambda self:False)
    socket = Socket()
    async with asyncio.timeout(5):
        await module.live_transcript(socket,UUID(meeting['id']))
    assert socket.messages[0]['type'] == 'ready'
    assert any(m.get('text') == 'বাংলা English' for m in socket.messages)
    assert sent[1]['realtimeInput']['audio']['mimeType'] == 'audio/pcm;rate=16000'


def test_index_distinguishes_unconfirmed_ai_and_excludes_deselected_details():
    from types import SimpleNamespace

    from app.ai.indexing import meeting_chunks, record_text
    draft = SimpleNamespace(confirmed_at=None, receipt={}, transcript_segments=[], intelligence={
        'important_facts':[{'description':'Unsupported fact suggestion','evidence_text':'Source quote','interpretation':False}]})
    record = SimpleNamespace(id='meeting',capture=draft,title='Test',start_time=datetime.now(timezone.utc),
        meta={},summary='Summary',notes='Source quote',decisions_list=[],action_items=[])
    assert 'Unconfirmed AI suggestions' in record_text(record,'meeting')
    draft.confirmed_at = datetime.now(timezone.utc)
    draft.receipt = {'selected':[]}
    text = record_text(record,'meeting')
    assert 'Unsupported fact suggestion' not in text and 'Source quote' in text
    assert all(chunk['metadata']['source']=='meeting' for chunk in meeting_chunks(record))


async def test_manual_meeting_cannot_relink_deleted_person(async_client, auth_headers):
    person = (await async_client.post('/api/v1/people',headers=auth_headers,json={'name':'Deleted participant'})).json()
    assert (await async_client.delete('/api/v1/people/'+person['id'],headers=auth_headers)).status_code == 204
    response = await async_client.post('/api/v1/meetings',headers=auth_headers,json={
        'title':'Manual notes','meeting_date':'2026-10-08T10:00:00', 'participant_person_ids':[person['id']]})
    assert response.status_code == 404
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Meeting)) == 0


async def test_outer_worker_timeout_leaves_retryable_capture_instead_of_stuck_processing(async_client, auth_headers, audio_stub, monkeypatch):
    from app.jobs.runner import JobRunner
    meeting = await uploaded(async_client, auth_headers)
    async with TestingSessionLocal() as db:
        job_id = str((await db.scalar(select(JobRecord).where(JobRecord.job_type=='meeting_processing'))).id)
    async def timed_out(db,owner,kind,payload):
        row = await db.get(MeetingCapture,payload['meeting_id'])
        row.state = 'extracting'
        await db.commit()
        raise TimeoutError('synthetic worker timeout')
    monkeypatch.setattr(JobRunner,'_execute_payload',timed_out)
    for _ in range(3):
        await JobRunner.run_job_by_id(job_id)
    response = await async_client.get('/api/v1/meetings/'+meeting['id'],headers=auth_headers)
    assert response.json()['capture']['state'] == 'failed'
    assert response.json()['capture']['error_code'] == 'MEETING_PROCESSING_TIMEOUT'
    retried = await async_client.post('/api/v1/meetings/'+meeting['id']+'/retry',headers=auth_headers)
    assert retried.status_code == 200 and retried.json()['capture']['state'] == 'uploaded'
