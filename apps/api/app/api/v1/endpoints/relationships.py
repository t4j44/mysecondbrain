from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.services.relationships import FollowupActionInput, RelationshipService

router = APIRouter(prefix='/relationships', tags=['Relationship intelligence'])


@router.get('/home')
async def home(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).home()


@router.get('/followups')
async def followups(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).followups()


@router.get('/people/{person_id}')
async def profile(person_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).profile(person_id)


class DraftInput(BaseModel):
    suggestion_key: str = Field(min_length=1, max_length=200)


@router.post('/people/{person_id}/draft')
async def draft(person_id: UUID, payload: DraftInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).draft(person_id, payload.suggestion_key)


@router.post('/people/{person_id}/actions')
async def act(person_id: UUID, payload: FollowupActionInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).act(person_id, payload)
