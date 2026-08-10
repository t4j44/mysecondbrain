from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.pagination import PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.services import (
    DashboardService,
    KPIService,
    ProfileService,
    ProjectService,
    ReviewService,
    TaskService,
    VentureService,
    get_dashboard_service,
    get_kpi_service,
    get_profile_service,
    get_project_service,
    get_review_service,
    get_task_service,
    get_venture_service,
)
from app.schemas import (
    DashboardInsightsResponse,
    DashboardSummaryResponse,
    ProfileResponse,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    VentureCreate,
    VentureResponse,
    VentureUpdate,
    WeeklyReviewCreate,
    WeeklyReviewResponse,
)
from app.schemas.founder import KPICreate, KPIEntryCreate, KPIEntryResponse, KPIResponse

router = APIRouter()


# --- PROFILE ENDPOINTS (Task 10) ---
@router.get(
    "/me", response_model=ProfileResponse, summary="Get current authenticated founder profile"
)
async def read_my_profile(
    service: ProfileService = Depends(get_profile_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_my_profile(email=user.email)


@router.patch(
    "/me", response_model=ProfileResponse, summary="Update current founder profile details"
)
async def update_my_profile(
    payload: ProfileUpdate,
    service: ProfileService = Depends(get_profile_service),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_profile(
        data_dict=payload.model_dump(exclude_unset=True), email=user.email
    )


# --- DASHBOARD ENDPOINTS (Task 11) ---
@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="Retrieve real-time founder operational KPI summary",
)
async def read_dashboard_summary(
    timezone: str = Query(
        "UTC", description="Local timezone string for precise 'today' computation"
    ),
    service: DashboardService = Depends(get_dashboard_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_summary(timezone_str=timezone)


@router.get(
    "/dashboard/insights",
    response_model=DashboardInsightsResponse,
    summary="Generate automated executive AI operating guidance",
)
async def read_dashboard_insights(
    service: DashboardService = Depends(get_dashboard_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_insights()


# --- VENTURES ENDPOINTS (Task 12) ---
@router.post(
    "/ventures",
    response_model=VentureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new strategic venture",
)
async def create_venture(
    payload: VentureCreate,
    service: VentureService = Depends(get_venture_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_venture(payload.model_dump())


@router.get(
    "/ventures", response_model=dict, summary="List user strategic ventures with pagination"
)
async def list_ventures(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: VentureService = Depends(get_venture_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(
        limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
    )
    res = await service.list_ventures(pagination)
    return res.model_dump()


@router.get("/ventures/{id}", response_model=VentureResponse, summary="Get venture details by ID")
async def read_venture(
    id: str,
    service: VentureService = Depends(get_venture_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_venture(id)


@router.patch(
    "/ventures/{id}", response_model=VentureResponse, summary="Update strategic venture attributes"
)
async def update_venture(
    id: str,
    payload: VentureUpdate,
    service: VentureService = Depends(get_venture_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_venture(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/ventures/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive or delete strategic venture",
)
async def delete_venture(
    id: str,
    service: VentureService = Depends(get_venture_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.archive_or_delete_venture(id)


# --- PROJECTS ENDPOINTS (Task 13) ---
@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an actionable product project",
)
async def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_project(payload.model_dump())


@router.get("/projects", response_model=dict, summary="List actionable projects across ventures")
async def list_projects(
    venture_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ProjectService = Depends(get_project_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_projects(pagination, venture_id=venture_id)
    return res.model_dump()


@router.get("/projects/{id}", response_model=ProjectResponse, summary="Get project details by ID")
async def read_project(
    id: str,
    service: ProjectService = Depends(get_project_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_project(id)


@router.patch(
    "/projects/{id}", response_model=ProjectResponse, summary="Update project progress or status"
)
async def update_project(
    id: str,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_project(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/projects/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archive project record"
)
async def delete_project(
    id: str,
    service: ProjectService = Depends(get_project_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_project(id)


# --- TASKS ENDPOINTS (Task 14) ---
@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create operational founder task",
)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_task(payload.model_dump())


@router.get("/tasks", response_model=dict, summary="List operational founder task queue")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: TaskService = Depends(get_task_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_tasks(pagination, status=status)
    return res.model_dump()


@router.get("/tasks/{id}", response_model=TaskResponse, summary="Get task details by ID")
async def read_task(
    id: str,
    service: TaskService = Depends(get_task_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_task(id)


@router.patch(
    "/tasks/{id}",
    response_model=TaskResponse,
    summary="Update task attributes and execution states",
)
async def update_task(
    id: str,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_task(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove task from active queue"
)
async def delete_task(
    id: str,
    service: TaskService = Depends(get_task_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_task(id)


# --- KPI ENDPOINTS (Task 24) ---
@router.post(
    "/kpis",
    response_model=KPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define new founder performance metric",
)
async def create_kpi(
    payload: KPICreate,
    service: KPIService = Depends(get_kpi_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_kpi(payload.model_dump())


@router.get("/kpis", response_model=dict, summary="List active founder and venture KPIs")
async def list_kpis(
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: KPIService = Depends(get_kpi_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_kpis(pagination, category=category)
    return res.model_dump()


@router.post(
    "/kpis/{kpi_id}/entries",
    response_model=KPIEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record longitudinal KPI datapoint",
)
async def record_kpi_entry(
    kpi_id: str,
    payload: KPIEntryCreate,
    service: KPIService = Depends(get_kpi_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.record_entry(kpi_id, payload.model_dump(exclude_unset=True))


# --- WEEKLY REVIEWS ENDPOINTS (Task 28) ---
@router.post(
    "/reviews/weekly",
    response_model=WeeklyReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compile weekly founder review",
)
async def create_weekly_review(
    payload: WeeklyReviewCreate,
    service: ReviewService = Depends(get_review_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_review(payload.model_dump())


@router.get(
    "/reviews/weekly", response_model=dict, summary="List archived weekly founder operating reviews"
)
async def list_weekly_reviews(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ReviewService = Depends(get_review_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_reviews(pagination)
    return res.model_dump()
