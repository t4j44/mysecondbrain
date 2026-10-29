"""Native-ready REST contract; audio never passes through Next.js."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, WebSocket
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.errors import ConflictError
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.schemas.meeting_intelligence import (
    CaptureCreate,
    ConfirmIntelligence,
    MeetingReview,
    NotesUpdate,
    SpeakerMapping,
    UploadAuthorize,
)
from app.schemas.meetings import MeetingResponse
from app.services import meeting_intelligence as service
from app.services.meeting_audio import AudioStorage
from app.services.meeting_usage import quota_view

router = APIRouter(prefix='/meetings', tags=['Meetings'])


@router.get('/{identity}/preparation')
async def preparation(identity: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.services.meeting_preparation import prepare
    return JSONResponse(jsonable_encoder(await prepare(db, user.id, str(identity))),
        headers={'Cache-Control': 'private, no-store'})


@router.get('/{identity}/notes')
async def notes(identity: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.services.meeting_outputs import notes_view
    meeting, _ = await service.capture_for(db, user.id, str(identity))
    return JSONResponse(notes_view(meeting), headers={'Cache-Control': 'no-store'})


@router.put('/{identity}/notes')
async def update_notes(identity: UUID, payload: NotesUpdate, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.services.meeting_outputs import save_notes
    meeting, _ = await service.capture_for(db, user.id, str(identity), lock=True)
    result = await save_notes(db, meeting, payload)
    await db.commit()
    return JSONResponse(result, headers={'Cache-Control': 'no-store'})


@router.put('/{identity}/review', response_model=MeetingResponse)
async def review(identity: UUID, payload: MeetingReview, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    meeting, capture = await service.capture_for(db, user.id, str(identity), lock=True)
    if capture.confirmed_at:
        raise ConflictError('Meeting context is already confirmed; existing historical links are preserved.')
    service.require_review_snapshot(meeting, payload.expected_review_token)
    meta = meeting.meta or {}
    if meta.get('review_version', 0) != payload.expected_version:
        raise ConflictError('Meeting details changed in another tab. Reload before saving.')
    values = payload.model_dump(exclude_unset=True, exclude={'expected_version', 'expected_review_token'})
    for kind in ('project', 'venture'):
        linked_id = values.get(kind + '_id')
        if linked_id:
            from app.ai.indexing import owned_record
            await owned_record(db, user.id, kind, str(linked_id))
    for key in ('title', 'location', 'venture_id'):
        if key in values:
            if key == 'title' and values[key] is None:
                raise ConflictError('Title cannot be empty.')
            setattr(meeting, key, str(values[key]) if key == 'venture_id' and values[key] else values[key])
    meeting.meta = {**meta, **{k: str(v) if k == 'project_id' and v else v
        for k, v in values.items() if k in {'purpose', 'agenda', 'timezone', 'project_id'}},
        'review_version': payload.expected_version + 1, 'reviewed_by_user': True}
    if 'purpose' in values:
        meeting.description = values['purpose']
    from app.jobs.index_queue import queue_index
    queue_index(db, meeting)
    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.get('/{identity}/export/markdown')
async def markdown(identity: UUID, kind: Literal['notes', 'minutes', 'detailed', 'all'] = 'all',
        user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.services.meeting_outputs import export_markdown
    meeting, _ = await service.capture_for(db, user.id, str(identity))
    return Response(export_markdown(meeting, kind), media_type='text/markdown; charset=utf-8',
        headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Content-Disposition': f'attachment; filename="meeting-{identity}-{kind}.md"'})


@router.websocket('/{identity}/live')
async def live(socket: WebSocket, identity: UUID):
    from app.services.meeting_live import live_transcript
    await live_transcript(socket, identity)


@router.get('/usage')
async def usage(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await quota_view(db, user.id)


@router.get('/people-search')
async def search_people(q: str = '', user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from sqlalchemy import select

    from app.models.entities import Person
    rows = (await db.execute(select(Person).where(Person.user_id == user.id, Person.deleted_at.is_(None),
        Person.archived_at.is_(None), Person.name.ilike('%' + q[:100].replace('%', '\\%').replace('_', '\\_') + '%', escape='\\'))
        .order_by(Person.name).limit(30))).scalars().all()
    return [{'id': str(p.id), 'name': p.name} for p in rows]


@router.post('/captures', response_model=MeetingResponse, status_code=201)
async def create(payload: CaptureCreate, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    meeting = await service.create_capture(db, user.id, payload)
    await db.commit()
    return meeting


@router.post('/{identity}/upload-authorization')
async def authorize(identity: UUID, payload: UploadAuthorize, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    result = await service.authorize_upload(db, user.id, str(identity), payload.mime_type)
    await db.commit()
    return result


@router.put('/{identity}/audio', status_code=204)
async def upload_local(identity: UUID, request: Request, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.core.config import settings
    from app.core.errors import ValidationError
    _, capture = await service.capture_for(db, user.id, str(identity), lock=True)
    if capture.state != 'uploading' or not capture.audio_path:
        raise ConflictError('Authorize this upload first.')
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > settings.MEETING_AUDIO_MAX_BYTES:
            raise ValidationError('Recording is too large (maximum 50 MB).')
    await AudioStorage().local_upload(capture.audio_path, bytes(content))
    await db.commit()
    return Response(status_code=204)


@router.post('/{identity}/finalize-upload', response_model=MeetingResponse)
async def finalize(identity: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    meeting = await service.finalize_upload(db, user.id, str(identity))
    await db.commit()
    return meeting


@router.post('/{identity}/retry', response_model=MeetingResponse)
async def retry(identity: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    meeting = await service.retry_processing(db, user.id, str(identity))
    await db.commit()
    return meeting


@router.post('/{identity}/speakers', response_model=MeetingResponse)
async def speakers(identity: UUID, payload: SpeakerMapping, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    meeting = await service.map_speaker(db, user.id, str(identity), payload)
    await db.commit()
    return meeting


@router.post('/{identity}/confirm')
async def confirm(identity: UUID, payload: ConfirmIntelligence, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    receipt = await service.confirm_intelligence(db, user.id, str(identity), payload)
    await db.commit()
    return receipt


@router.get('/{identity}/recording')
async def recording(identity: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from datetime import datetime, timezone
    _, capture = await service.capture_for(db, user.id, str(identity))
    expiry = capture.retained_until
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if not capture.audio_path or capture.audio_deleted_at or (expiry and expiry <= datetime.now(timezone.utc)):
        raise ConflictError('This recording is no longer available. The transcript is saved.')
    storage = AudioStorage()
    if storage.use_supabase:
        return JSONResponse({'url': await storage.get_signed_url(capture.audio_path, 300), 'expires_seconds': 300},
            headers={'Cache-Control': 'no-store'})
    return Response(await storage.read_bounded(capture.audio_path), media_type=capture.audio_mime,
        headers={'Cache-Control': 'no-store'})
