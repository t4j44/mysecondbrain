from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.core.pagination import PaginatedResponse, PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.services import (
    AuditService,
    ExportService,
    IntegrationManagementService,
    get_audit_service,
    get_export_service,
    get_integration_service,
)
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
