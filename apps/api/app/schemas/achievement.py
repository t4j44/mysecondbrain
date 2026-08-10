"""
Pydantic Schemas for Achievement Portfolio & Career Proof
Module Owner: Agent 9
Enforces strict evidence-before-claims rules and verification status auditing.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VerificationStatus(str, Enum):
    SELF_REPORTED = "self_reported"
    SUPPORTED = "supported"
    VERIFIED = "verified"
    NEEDS_EVIDENCE = "needs_evidence"


class AchievementEvidenceResource(BaseModel):
    id: Optional[str] = None
    achievement_id: Optional[str] = None
    source_id: str
    source_type: str = Field(
        ...,
        description="project, task, decision, document, meeting, memory, kpi_entry, person, external_url",
    )
    source_title: str
    source_date: str
    external_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AchievementCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    role: str = Field(
        ..., min_length=2, max_length=100, description="e.g. Founder & AI Product Manager"
    )
    description: Optional[str] = None
    problem: Optional[str] = None
    context: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    impact: str = Field(
        ..., min_length=10, description="Quantified KPI outcome or validated qualitative impact"
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Demonstrated competencies e.g. RAG Systems, Product Strategy",
    )
    achievement_date: date = Field(default_factory=date.today)
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    visibility: str = Field(default="private", description="private, portfolio_ready, public")
    evidence_items: List[AchievementEvidenceResource] = Field(default_factory=list)
    related_people_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AchievementUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=150)
    role: Optional[str] = None
    description: Optional[str] = None
    problem: Optional[str] = None
    context: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    impact: Optional[str] = None
    skills: Optional[List[str]] = None
    achievement_date: Optional[date] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    visibility: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None
    evidence_items: Optional[List[AchievementEvidenceResource]] = None
    related_people_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AchievementResource(AchievementCreateRequest):
    id: str
    user_id: str
    verification_status: VerificationStatus = VerificationStatus.SELF_REPORTED
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AchievementResponse(BaseModel):
    data: AchievementResource
    meta: Dict[str, Any]


class AchievementListResponse(BaseModel):
    data: List[AchievementResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any]
