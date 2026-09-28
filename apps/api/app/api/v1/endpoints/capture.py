from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.integrations.storage_client import StorageService
from app.services.capture import CaptureConfirm, CaptureInput, CaptureService
from app.services.context_events import erase_media
from app.services.context_media import media_record, upload_media

router = APIRouter(prefix="/capture", tags=["Capture"])


@router.post("/propose")
async def propose(payload: CaptureInput, user: AuthenticatedUser = Depends(get_current_user),
                  db=Depends(get_rls_db_session)):
    return await CaptureService(db, user.id).propose(payload)


@router.post("/{draft_id}/confirm")
async def confirm(draft_id: str, payload: CaptureConfirm,
                  user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await CaptureService(db, user.id).confirm(draft_id, payload)


@router.post('/{draft_id}/media')
async def upload(draft_id: UUID, request_id: UUID = Form(...),
                 kind: Literal['business_card', 'moment'] = Form(...), file: UploadFile = File(...),
                 user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    content = await file.read(2 * 1024**2 + 1)
    return await upload_media(db, user.id, draft_id, request_id, kind, content)


@router.get('/media/{media_id}')
async def photo(media_id: UUID, thumbnail: bool = False,
                user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    row = await media_record(db, user.id, media_id)
    content = await StorageService().read_file(row.thumbnail_path if thumbnail else row.storage_path)
    return Response(content, media_type=row.mime_type, headers={'Cache-Control': 'private, no-store',
                    'X-Content-Type-Options': 'nosniff'})


@router.delete('/media/{media_id}')
async def remove_photo(media_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    row = await media_record(db, user.id, media_id)
    erase_media(db, row)
    await db.delete(row)
    await db.commit()
    return {'deleted': True}
