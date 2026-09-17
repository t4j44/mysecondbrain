"""Durable queue; atomic claims and owner-scoped execution."""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select

from app.core.logging import logger
from app.dependencies.database import admin_db_session, rls_db_session
from app.models.entities import ExportRecord, JobRecord

RUNNABLE = {'document_processing', 'index_record', 'export_markdown', 'export_archive', 'sync_google_drive', 'sync_google_calendar'}

class JobRunner:
    @classmethod
    async def run_job_by_id(cls, job_id: str) -> None:
        async with admin_db_session(reason='job_claim') as db:
            job = (await db.execute(select(JobRecord).where(JobRecord.id == job_id).with_for_update(skip_locked=True))).scalar_one_or_none()
            if not job or job.job_type not in RUNNABLE or job.status != 'pending':
                return
            owner, kind, payload = str(job.user_id), job.job_type, job.result_payload
            claimed_at = datetime.now(timezone.utc)
            job.status, job.started_at = 'processing', claimed_at
            await db.commit()
        try:
            async with rls_db_session(owner) as db:
                async with asyncio.timeout(600):
                    result = await cls._execute_payload(db, owner, kind, payload)
                    await db.commit()
            async with admin_db_session(reason='job_completion') as db:
                job = (await db.execute(select(JobRecord).where(JobRecord.id == job_id,
                    JobRecord.started_at == claimed_at, JobRecord.status == 'processing').with_for_update())).scalar_one_or_none()
                if job is None:
                    return
                job.status, job.completed_at = 'completed', datetime.now(timezone.utc)
                job.result_payload = {**payload, 'result': result}
                job.error_code = job.error_message = None
                await db.commit()
        except Exception as exc:
            async with admin_db_session(reason='job_failure') as db:
                job = (await db.execute(select(JobRecord).where(JobRecord.id == job_id,
                    JobRecord.started_at == claimed_at, JobRecord.status == 'processing').with_for_update())).scalar_one_or_none()
                if job is None:
                    return
                job.retry_count = (job.retry_count or 0) + 1
                job.status = 'failed' if job.retry_count >= 3 else 'pending'
                job.error_code = getattr(exc, 'code', 'JOB_FAILED')
                job.error_message = 'Processing failed. Check configuration and retry.'
                job.updated_at = datetime.now(timezone.utc)
                if kind in {'export_markdown', 'export_archive'} and payload.get('export_id'):
                    export = (await db.execute(select(ExportRecord).where(
                        ExportRecord.id == payload['export_id'], ExportRecord.user_id == owner,
                    ))).scalar_one_or_none()
                    if export is not None:
                        export.status = 'failed' if job.status == 'failed' else 'pending'
                        export.retry_count = job.retry_count
                await db.commit()
            logger.warning('Job failed', extra={'job_id': job_id, 'error_type': type(exc).__name__})

    @staticmethod
    async def _execute_payload(db, user_id: str, job_type: str, payload: dict) -> dict:
        if job_type == 'index_record':
            from app.ai.indexing import index_record
            return await index_record(db, user_id, payload['kind'], payload['record_id'])
        if job_type == 'document_processing':
            from app.jobs.handlers.document_processing import process_document_handler
            return await process_document_handler(db, user_id, payload)
        if job_type in {'export_markdown', 'export_archive'}:
            from app.jobs.handlers.export_markdown import execute_export_handler
            return await execute_export_handler(db, user_id, payload)
        if job_type in {'sync_google_drive', 'sync_google_calendar'}:
            from app.jobs.handlers.sync_google import execute_google_sync_handler
            return await execute_google_sync_handler(db, user_id, payload, job_type)
        raise ValueError('Unsupported job type')

async def process_job_async(job_id: str) -> None:
    await JobRunner.run_job_by_id(job_id)

async def queue_worker() -> None:
    while True:
        try:
            async with admin_db_session(reason='queue_poll') as db:
                now = datetime.now(timezone.utc)
                jobs = (await db.execute(select(JobRecord).where(
                    JobRecord.job_type.in_(RUNNABLE),
                    or_(JobRecord.status == 'pending', (JobRecord.status == 'processing') &
                        (JobRecord.started_at < now - timedelta(minutes=15))),
                ).order_by(JobRecord.created_at).limit(20).with_for_update(skip_locked=True))).scalars().all()
                ready = []
                for job in jobs:
                    if job.status == 'processing':
                        job.status = 'pending'
                    updated = job.updated_at.replace(tzinfo=timezone.utc) if job.updated_at.tzinfo is None else job.updated_at
                    if not job.retry_count or updated < now - timedelta(seconds=60 * job.retry_count):
                        ready.append(str(job.id))
                await db.commit()
            for job_id in ready:
                await process_job_async(job_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning('Queue poll failed (%s)', type(exc).__name__)
        await asyncio.sleep(15)
