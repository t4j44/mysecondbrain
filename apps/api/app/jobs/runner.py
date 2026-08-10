from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.dependencies.database import AsyncSessionLocal
from app.repositories.integrations import JobRepository


class JobRunner:
    @classmethod
    async def run_job_by_id(cls, job_id: str) -> None:
        async with AsyncSessionLocal() as db:
            repo = JobRepository()
            job = await repo.get_by_id_unscoped(db, id=job_id)
            if not job or job.status in {"completed"}:
                return

            job.status = "processing"
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                result = await cls._execute_payload(
                    db, job.user_id, job.job_type, job.result_payload
                )
                job.status = "completed"
                job.result_payload = result
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as exc:
                job.retry_count += 1
                job.error_code = "TASK_EXECUTION_FAILURE"
                job.error_message = str(exc)
                job.status = "failed" if job.retry_count >= 3 else "pending"
                job.updated_at = datetime.now(timezone.utc)
                await db.commit()
                logger.error(
                    f"Job {job_id} ({job.job_type}) failed on try {job.retry_count}: {str(exc)}",
                    exc_info=True,
                )

    @staticmethod
    async def _execute_payload(
        db: AsyncSession, user_id: str, job_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        from app.jobs.handlers.document_processing import process_document_handler
        from app.jobs.handlers.export_markdown import execute_export_handler
        from app.jobs.handlers.sync_google import execute_google_sync_handler

        if job_type == "document_processing":
            return await process_document_handler(db, user_id, payload)
        elif job_type in {"export_markdown", "export_archive"}:
            return await execute_export_handler(db, user_id, payload)
        elif job_type in {"sync_google_drive", "sync_google_calendar"}:
            return await execute_google_sync_handler(db, user_id, payload, job_type)
        else:
            raise ValueError(f"Unsupported job execution profile: {job_type}")


async def process_job_async(job_id: str) -> None:
    try:
        await JobRunner.run_job_by_id(job_id)
    except Exception as e:
        logger.error(f"Background task dispatch terminated abnormally: {str(e)}", exc_info=True)
