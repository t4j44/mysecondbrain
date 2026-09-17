"""Authenticated source inspection and explicit reindexing for citations."""
from uuid import UUID

from fastapi import APIRouter, Depends

from app.ai.indexing import owned_record, record_text
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.models.entities import AuditLog, JobRecord

router = APIRouter(prefix='/sources', tags=['Sources'])


@router.get('/{kind}/{record_id}')
async def read_source(kind: str, record_id: UUID,
                      user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    record = await owned_record(db, user.id, kind, str(record_id))
    db.add(AuditLog(user_id=user.id, event_type='beta_source_opened', details={'kind': kind}))
    await db.commit()
    return {'id': str(record.id), 'entity_type': kind, 'text': record_text(record, kind),
            'updated_at': record.updated_at,
            'title': getattr(record, 'title', None) or getattr(record, 'name', None) or getattr(record, 'filename', kind)}


@router.post('/{kind}/{record_id}/index', status_code=202)
async def reindex_source(kind: str, record_id: UUID,
                         user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    await owned_record(db, user.id, kind, str(record_id))
    job = JobRecord(user_id=user.id, job_type='document_processing' if kind == 'document' else 'index_record',
                    status='pending', result_payload={'kind': kind, 'record_id': str(record_id), 'document_id': str(record_id)})
    db.add(job)
    await db.commit()
    return {'job_id': str(job.id), 'status': 'pending'}
