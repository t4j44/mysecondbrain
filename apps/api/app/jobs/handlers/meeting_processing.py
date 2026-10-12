"""Restartable transcription and extraction in the existing durable worker."""
import hashlib
from datetime import datetime, timedelta, timezone

from app.ai.meeting_provider import GeminiMeetingProvider, extract_intelligence
from app.ai.privacy import private_ai_scope
from app.core.config import settings
from app.core.errors import ConflictError
from app.jobs.index_queue import queue_index
from app.services.meeting_audio import AudioStorage, audio_chunks
from app.services.meeting_intelligence import capture_for, ensure_audio_consent


async def process_meeting(db, owner, payload):
    if payload.get('processing_version') != 1:
        raise ConflictError('Unsupported meeting processing version.')
    identity = payload['meeting_id']
    meeting, capture = await capture_for(db, owner, identity, lock=True)
    if capture.state in {'awaiting_review', 'completed'}:
        return {'meeting_id': identity, 'state': capture.state}
    if not capture.audio_path or not capture.audio_path.startswith(owner + '/') or capture.charged_seconds < capture.duration_seconds or not capture.duration_seconds:
        raise ConflictError('Recording upload has not been verified.')
    try:
        ensure_audio_consent(capture)
        if not meeting.notes:
            capture.state, capture.error_code = 'transcribing', None
            await db.commit()
            content = await AudioStorage().read_bounded(capture.audio_path)
            if hashlib.sha256(content).hexdigest() != capture.audio_checksum:
                raise ConflictError('The uploaded recording changed.')
            async for index, offset, path in audio_chunks(content, capture.audio_mime, capture.duration_seconds):
                _, capture = await capture_for(db, owner, identity, lock=True)
                if any(s['chunk_index'] == index for s in capture.transcript_segments):
                    await db.commit()
                    continue
                await db.commit()
                segments = await GeminiMeetingProvider().transcribe(path, index, offset)
                _, capture = await capture_for(db, owner, identity, lock=True)
                if not any(s['chunk_index'] == index for s in capture.transcript_segments):
                    capture.transcript_segments = [*capture.transcript_segments, *segments]
                await db.commit()
            meeting, capture = await capture_for(db, owner, identity, lock=True)
            meeting.notes = '\n'.join(f'[{s["speaker_local_id"]} {s["start_offset"]:.1f}s] {s["text"]}'
                for s in capture.transcript_segments)
            capture.retained_until = datetime.now(timezone.utc) + timedelta(days=settings.MEETING_AUDIO_RETENTION_DAYS)
            await db.commit()
        meeting, capture = await capture_for(db, owner, identity, lock=True)
        capture.state = 'extracting'
        transcript, date = meeting.notes, meeting.start_time.isoformat()
        speakers = sorted({s['speaker_local_id'] for s in capture.transcript_segments})
        await db.commit()
        with private_ai_scope(owner, db):
            intelligence = await extract_intelligence(transcript, date=date, speakers=speakers)
        meeting, capture = await capture_for(db, owner, identity, lock=True)
        capture.intelligence = intelligence.model_dump(mode='json')
        meeting.summary = intelligence.summary
        capture.state, capture.error_code = 'awaiting_review', None
        queue_index(db, meeting)
        await db.commit()
        return {'meeting_id': identity, 'state': 'awaiting_review'}
    except Exception as exc:
        await db.rollback()
        try:
            _, capture = await capture_for(db, owner, identity, lock=True)
            stage_code = 'MEETING_EXTRACTION_FAILED' if capture.state == 'extracting' else 'MEETING_TRANSCRIPTION_FAILED'
            safe_code = getattr(exc, 'code', None)
            capture.state, capture.error_code = 'failed', safe_code if safe_code in {'AI_PRIVACY_BLOCKED', 'AUDIO_TOOLS_UNAVAILABLE'} else stage_code
            await db.commit()
        except Exception:
            await db.rollback()
        raise
