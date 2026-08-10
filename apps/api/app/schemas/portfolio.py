"""
Pydantic Schemas for Career Proof Case Studies & Portfolio
Module Owner: Agent 9
Supports AI grounded case study generation without fabricated metrics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCoverageState(BaseModel):
    problem: str = "supported"
    role: str = "supported"
    responsibilities: str = "supported"
    actions: str = "supported"
    impact: str = "partially_supported"
    skills: str = "supported"


class CaseStudyCitation(BaseModel):
    record_id: str
    record_type: str
    claim_supported: str
    url_or_path: str


class GenerateCaseStudyRequest(BaseModel):
    target_role: str = Field(
        ...,
        min_length=3,
        description="Target role e.g. AI Product Manager or Chief Product Officer",
    )
    target_audience: Optional[str] = Field("Recruiters & VCs", description="Audience context")
    selected_achievement_ids: List[str] = Field(
        ..., min_length=1, description="Selected achievements from public.achievements"
    )
    selected_project_ids: List[str] = Field(default_factory=list)
    selected_decision_ids: List[str] = Field(default_factory=list)
    selected_document_ids: List[str] = Field(default_factory=list)
    selected_kpi_entry_ids: List[str] = Field(default_factory=list)
    length: str = Field(default="standard", description="compact, standard, in_depth")
    tone: Optional[str] = "Authoritative, fact-based, operational, retro-editorial"


class ManualCaseStudyCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    target_role: str
    target_audience: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    executive_summary: str = Field(..., min_length=10)
    full_markdown_case: str = Field(..., min_length=20)
    linked_achievement_ids: List[str] = Field(default_factory=list)
    is_public: bool = False
    status: str = "draft"


class CaseStudyUpdateRequest(BaseModel):
    title: Optional[str] = None
    target_role: Optional[str] = None
    executive_summary: Optional[str] = None
    full_markdown_case: Optional[str] = None
    linked_achievement_ids: Optional[List[str]] = None
    is_public: Optional[bool] = None
    status: Optional[str] = None  # draft | approved | archived


class CaseStudyResource(ManualCaseStudyCreateRequest):
    id: str
    user_id: str
    section_coverage: Optional[EvidenceCoverageState] = Field(default_factory=EvidenceCoverageState)
    citations: List[CaseStudyCitation] = Field(default_factory=list)
    is_ai_generated: bool = False
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    prompt_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CaseStudyResponse(BaseModel):
    data: CaseStudyResource
    meta: Dict[str, Any]


class CaseStudyListResponse(BaseModel):
    data: List[CaseStudyResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any]
