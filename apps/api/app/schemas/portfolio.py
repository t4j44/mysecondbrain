"""
Pydantic Schemas for Senior Product Intelligence, Evidence & Career Portfolio Engine
Strictly grounds all professional claims in verified Second Brain evidence without fabricated metrics.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# SKILL TAXONOMY
# ============================================================================

SKILL_TAXONOMY = [
    "Product Management",
    "Market Research",
    "Competitive Intelligence",
    "TAM/SAM/SOM",
    "Technical Architecture",
    "AI Engineering",
    "RAG Design",
    "UI/UX",
    "Product Strategy",
    "GTM",
    "Founder Sales",
    "Partnerships",
    "Creative Direction",
    "Video Production",
    "Research",
    "Leadership",
    "Operations",
]


# ============================================================================
# 1. WORK SESSION SCHEMAS
# ============================================================================

class WorkSessionCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    objective: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int = Field(default=0, ge=0)
    summary: Optional[str] = None
    outcomes: Optional[str] = None
    artifacts_created: List[str] = Field(default_factory=list)
    decisions_made: List[str] = Field(default_factory=list)
    skills_exercised: List[str] = Field(default_factory=list)
    source: str = Field(default="manual_log", description="manual_log, ide_tracker, git_session, calendar_sync")
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)


class WorkSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    objective: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    summary: Optional[str] = None
    outcomes: Optional[str] = None
    artifacts_created: Optional[List[str]] = None
    decisions_made: Optional[List[str]] = None
    skills_exercised: Optional[List[str]] = None
    source: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class WorkSessionResource(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    title: str
    objective: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 0
    summary: Optional[str] = None
    outcomes: Optional[str] = None
    artifacts_created: List[str] = Field(default_factory=list)
    decisions_made: List[str] = Field(default_factory=list)
    skills_exercised: List[str] = Field(default_factory=list)
    source: str = "manual_log"
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkSessionResponse(BaseModel):
    data: WorkSessionResource
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorkSessionListResponse(BaseModel):
    data: List[WorkSessionResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 2. EVIDENCE ITEM SCHEMAS
# ============================================================================

class EvidenceItemCreate(BaseModel):
    source_type: str = Field(..., description="work_session, decision, document, interaction, kpi_entry, task, memory, achievement")
    source_id: str = Field(..., description="UUID / ID of the source record")
    work_session_id: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    evidence_type: str = Field(..., description="decision_record, code_deliverable, session_log, document_excerpt, kpi_metric, architectural_spec, user_research")
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=5)
    source_reference: Optional[str] = Field(None, description="URL, file path, commit hash, or canonical markdown path")
    timestamp: Optional[datetime] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)


class EvidenceItemUpdate(BaseModel):
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    work_session_id: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    evidence_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    source_reference: Optional[str] = None
    timestamp: Optional[datetime] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata_payload: Optional[Dict[str, Any]] = None


class EvidenceItemResource(BaseModel):
    id: str
    user_id: str
    source_type: str
    source_id: str
    work_session_id: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    evidence_type: str
    title: str
    content: str
    source_reference: Optional[str] = None
    timestamp: datetime
    confidence: float = 1.0
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceItemResponse(BaseModel):
    data: EvidenceItemResource
    meta: Dict[str, Any] = Field(default_factory=dict)


class EvidenceItemListResponse(BaseModel):
    data: List[EvidenceItemResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 3. PORTFOLIO EVIDENCE SCHEMAS
# ============================================================================

class PortfolioEvidenceCreate(BaseModel):
    skill: str = Field(..., description="Skill name from taxonomy or verified domain")
    project: str = Field(..., min_length=2, max_length=255)
    project_id: Optional[str] = None
    venture_id: Optional[str] = None
    claim: str = Field(..., min_length=10, description="Specific professional capability claim")
    supporting_evidence_ids: List[str] = Field(..., min_length=1, description="Must link to at least 1 verified EvidenceItem ID")
    impact: str = Field(..., min_length=5, description="Documented operational or product impact")
    metric: Optional[str] = Field(None, description="Verified metric IF verified; NEVER invented")
    metric_verified: bool = Field(default=False, description="True only if metric is verified against KPI data")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    review_status: Literal["draft", "in_review", "approved", "rejected"] = Field(default="draft")
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)


class PortfolioEvidenceUpdate(BaseModel):
    skill: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[str] = None
    venture_id: Optional[str] = None
    claim: Optional[str] = None
    supporting_evidence_ids: Optional[List[str]] = None
    impact: Optional[str] = None
    metric: Optional[str] = None
    metric_verified: Optional[bool] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    review_status: Optional[Literal["draft", "in_review", "approved", "rejected"]] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class PortfolioEvidenceResource(BaseModel):
    id: str
    user_id: str
    skill: str
    project: str
    project_id: Optional[str] = None
    venture_id: Optional[str] = None
    claim: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    impact: str
    metric: Optional[str] = None
    metric_verified: bool = False
    confidence: float = 1.0
    review_status: str = "draft"
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PortfolioEvidenceResponse(BaseModel):
    data: PortfolioEvidenceResource
    meta: Dict[str, Any] = Field(default_factory=dict)


class PortfolioEvidenceListResponse(BaseModel):
    data: List[PortfolioEvidenceResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 4. ENTITY EDGE GRAPH SCHEMAS (Postgres-Native)
# ============================================================================

class EntityEdgeCreate(BaseModel):
    source_entity_type: str = Field(..., description="skill, portfolio_evidence, evidence_item, work_session, project, venture, decision, task, document")
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    relationship_type: str = Field(..., description="evidenced_by, generated_during, demonstrates_skill, contributed_to, derived_from, validates")
    weight: float = Field(default=1.0)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)


class EntityEdgeResource(BaseModel):
    id: str
    user_id: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    relationship_type: str
    weight: float = 1.0
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityEdgeResponse(BaseModel):
    data: EntityEdgeResource
    meta: Dict[str, Any] = Field(default_factory=dict)


class EntityEdgeListResponse(BaseModel):
    data: List[EntityEdgeResource]
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 5. SKILL EVIDENCE RESOLUTION SCHEMAS
# ============================================================================

class SkillEvidenceClaimTrace(BaseModel):
    portfolio_evidence_id: str
    claim: str
    project: str
    impact: str
    metric: Optional[str] = None
    metric_verified: bool = False
    confidence: float
    review_status: str
    evidence_items: List[EvidenceItemResource] = Field(default_factory=list)
    work_sessions: List[WorkSessionResource] = Field(default_factory=list)


class SkillEvidenceResponse(BaseModel):
    skill: str
    total_claims: int
    total_evidence_items: int
    verified_claims_count: int
    traces: List[SkillEvidenceClaimTrace]
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 6. GENERATOR REQUESTS & RESPONSES (All DRAFT Status)
# ============================================================================

class GenerateCaseStudyDraftRequest(BaseModel):
    target_role: str = Field(..., min_length=3, description="Target role e.g. AI Product Manager or Chief Product Officer")
    target_audience: Optional[str] = Field("Recruiters, Hiring Managers & Investors", description="Audience context")
    portfolio_evidence_ids: Optional[List[str]] = Field(default_factory=list, description="IDs from portfolio_evidence")
    evidence_item_ids: Optional[List[str]] = Field(default_factory=list, description="Direct EvidenceItem IDs")
    project_id: Optional[str] = None
    venture_id: Optional[str] = None
    tone: Optional[str] = "Authoritative, fact-based, operational, retro-editorial"


class GenerateCaseStudyDraftResponse(BaseModel):
    title: str
    target_role: str
    target_audience: str
    status: Literal["draft"] = "draft"
    human_review_required: bool = True
    executive_summary: str
    full_markdown_case: str
    linked_evidence_ids: List[str]
    citations: List[Dict[str, Any]]
    verified_metrics: List[str]
    meta: Dict[str, Any] = Field(default_factory=dict)


class GenerateCVEvidenceRequest(BaseModel):
    target_role: str = Field(..., min_length=3)
    skills_filter: Optional[List[str]] = Field(default_factory=list)
    project_filter: Optional[str] = None
    max_bullets_per_skill: int = Field(default=3, ge=1, le=10)


class CVBulletPoint(BaseModel):
    skill: str
    project: str
    bullet_text: str
    impact_summary: str
    metric: Optional[str] = None
    metric_verified: bool = False
    supporting_evidence_ids: List[str]
    confidence: float
    verification_level: str  # verified | supported | documented


class GenerateCVEvidenceResponse(BaseModel):
    target_role: str
    status: Literal["draft"] = "draft"
    human_review_required: bool = True
    total_bullet_points: int
    bullet_points: List[CVBulletPoint]
    skill_matrix: Dict[str, List[str]]
    meta: Dict[str, Any] = Field(default_factory=dict)


class GenerateLinkedInProgressDraftRequest(BaseModel):
    work_session_id: Optional[str] = None
    evidence_item_ids: Optional[List[str]] = None
    portfolio_evidence_id: Optional[str] = None
    project_id: Optional[str] = None
    tone: str = Field(default="authentic_builder", description="authentic_builder, technical_deep_dive, founder_reflection")
    include_takeaways: bool = True


class GenerateLinkedInProgressDraftResponse(BaseModel):
    status: Literal["draft"] = "draft"
    human_review_required: bool = True
    headline: str
    post_text: str
    referenced_work_session_id: Optional[str] = None
    referenced_evidence_ids: List[str] = Field(default_factory=list)
    anti_hallucination_verified: bool = True
    meta: Dict[str, Any] = Field(default_factory=dict)


class GenerateXProgressDraftRequest(BaseModel):
    work_session_id: Optional[str] = None
    evidence_item_ids: Optional[List[str]] = None
    portfolio_evidence_id: Optional[str] = None
    thread_format: bool = Field(default=True, description="True for thread, False for single post")


class GenerateXProgressDraftResponse(BaseModel):
    status: Literal["draft"] = "draft"
    human_review_required: bool = True
    thread_tweets: List[str]
    referenced_work_session_id: Optional[str] = None
    referenced_evidence_ids: List[str] = Field(default_factory=list)
    anti_hallucination_verified: bool = True
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 7. BACKWARD COMPATIBILITY SCHEMAS
# ============================================================================

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
    status: Optional[str] = None


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
