"""Native-ready REST contract; audio never passes through Next.js."""
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, WebSocket
from fastapi.responses import JSONResponse

from app.core.errors import ConflictError
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.schemas.meeting_intelligence import (
    CaptureCreate,
    ConfirmIntelligence,
    SpeakerMapping,
    UploadAuthorize,
)
from app.schemas.meetings import MeetingResponse
from app.services import meeting_intelligence as service
from app.services.meeting_audio import AudioStorage
from app.services.meeting_usage import quota_view

router = APIRouter(prefix='/meetings', tags=['Meetings'])


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
