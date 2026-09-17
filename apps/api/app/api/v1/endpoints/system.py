from datetime import timedelta
from typing import Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import Response
from pydantic import AwareDatetime, BaseModel, Field
from sqlalchemy import select

from app.core.errors import NotFoundError, ValidationError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_rls_db_session
from app.dependencies.services import (
    AuditService,
    ExportService,
    IntegrationManagementService,
    get_audit_service,
    get_export_service,
    get_integration_service,
)
from app.integrations.google_client import GoogleIntegrationService
from app.models.entities import JobRecord, Task
from app.schemas import (
    AuditLogResponse,
    ExportRequest,
    ExportResponse,
    GoogleCallbackRequest,
    GoogleCallbackResponse,
    IntegrationResponse,
    JobResponse,
    SyncCalendarRequest,
    SyncDriveRequest,
)

router = APIRouter()


@router.get('/exports/{export_id}/download')
async def download_export(export_id: str, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.integrations.storage_client import StorageService
    from app.repositories.integrations import ExportRepository
    record = await ExportRepository().get_by_id(db, user.id, export_id)
    if not record or record.status != 'completed' or not record.file_path:
        raise NotFoundError('Export is not ready.')
    if not record.file_path.startswith(f'{user.id}/'):
        raise NotFoundError('Export is not available.')
    content = await StorageService().read_file(record.file_path)
    return Response(content, media_type='text/markdown', headers={
        'Content-Disposition': 'attachment; filename="second-brain-export.md"',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@router.post("/integrations/google/authorize")
async def google_authorize(provider: Literal["google_drive", "google_calendar"],
                           user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return await GoogleIntegrationService(db, user.id).authorize(provider)


@router.delete("/integrations/google/{provider}")
async def google_disconnect(provider: Literal["google_drive", "google_calendar"],
                           user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    return {"disconnected": await GoogleIntegrationService(db, user.id).disconnect_provider(provider)}


class CalendarSchedule(BaseModel):
    start: AwareDatetime
    duration_minutes: int = Field(default=30, ge=5, le=1440)
    timezone: str = "Asia/Dhaka"
    cancel: bool = False


@router.post("/integrations/google/tasks/{task_id}/schedule", status_code=202)
async def schedule_task(task_id: str, payload: CalendarSchedule,
                        user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    try:
        ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError:
        raise ValidationError("Choose a valid timezone.") from None
    task = (await db.execute(select(Task).where(Task.id == task_id,
        Task.user_id == user.id, Task.deleted_at.is_(None)))).scalar_one_or_none()
    if task is None:
        raise NotFoundError("Task not found.")
    await GoogleIntegrationService(db, user.id).access_token("google_calendar")
    task.calendar_sync_metadata = {**(task.calendar_sync_metadata or {}), "enabled": True, "cancel": payload.cancel,
        "start": payload.start.isoformat(), "end": (payload.start + timedelta(minutes=payload.duration_minutes)).isoformat(),
        "timezone": payload.timezone, "status": "pending"}
    job = JobRecord(user_id=user.id, job_type="sync_google_calendar", status="pending",
                    result_payload={"task_id": str(task.id), "calendar_id": "primary"})
    db.add(job)
    await db.commit()
    return {"job_id": str(job.id), "status": "pending"}


@router.get("/jobs/{job_id}")
async def job_status(job_id: str, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    job = (await db.execute(select(JobRecord).where(JobRecord.id == job_id,
        JobRecord.user_id == user.id))).scalar_one_or_none()
    if not job:
        raise NotFoundError("Job not found.")
    return {"id": str(job.id), "status": job.status, "error_code": job.error_code,
            "retry_count": job.retry_count}


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    from app.jobs.runner import RUNNABLE
    job = (await db.execute(select(JobRecord).where(JobRecord.id == job_id,
        JobRecord.user_id == user.id).with_for_update())).scalar_one_or_none()
    if not job or job.job_type not in RUNNABLE or job.status != "failed":
        raise NotFoundError("No failed job available to retry.")
    job.status, job.retry_count = "pending", 0
    await db.commit()
    return {"status": "pending"}


# --- INTEGRATIONS ENDPOINTS (Tasks 29, 30, 31) ---
@router.get(
    "/integrations",
    response_model=PaginatedResponse[IntegrationResponse],
    summary="List configured third-party integration statuses without leaking encrypted tokens",
)
async def list_integrations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: IntegrationManagementService = Depends(get_integration_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_integrations(pagination)
    return res


@router.post(
    "/integrations/google/callback",
    response_model=GoogleCallbackResponse,
    summary="Process Google OAuth authorization code callback and encrypt tokens",
)
async def google_oauth_callback(
    payload: GoogleCallbackRequest,
    service: IntegrationManagementService = Depends(get_integration_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    res = await service.handle_google_callback(payload.code, payload.state)
    return GoogleCallbackResponse(**res)


@router.post(
    "/sync/gdrive",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger background Drive synchronization task",
)
async def sync_google_drive(
    background_tasks: BackgroundTasks,
    payload: Optional[SyncDriveRequest] = None,
    service: IntegrationManagementService = Depends(get_integration_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    req = payload or SyncDriveRequest()
    job = await service.trigger_drive_sync(
        req.folder_id, req.sync_mode, background_tasks=background_tasks
    )
    return job


@router.post(
    "/sync/calendar",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Google Calendar scheduled event ingestion job",
)
async def sync_google_calendar(
    background_tasks: BackgroundTasks,
    payload: Optional[SyncCalendarRequest] = None,
    service: IntegrationManagementService = Depends(get_integration_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    req = payload or SyncCalendarRequest()
    job = await service.trigger_calendar_sync(
        req.calendar_id or "primary", background_tasks=background_tasks
    )
    return job


# --- EXPORT ENDPOINTS (Task 32) ---
@router.post(
    "/exports",
    response_model=ExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue background Markdown archive export job",
)
@router.post(
    "/export/markdown",
    response_model=ExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Markdown export (api_contracts.md standard)",
)
async def trigger_markdown_export(
    background_tasks: BackgroundTasks,
    payload: Optional[ExportRequest] = None,
    service: ExportService = Depends(get_export_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    req = payload or ExportRequest()
    exp = await service.trigger_export_job(
        req.export_type, req.target_module, req.record_id, background_tasks=background_tasks
    )
    return exp


@router.get(
    "/exports",
    response_model=PaginatedResponse[ExportResponse],
    summary="List generated export archives with temporary signed access links",
)
async def list_exports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ExportService = Depends(get_export_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.get_export_history(pagination)
    return res


# --- AUDIT LOGS ENDPOINTS ---
@router.get(
    "/audit-logs",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Inspect system audit events and security access tracking",
)
async def read_audit_logs(
    event_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AuditService = Depends(get_audit_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_audit_logs(pagination, event_type=event_type)
    return res
