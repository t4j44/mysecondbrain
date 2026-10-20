"""Capture lifecycle and explicit transactional writes to the existing graph."""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, text

from app.ai.indexing import owned_record
from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.jobs.index_queue import queue_index
from app.models.entities import (
    Commitment,
    Decision,
    EntityEdge,
    Interaction,
    JobRecord,
    Meeting,
    Memory,
    Task,
)
from app.models.meeting_intelligence import MeetingCapture
from app.models.meetings import MeetingParticipant
from app.schemas.meeting_intelligence import (
    CANDIDATE_FIELDS,
    CaptureCreate,
    ConfirmIntelligence,
    MeetingIntelligence,
    SpeakerMapping,
)
from app.services.context_events import create_event, event_link
from app.services.meeting_audio import AudioStorage, audio_mime, inspect_audio
from app.services.meeting_usage import charge, month_start


async def capture_for(db, owner, identity, *, lock=False):
    meeting = await owned_record(db, owner, 'meeting', str(identity))
    query = select(MeetingCapture).where(MeetingCapture.user_id == owner, MeetingCapture.meeting_id == str(identity))
    if lock:
        query = query.with_for_update()
    capture = (await db.execute(query.execution_options(populate_existing=True))).scalar_one_or_none()
    if not capture:
        raise NotFoundError('Recording is not available.')
    if lock:
        # Read metadata only after the capture lock; concurrent notes/review writes
        # must see the previous transaction's version, not the stale identity map.
        meeting = await db.scalar(select(Meeting).where(Meeting.id == str(identity),
            Meeting.user_id == owner, Meeting.deleted_at.is_(None), Meeting.archived_at.is_(None))
            .with_for_update().execution_options(populate_existing=True))
        if not meeting:
            raise NotFoundError('Meeting is not available.')
    return meeting, capture


async def create_capture(db, owner, payload: CaptureCreate):
    if settings.AI_DATA_MODE == 'free_redacted' and not payload.non_sensitive_recording:
        raise ConflictError('Free-tier audio requires explicit confirmation that the recording contains no sensitive, confidential or personal information. Text redaction does not sanitize audio.')
    if settings.AI_DATA_MODE == 'paid_private' and settings.requires_postgres() and not settings.MEETING_PRIVATE_AUDIO_RELEASE_VERIFIED:
        raise ConflictError('Private audio processing is disabled until the provider project privacy terms and release acceptance are verified.')
    if db.bind.dialect.name == 'postgresql':
        await db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key, 32))'),
            {'key': f'{owner}:{payload.request_id}'})
    prior = await db.scalar(select(MeetingCapture).where(MeetingCapture.user_id == owner,
        MeetingCapture.request_id == str(payload.request_id)))
    if prior:
        return (await capture_for(db, owner, prior.meeting_id))[0]
    if payload.venture_id:
        await owned_record(db, owner, 'venture', str(payload.venture_id))
    now = datetime.now(timezone.utc)
    meeting = Meeting(user_id=owner, title=payload.title, start_time=payload.meeting_date,
        end_time=payload.meeting_date, venture_id=str(payload.venture_id) if payload.venture_id else None,
        meta={'timezone': payload.timezone, 'audio_privacy_attestation': {
            'non_sensitive_recording': payload.non_sensitive_recording,
            'accepted_by_user': True, 'notice_version': 2}})
    db.add(meeting)
    await db.flush()
    capture = MeetingCapture(meeting_id=meeting.id, user_id=owner, request_id=str(payload.request_id),
        period_start=month_start(), consent_at=now, data_mode=settings.AI_DATA_MODE,
        receipt={'audio_privacy': {'notice_version': 2,
            'non_sensitive_recording': payload.non_sensitive_recording}})
    db.add(capture)
    await db.flush()
    await db.refresh(meeting)
    return meeting


async def authorize_upload(db, owner, identity, mime):
    _, capture = await capture_for(db, owner, identity, lock=True)
    mime = audio_mime(mime)
    if capture.state not in {'draft', 'recording', 'uploading'}:
        raise ConflictError('This recording has already been submitted.')
    storage = AudioStorage()
    if capture.audio_path:
        if capture.audio_mime != mime:
            raise ConflictError('Retry with the original recording format.')
        url = await storage.upload_url(capture.audio_path)
    else:
        capture.audio_path, url = await storage.authorize(owner, identity, mime)
        capture.audio_mime = mime
    capture.state = 'uploading'
    return {'upload_url': url, 'mime_type': mime, 'max_bytes': settings.MEETING_AUDIO_MAX_BYTES,
        'local_upload_endpoint': f'/meetings/{identity}/audio' if not url else None}


def enqueue_processing(db, capture):
    db.add(JobRecord(user_id=capture.user_id, job_type='meeting_processing', status='pending',
        result_payload={'meeting_id': str(capture.meeting_id), 'processing_version': 1}))


async def finalize_upload(db, owner, identity):
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if capture.state in {'uploaded', 'transcribing', 'extracting', 'awaiting_review', 'completed', 'failed'}:
        return meeting
    if not capture.audio_path or capture.state != 'uploading':
        raise ConflictError('Upload a recording first.')
    ensure_audio_consent(capture)
    if not capture.audio_path.startswith(owner + '/'):
        raise NotFoundError('Recording is not available.')
    content = await AudioStorage().read_bounded(capture.audio_path)
    duration = await inspect_audio(content, capture.audio_mime)
    # A draft made last month cannot consume last month's unused allowance.
    if not capture.charged_seconds:
        capture.period_start = month_start()
    await charge(db, capture, max(duration, capture.live_seconds))
    capture.duration_seconds = duration
    capture.audio_checksum = hashlib.sha256(content).hexdigest()
    meeting.end_time = meeting.start_time + timedelta(seconds=duration)
    capture.state, capture.error_code = 'uploaded', None
    enqueue_processing(db, capture)
    await db.flush()
    await db.refresh(meeting)
    return meeting


async def retry_processing(db, owner, identity):
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if capture.state != 'failed':
        return meeting
    jobs = (await db.execute(select(JobRecord).where(JobRecord.user_id == owner,
        JobRecord.job_type == 'meeting_processing'))).scalars().all()
    matching = [j for j in jobs if (j.result_payload or {}).get('meeting_id') == str(identity)]
    if any(j.status in {'pending', 'processing'} for j in matching):
        return meeting
    capture.state, capture.error_code = 'uploaded', None
    enqueue_processing(db, capture)
    return meeting


async def map_speaker(db, owner, identity, payload: SpeakerMapping):
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if capture.confirmed_at:
        raise ConflictError('Speaker mappings are already saved for this meeting.')
    speakers = {s['speaker_local_id'] for s in capture.transcript_segments}
    if payload.speaker not in speakers:
        raise NotFoundError('Speaker is not available.')
    person_name = None
    if payload.person_id:
        person = await owned_record(db, owner, 'person', str(payload.person_id))
        person_name = person.name
    capture.speaker_mappings = {**capture.speaker_mappings, payload.speaker:
        {'kind': payload.kind, 'person_id': str(payload.person_id) if payload.person_id else None,
         'person_name': person_name,
         'source': 'meeting', 'meeting_id': str(identity), 'speaker_label': payload.speaker, 'confirmed_by_user': True}}
    await db.flush()
    await db.refresh(meeting)
    return meeting


async def confirm_intelligence(db, owner, identity, payload: ConfirmIntelligence):
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if capture.confirmed_at:
        return capture.receipt
    if capture.state != 'awaiting_review':
        raise ConflictError('Wait until the meeting is ready to review.')
    intelligence = MeetingIntelligence.model_validate(capture.intelligence)
    from app.ai.meeting_evidence import ground_intelligence
    intelligence = ground_intelligence(intelligence, capture.transcript_segments,
        sorted({s['speaker_local_id'] for s in capture.transcript_segments}))
    candidates = {f'{key}:{i}': item for key in CANDIDATE_FIELDS
        for i, item in enumerate(getattr(intelligence, key))}
    selected = set(candidates) if payload.selections is None else set(payload.selections)
    if selected - candidates.keys():
        raise ConflictError('One of the selected details is not available.')
    people = {}
    for mapping in capture.speaker_mappings.values():
        if mapping['kind'] == 'person':
            person = await owned_record(db, owner, 'person', mapping['person_id'])
            people[str(person.id)] = person
    # A speaker mapping creates participation only at this explicit Save gate.
    existing = {str(p) for p in meeting.participant_person_ids}
    for person_id in people.keys() - existing:
        db.add(MeetingParticipant(user_id=owner, meeting_id=meeting.id, person_id=person_id))
    meeting.summary = intelligence.summary
    meeting.decisions_list = [v.description for k, v in candidates.items() if k in selected and k.startswith('decisions:')]
    meeting.action_items = [v.description for k, v in candidates.items() if k in selected and k.split(':')[0] in {'action_items', 'follow_ups'}]
    provenance = {'source': 'meeting', 'meeting_id': str(meeting.id), 'confirmed_by_user': True,
        'timezone_known': bool((meeting.meta or {}).get('timezone')),
        'speaker_mappings': capture.speaker_mappings}
    meeting.meta = {**(meeting.meta or {}), 'participant_names': [p.name for p in people.values()]}
    project_id = (meeting.meta or {}).get('project_id')
    for kind, linked_id in (('venture', meeting.venture_id), ('project', project_id)):
        if linked_id:
            await owned_record(db, owner, kind, str(linked_id))
    # Keep exact proposals in capture; context payload includes selected evidence only.
    event, _ = await create_event(db, owner, key=f'meeting:{identity}:v1', event_type='meeting',
        title=meeting.title, summary=intelligence.summary, occurred_at=meeting.start_time,
        timezone=(meeting.meta or {}).get('timezone') or 'UTC', source_type='meeting', source_provider='gemini', source_external_id=str(identity),
        raw_payload={'selected': sorted(selected)}, metadata_payload=provenance,
        venture_id=meeting.venture_id, project_id=project_id, privacy_class='private')
    await event_link(db, event, 'meeting', meeting.id, derived=False)
    async def meeting_link(kind, target, relation, metadata=None):
        # Both source and target checked under this owner's transaction.
        await owned_record(db, owner, kind, str(target))
        db.add(EntityEdge(user_id=owner, source_entity_type='meeting', source_entity_id=meeting.id,
            target_entity_type=kind, target_entity_id=str(target), relationship_type=relation,
            source_event_id=event.id, occurred_at=meeting.start_time, valid_from=meeting.start_time,
            confidence=(metadata or {}).get('confidence', 1), metadata_payload={**provenance, 'timezone_known': bool((meeting.meta or {}).get('timezone')),
                **(metadata or {})}))
    if meeting.venture_id:
        await meeting_link('venture', meeting.venture_id, 'about')
    if project_id:
        await meeting_link('project', project_id, 'related_to')
    receipt: dict = {'meeting_id': str(identity), 'context_event_id': str(event.id),
        'audio_privacy': (capture.receipt or {}).get('audio_privacy', {}),
        'interactions': [], 'commitments': [], 'tasks': [], 'decisions': [], 'memories': [], 'selected': sorted(selected)}
    for person in people.values():
        await meeting_link('person', person.id, 'participated_in_by', {'speaker_ids':
            [s for s, m in capture.speaker_mappings.items() if m.get('person_id') == str(person.id)]})
        interaction = Interaction(user_id=owner, person_id=person.id, meeting_id=meeting.id,
            venture_id=meeting.venture_id, interaction_type='meeting', title=meeting.title,
            summary=intelligence.summary, date=meeting.start_time, meta=provenance)
        db.add(interaction)
        await db.flush()
        queue_index(db, interaction)
        await event_link(db, event, 'interaction', interaction.id)
        receipt['interactions'].append(str(interaction.id))
        person.last_interaction_at = max([d for d in [person.last_interaction_at, meeting.start_time]
            if d is not None], key=lambda d: d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d)
        person_event, _ = await create_event(db, owner, key=f'meeting:{identity}:person:{person.id}',
            event_type='meeting', title=meeting.title, summary=intelligence.summary, occurred_at=meeting.start_time,
            timezone=(meeting.meta or {}).get('timezone') or 'UTC', source_type='meeting', source_provider='gemini', source_external_id=str(identity),
            person_id=person.id, metadata_payload=provenance, privacy_class='private')
        await event_link(db, person_event, 'meeting', meeting.id, derived=False)
    for key in sorted(selected):
        item = candidates[key]
        category = key.split(':')[0]
        meta = {**provenance, 'candidate_id': key, 'evidence_text': item.evidence_text,
            'evidence': [r.model_dump(mode='json') for r in item.evidence],
            'condition': item.condition, 'confidence': item.confidence, 'interpretation': item.interpretation}
        mapping_from = capture.speaker_mappings.get(item.from_speaker, {})
        mapping_to = capture.speaker_mappings.get(item.to_speaker, {})
        row: Any = None
        row_kind = None
        if category == 'commitments' and not item.interpretation:
            direction = 'owed_by_me' if mapping_from.get('kind') == 'me' else 'owed_to_me' if mapping_to.get('kind') == 'me' else 'unspecified'
            row = Commitment(user_id=owner, meeting_id=meeting.id, venture_id=meeting.venture_id,
                from_person_id=mapping_from.get('person_id'), to_person_id=mapping_to.get('person_id'),
                description=item.description + (f' (Condition: {item.condition})' if item.condition else ''),
                project_id=project_id, direction=direction, due_at=item.due_at, source='meeting')
            row_kind = 'commitment'
        elif category in {'action_items', 'follow_ups'} and not item.interpretation:
            row = Task(user_id=owner, title=item.description[:500], description=item.evidence_text,
                venture_id=meeting.venture_id, project_id=project_id, person_id=mapping_from.get('person_id'),
                due_date=item.due_at, calendar_sync_metadata=meta)
            row_kind = 'task'
        elif category == 'decisions' and not item.interpretation:
            row = Decision(user_id=owner, title=item.description[:255], decision=item.description,
                context=f'Meeting {identity}: {item.evidence_text}', venture_id=meeting.venture_id,
                project_id=project_id,
                decision_date=meeting.start_time)
            row_kind = 'decision'
        elif category in {'memory_candidates', 'lesson_candidates'}:
            row = Memory(user_id=owner, title=item.description[:255], body=item.description,
                summary=item.evidence_text, source='meeting', type='lesson' if category == 'lesson_candidates' else 'insight',
                memory_date=meeting.start_time, meta=meta)
            row_kind = 'memory'
        if row:
            db.add(row)
            await db.flush()
            queue_index(db, row)
            await event_link(db, event, row_kind, row.id, metadata=meta)
            await meeting_link(row_kind, row.id, 'produced', meta)
            receipt[{'commitment': 'commitments', 'task': 'tasks', 'decision': 'decisions', 'memory': 'memories'}[str(row_kind)]].append(str(row.id))
    # Preserve facts, feedback, interpretations and proposal evidence with the source.
    capture.receipt = receipt
    capture.intelligence = intelligence.model_dump(mode='json')
    capture.confirmed_at = datetime.now(timezone.utc)
    capture.state = 'completed'
    queue_index(db, meeting)
    await db.flush()
    return receipt


async def meter_live(db, owner, identity, seconds: int):
    _, capture = await capture_for(db, owner, identity, lock=True)
    if capture.state not in {'draft', 'recording'}:
        raise ConflictError('This recording has ended.')
    ensure_audio_consent(capture)
    if not capture.charged_seconds:
        capture.period_start = month_start()
    capture.live_seconds += seconds
    await charge(db, capture, capture.live_seconds)
    capture.state = 'recording'


def ensure_audio_consent(capture):
    if capture.data_mode != settings.AI_DATA_MODE:
        raise ConflictError('AI privacy settings changed. Create a new meeting and accept the current recording notice.')
    privacy = (capture.receipt or {}).get('audio_privacy', {})
    if privacy.get('notice_version') != 2 or (settings.AI_DATA_MODE == 'free_redacted' and not privacy.get('non_sensitive_recording')):
        raise ConflictError('The recording notice changed. Create a new meeting and accept the current audio privacy notice.')
    if settings.AI_DATA_MODE == 'paid_private' and settings.requires_postgres() and not settings.MEETING_PRIVATE_AUDIO_RELEASE_VERIFIED:
        raise ConflictError('Private audio processing is disabled pending provider privacy verification.')


async def expire_audio(db):
    now = datetime.now(timezone.utc)
    rows = (await db.execute(select(MeetingCapture).where(MeetingCapture.audio_deleted_at.is_(None),
        MeetingCapture.audio_path.is_not(None), MeetingCapture.retained_until <= now)
        .limit(20).with_for_update(skip_locked=True))).scalars().all()
    for capture in rows:
        # Erasure is durable; signed playback immediately stops once marked deleted.
        db.add(JobRecord(user_id=capture.user_id, job_type='storage_delete', status='pending',
            result_payload={'bucket': settings.MEETING_AUDIO_BUCKET, 'path': capture.audio_path}))
        capture.audio_deleted_at = now
