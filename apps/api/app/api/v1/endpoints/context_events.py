from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import AwareDatetime
from sqlalchemy import select

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.models.entities import ContextMedia
from app.services.context_events import (
    EventInput,
    create_event,
    delete_event,
    event_list,
    event_view,
    get_event,
)

router = APIRouter(prefix='/context-events', tags=['Context events'])


@router.get('')
async def events(person_id: UUID | None = None, project_id: UUID | None = None,
                 start: AwareDatetime | None = None, end: AwareDatetime | None = None,
                 limit: int = Query(50, ge=1, le=100),
                 user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await event_list(db, user.id, person_id=person_id, project_id=project_id, start=start, end=end, limit=limit)


@router.post('')
async def create(payload: EventInput, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    values = payload.model_dump(exclude={'confirmed', 'request_id'})
    for key in ('person_id', 'project_id', 'venture_id'):
        values[key] = str(values[key]) if values[key] else None
    row, _ = await create_event(db, user.id, key='manual:' + str(payload.request_id), source_type='manual', **values)
    await db.commit()
    return event_view(row)


@router.get('/{event_id}')
async def read(event_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    event = await get_event(db, user.id, event_id)
    media = (await db.execute(select(ContextMedia).where(ContextMedia.user_id == user.id,
        ContextMedia.event_id == event.id))).scalars().all()
    return {**event_view(event), 'raw_text': event.raw_text, 'raw_payload': event.raw_payload,
        'media': [{'id': str(row.id), 'kind': row.kind} for row in media]}


@router.delete('/{event_id}')
async def remove(event_id: UUID, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    await delete_event(db, user.id, event_id)
    await db.commit()
    return {'deleted': True, 'notice': 'Search access removed. Private media erasure is queued.'}
