"""
Pydantic Schemas for Idea Vault & Strategic Validation Module
Module Owner: Agent 9
Enforces zero client-supplied ownership & structured assumption verification.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IdeaStatus(str, Enum):
    CAPTURED = "captured"
    EXPLORING = "exploring"
    VALIDATING = "validating"
    PRIORITIZED = "prioritized"
    BUILDING = "building"
    PAUSED = "paused"
    REJECTED = "rejected"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    # COMPATIBILITY WITH SIMPLE SQL CHECK CONSTRAINTS
    DRAFT = "draft"
    EXECUTING = "executing"
    CONVERTED = "converted"


class AssumptionCategory(str, Enum):
    PROBLEM = "problem"
    USER = "user"
    MARKET = "market"
    SOLUTION = "solution"
    DISTRIBUTION = "distribution"
    REVENUE = "revenue"
    TECHNICAL = "technical"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"


class AssumptionImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssumptionEvidenceStatus(str, Enum):
    UNTESTED = "untested"
    SUPPORTED = "supported"
    INVALIDATED = "invalidated"


class StructuredAssumption(BaseModel):
    id: str = Field(..., description="Unique identifier for assumption")
    statement: str = Field(..., min_length=3, description="Clear hypothesis statement")
    category: AssumptionCategory
    importance: AssumptionImportance = AssumptionImportance.MEDIUM
    evidence_status: AssumptionEvidenceStatus = AssumptionEvidenceStatus.UNTESTED
    validation_method: Optional[str] = None
    result: Optional[str] = None
    notes: Optional[str] = None


class ValidationExperiment(BaseModel):
    id: str
    idea_id: str
    validation_question: str = Field(..., min_length=5)
    hypothesis: str
    method: str = Field(..., description="e.g. user_interview, prototype_test")
    target_participants: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    result: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    conclusion: Optional[str] = None
    next_action: Optional[str] = None


class IdeaEvidenceLink(BaseModel):
    record_id: str
    record_type: str = Field(
        ..., description="memory, meeting, person, document, decision, project"
    )
    title: str
    date_recorded: str
    excerpt: Optional[str] = None


class IdeaAIAnalysisResult(BaseModel):
    problem_clarity_score: int = Field(..., ge=1, le=10)
    solution_viability_score: int = Field(..., ge=1, le=10)
    target_user_specificity: str
    strategic_fit_summary: str
    similar_internal_ideas: List[Dict[str, Any]] = Field(default_factory=list)
    major_untested_assumptions: List[StructuredAssumption] = Field(default_factory=list)
    recommended_next_experiment: Optional[Dict[str, Any]] = None
    generated_at: datetime
    provider: str = "gemini"
    model: str = "gemini-1.5-pro"
    prompt_version: str = "1.0.0"
    citations: List[Dict[str, str]] = Field(default_factory=list)


# --- API REQUEST MODELS (Client-Supplied Ownership Banned) ---
class IdeaCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    problem: Optional[str] = None
    solution: Optional[str] = None
    target_users: Optional[str] = None
    market: Optional[str] = None
    venture_id: Optional[str] = None
    potential_score: Optional[int] = Field(None, ge=1, le=10)
    status: IdeaStatus = IdeaStatus.CAPTURED
    next_steps: Optional[str] = None
    assumptions: List[StructuredAssumption] = Field(default_factory=list)
    experiments: List[ValidationExperiment] = Field(default_factory=list)
    evidence_links: List[IdeaEvidenceLink] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IdeaUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    problem: Optional[str] = None
    solution: Optional[str] = None
    target_users: Optional[str] = None
    market: Optional[str] = None
    venture_id: Optional[str] = None
    potential_score: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[IdeaStatus] = None
    next_steps: Optional[str] = None
    assumptions: Optional[List[StructuredAssumption]] = None
    experiments: Optional[List[ValidationExperiment]] = None
    evidence_links: Optional[List[IdeaEvidenceLink]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class IdeaToProjectConvertRequest(BaseModel):
    name: Optional[str] = None
    venture_id: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    initial_tasks: List[Dict[str, str]] = Field(default_factory=list)


# --- API RESPONSE MODELS (Wrapped Standard) ---
class IdeaResource(IdeaCreateRequest):
    id: str
    user_id: str  # Added strictly by server after RLS session extraction
    ai_validation_summary: Optional[str] = None
    ai_analysis: Optional[IdeaAIAnalysisResult] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IdeaResponse(BaseModel):
    data: IdeaResource
    meta: Dict[str, Any]


class IdeaListResponse(BaseModel):
    data: List[IdeaResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any]


class ConvertProjectData(BaseModel):
    new_project_id: str
    source_idea_id: str
    idea_status: IdeaStatus
    converted_at: datetime


class IdeaConversionResponse(BaseModel):
    data: ConvertProjectData
    meta: Dict[str, Any]
