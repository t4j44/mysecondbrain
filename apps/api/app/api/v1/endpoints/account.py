from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.core.config import settings
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import admin_db_session, get_rls_db_session
from app.models.entities import AccountClosure
from app.services.account import portable_export, request_closure

router = APIRouter(prefix='/account', tags=['Privacy and data'])


@router.get('/privacy')
async def privacy(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return {'ai_data_mode': settings.AI_DATA_MODE, 'account_deletion': 'available',
            'notice': 'Free-tier redaction can miss identifying details. Avoid sensitive or confidential content.'}


@router.get('/export')
async def export_account(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    data = await portable_export(db, user.id)
    return Response(data, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename="second-brain-account.zip"', 'Cache-Control': 'no-store'})


class DeleteConfirmation(BaseModel):
    confirmation: Literal['DELETE MY ACCOUNT']


@router.post('/delete', status_code=202)
async def delete_account(payload: DeleteConfirmation, user: AuthenticatedUser = Depends(get_current_user)):
    return {'status': await request_closure(user.id), 'message': 'Access blocked; deletion queued. Cleanup may take several minutes.'}


@router.get('/deletion-status')
async def deletion_status(user: AuthenticatedUser = Depends(get_current_user)):
    async with admin_db_session(reason='own_deletion_receipt') as db:
        row = await db.get(AccountClosure, user.id)
        return {'status': row.status if row else 'not_requested', 'error_code': row.error_code if row else None}
