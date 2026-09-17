from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- PROFILE SCHEMAS (Task 10) ---
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    current_mission: Optional[str] = None
    avatar_url: Optional[str] = None
    onboarding_status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en-US"
    current_mission: Optional[str] = None
    avatar_url: Optional[str] = None
    onboarding_status: str = "in_progress"
    settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- VENTURES SCHEMAS (Task 12) ---
class VentureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    vision: Optional[str] = None
    mission: Optional[str] = None
    description: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|paused|archived|exited)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    metadata_payload: Dict[str, Any] = {}


class VentureUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    vision: Optional[str] = None
    mission: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|archived|exited)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class VentureResponse(BaseModel):
    id: str
    user_id: str
    name: str
    slug: str
    vision: Optional[str] = None
    mission: Optional[str] = None
    description: Optional[str] = None
    status: str
    priority: str
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    metadata_payload: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- PROJECTS SCHEMAS (Task 13) ---
class ProjectCreate(BaseModel):
    venture_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(
        default="in_progress", pattern="^(planned|in_progress|paused|completed|cancelled)$"
    )
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    progress: int = Field(default=0, ge=0, le=100)
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    venture_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(
        None, pattern="^(planned|in_progress|paused|completed|cancelled)$"
    )
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    progress: Optional[int] = Field(None, ge=0, le=100)
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: str
    priority: str
    progress: int
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- TASKS SCHEMAS (Task 14) ---
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    person_id: Optional[str] = None
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|cancelled)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_effort: Optional[str] = None
    tags: List[str] = []
    calendar_sync_metadata: Dict[str, Any] = {}


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    person_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|done|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    estimated_effort: Optional[str] = None
    tags: Optional[List[str]] = None
    calendar_sync_metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    person_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    estimated_effort: Optional[str] = None
    tags: List[str] = []
    calendar_sync_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- KPI SCHEMAS (Task 24) ---
class KPICreate(BaseModel):
    category: str = Field(..., pattern="^(founder|network|learning|venture)$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    unit: str = "count"
    target: float = 0.0
    period: str = "weekly"
    evidence_docs: List[str] = []
    is_active: bool = True


class KPIUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target: Optional[float] = None
    current_value: Optional[float] = None
    period: Optional[str] = None
    evidence_docs: Optional[List[str]] = None
    is_active: Optional[bool] = None


class KPIResponse(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    category: str
    name: str
    description: Optional[str] = None
    unit: str
    target: float
    current_value: float
    period: str
    evidence_docs: List[str] = []
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class KPIEntryCreate(BaseModel):
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    entry_date: Optional[datetime] = None


class KPIEntryUpdate(BaseModel):
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    entry_date: Optional[datetime] = None


class KPIEntryResponse(BaseModel):
    id: str
    kpi_id: str
    entry_date: datetime
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- WEEKLY REVIEW SCHEMAS (Task 28) ---
class WeeklyReviewCreate(BaseModel):
    title: str = Field(..., min_length=1)
    period_start: datetime
    period_end: datetime
    completed_tasks: List[Any] = []
    overdue_tasks: List[Any] = []
    project_progress: List[Any] = []
    meetings_summary: List[Any] = []
    interactions_summary: List[Any] = []
    new_ideas: List[Any] = []
    decisions_made: List[Any] = []
    achievements_recorded: List[Any] = []
    kpi_changes: List[Any] = []
    user_reflections: Optional[str] = None


class WeeklyReviewUpdate(BaseModel):
    title: Optional[str] = None
    user_reflections: Optional[str] = None


class WeeklyReviewResponse(BaseModel):
    id: str
    user_id: str
    title: str
    review_date: datetime
    period_start: datetime
    period_end: datetime
    completed_tasks: List[Any] = []
    overdue_tasks: List[Any] = []
    project_progress: List[Any] = []
    meetings_summary: List[Any] = []
    interactions_summary: List[Any] = []
    new_ideas: List[Any] = []
    decisions_made: List[Any] = []
    achievements_recorded: List[Any] = []
    kpi_changes: List[Any] = []
    user_reflections: Optional[str] = None
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- DASHBOARD SCHEMAS (Task 11) ---
class DashboardSummaryResponse(BaseModel):
    active_ventures_count: int = 0
    in_progress_projects_count: int = 0
    tasks_today: List[TaskResponse] = []
    overdue_tasks: List[TaskResponse] = []
    recent_memories: List[Any] = []
    kpi_highlights: List[KPIResponse] = []
    model_config = ConfigDict(from_attributes=True)


class DashboardInsightsResponse(BaseModel):
    ai_summary: str
    attention_required_projects: List[str] = []
    network_follow_ups: List[Any] = []
    productivity_velocity: Optional[float] = None
    recommendations: List[str] = []
    model_config = ConfigDict(from_attributes=True)
