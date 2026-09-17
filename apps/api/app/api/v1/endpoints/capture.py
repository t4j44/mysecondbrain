from fastapi import APIRouter, Depends

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.services.capture import CaptureConfirm, CaptureInput, CaptureService

router = APIRouter(prefix="/capture", tags=["Capture"])


@router.post("/propose")
async def propose(payload: CaptureInput, user: AuthenticatedUser = Depends(get_current_user),
                  db=Depends(get_rls_db_session)):
    return await CaptureService(db, user.id).propose(payload)


@router.post("/{draft_id}/confirm")
async def confirm(draft_id: str, payload: CaptureConfirm,
                  user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await CaptureService(db, user.id).confirm(draft_id, payload)
