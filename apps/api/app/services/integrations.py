from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks

from app.core.pagination import PaginatedResponse, PaginationParams
from app.integrations.google_client import GoogleIntegrationService
from app.models.entities import AuditLog, ExportRecord, Integration, JobRecord
from app.repositories.integrations import (
    AuditLogRepository,
    ExportRepository,
    IntegrationRepository,
    JobRepository,
)


class IntegrationManagementService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = IntegrationRepository()
        self.google_service = GoogleIntegrationService(db, user_id)

    async def list_integrations(
        self, pagination: PaginationParams
    ) -> PaginatedResponse[Integration]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)

    async def handle_google_callback(self, code: str, state: Optional[str]) -> Dict[str, Any]:
        res = await self.google_service.connect_oauth_callback(code, state)
        await self.db.commit()
        return res

    async def trigger_drive_sync(
        self, folder_id: Optional[str], sync_mode: str, background_tasks: Optional[BackgroundTasks]
    ) -> JobRecord:
        job = await self.google_service.trigger_drive_sync_job(folder_id, sync_mode)
        await self.db.commit()
        if background_tasks:
            from app.jobs.runner import process_job_async

            background_tasks.add_task(process_job_async, job.id)
        return job

    async def trigger_calendar_sync(
        self, calendar_id: str, background_tasks: Optional[BackgroundTasks]
    ) -> JobRecord:
        job = await self.google_service.trigger_calendar_sync_job(calendar_id)
        await self.db.commit()
        if background_tasks:
            from app.jobs.runner import process_job_async

            background_tasks.add_task(process_job_async, job.id)
        return job


class ExportService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = ExportRepository()
        self.job_repo = JobRepository()

    async def trigger_export_job(
        self,
        export_type: str,
        target_module: Optional[str],
        record_id: Optional[str],
        background_tasks: Optional[BackgroundTasks],
    ) -> ExportRecord:
        exp_record = await self.repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "export_type": export_type,
                "status": "pending",
            },
        )
        await self.db.flush()

        job = await self.job_repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "job_type": "export_markdown",
                "status": "pending",
                "result_payload": {
                    "export_id": exp_record.id,
                    "export_type": export_type,
                    "target_module": target_module,
                },
            },
        )
        await self.db.commit()

        if background_tasks:
            from app.jobs.runner import process_job_async

            background_tasks.add_task(process_job_async, job.id)

        return exp_record

    async def get_export_history(
        self, pagination: PaginationParams
    ) -> PaginatedResponse[ExportRecord]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination)


class AuditService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = AuditLogRepository()

    async def log_event(
        self,
        event_type: str,
        entity: Optional[str],
        target_id: Optional[str],
        details: dict,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        log = await self.repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "event_type": event_type,
                "target_entity": entity,
                "target_id": target_id,
                "details": details,
                "request_id": request_id,
            },
        )
        await self.db.commit()
        return log

    async def list_audit_logs(
        self, pagination: PaginationParams, event_type: Optional[str] = None
    ) -> PaginatedResponse[AuditLog]:
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        return await self.repo.list(self.db, self.user_id, pagination, **filters)
