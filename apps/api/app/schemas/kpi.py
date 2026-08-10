"""
Pydantic Schemas for Life KPI System & Founder Metrics
Module Owner: Agent 9
Enforces historical measurement integrity & non-vanity formulas.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class KPICategory(str, Enum):
    FOUNDER = "founder"
    NETWORK = "network"
    LEARNING = "learning"
    VENTURE = "venture"


class KPIPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class KPIDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    MILESTONE = "milestone"


class KPITrend(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class KPIEvidenceRef(BaseModel):
    record_id: str
    record_type: str
    title: str
    url_or_path: Optional[str] = None
    date_attached: str


# --- ENTRY MODELS ---
class KPIEntryCreateRequest(BaseModel):
    recorded_value: float = Field(..., description="Numeric measurement value")
    text_value: Optional[str] = Field(None, description="Optional qualitative or milestone state")
    notes: Optional[str] = None
    recording_date: date = Field(default_factory=date.today)
    evidence_refs: List[KPIEvidenceRef] = Field(default_factory=list)


class KPIEntryUpdateRequest(BaseModel):
    recorded_value: Optional[float] = None
    text_value: Optional[str] = None
    notes: Optional[str] = None
    evidence_refs: Optional[List[KPIEvidenceRef]] = None


class KPIEntryResource(BaseModel):
    id: str
    user_id: str
    kpi_id: str
    recorded_value: float
    text_value: Optional[str] = None
    notes: Optional[str] = None
    recording_date: date
    evidence_refs: List[KPIEvidenceRef] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- DEFINITION MODELS ---
class KPIDefinitionCreateRequest(BaseModel):
    category: Union[KPICategory, str] = Field(
        default="founder", description="Category or custom string"
    )
    metric_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    target_value: float = Field(default=0.0)
    unit: str = Field(default="count")
    period: KPIPeriod = KPIPeriod.WEEKLY
    direction: KPIDirection = KPIDirection.HIGHER_IS_BETTER
    related_venture_id: Optional[str] = None
    related_project_id: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KPIDefinitionUpdateRequest(BaseModel):
    category: Optional[Union[KPICategory, str]] = None
    metric_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    period: Optional[KPIPeriod] = None
    direction: Optional[KPIDirection] = None
    related_venture_id: Optional[str] = None
    related_project_id: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class KPIDefinitionResource(KPIDefinitionCreateRequest):
    id: str
    user_id: str
    current_value: float = 0.0
    calculated_progress: Optional[float] = None
    calculated_trend: Optional[KPITrend] = KPITrend.INSUFFICIENT_DATA
    latest_entries: List[KPIEntryResource] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- WRAPPED RESPONSES ---
class KPIResponse(BaseModel):
    data: KPIDefinitionResource
    meta: Dict[str, Any]


class KPIListResponse(BaseModel):
    data: List[KPIDefinitionResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any]


class KPIEntryResponse(BaseModel):
    data: KPIEntryResource
    meta: Dict[str, Any]


class KPIEntryListResponse(BaseModel):
    data: List[KPIEntryResource]
    meta: Dict[str, Any]
