from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from app.ai.indexing import SOURCES
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.models.entities import AuditLog
from app.services.enrichment import ClaimInput, ClaimReview, EnrichmentService, ResearchInput
from app.services.relationship_metrics import (
    WillingnessInput,
    activation,
    private_activity,
    record_home_observation,
)
from app.services.relationships import FollowupActionInput, RelationshipService, source

router = APIRouter(prefix='/relationships', tags=['Relationship intelligence'])
LinkKind = Literal['project', 'venture', 'meeting', 'document', 'organization', 'person', 'task', 'commitment']


class ConnectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    confirmed: Literal[True]
    kind: LinkKind
    record_id: UUID
    reason: str = Field(min_length=5, max_length=500)


@router.get('/link-options')
async def link_options(kind: LinkKind, query: str = Query(default='', max_length=100), user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    model: Any = SOURCES[kind][0]
    title = getattr(model, 'name', None)
    if title is None:
        title = getattr(model, 'title', None)
    if title is None:
        title = model.description
    rows = await RelationshipService(db, user.id).rows(model, title.icontains(query, autoescape=True), limit=30, order=title.asc())
    return [source(row, kind) for row in rows]


@router.post('/people/{person_id}/connections')
async def connect(person_id: UUID, payload: ConnectionInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).connect(person_id, payload.kind, payload.record_id, payload.reason)


@router.get('/records/{kind}/{record_id}/people')
async def record_people(kind: LinkKind, record_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await RelationshipService(db, user.id).people_for_record(kind, record_id)


@router.get('/home')
async def home(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    result = await RelationshipService(db, user.id).home()
    await record_home_observation(db, user.id, result['followups'])
    result['activation'] = await activation(db, user.id)
    await db.commit()
    return result


@router.get('/activity')
async def activity(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await private_activity(db, user.id)


@router.post('/willingness-to-pay')
async def willingness(payload: WillingnessInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    db.add(AuditLog(user_id=user.id, event_type='willingness_to_pay_' + payload.response,
        details={'plan': 'founding_member', 'monthly_usd': 5, 'survey_only': True}))
    await db.commit()
    return {'saved': True, 'notice': 'Interest recorded. No subscription or payment was created.'}


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


@router.post('/people/{person_id}/research')
async def research(person_id: UUID, payload: ResearchInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await EnrichmentService(db, user.id).research(person_id, payload)


@router.get('/people/{person_id}/claims')
async def claims(person_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await EnrichmentService(db, user.id).list(person_id)


@router.post('/people/{person_id}/claims')
async def propose_claim(person_id: UUID, payload: ClaimInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await EnrichmentService(db, user.id).propose(person_id, payload)


@router.post('/people/{person_id}/claims/{claim_id}/review')
async def review_claim(person_id: UUID, claim_id: UUID, payload: ClaimReview, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await EnrichmentService(db, user.id).review(person_id, claim_id, payload)


@router.delete('/people/{person_id}/claims/{claim_id}')
async def remove_claim(person_id: UUID, claim_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await EnrichmentService(db, user.id).remove(person_id, claim_id)
