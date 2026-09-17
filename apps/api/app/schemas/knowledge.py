from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- MEMORIES SCHEMAS (Task 18) ---
class MemoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="note", max_length=100)
    body: str = Field(..., min_length=1)
    summary: Optional[str] = None
    is_ai_summary: bool = False
    source: str = "user_author"
    memory_date: Optional[datetime] = None
    importance: int = Field(default=5, ge=1, le=10)
    related_people: List[str] = []
    related_projects: List[str] = []
    related_ventures: List[str] = []
    tags: List[str] = []
    visibility: str = "private"


class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    body: Optional[str] = None
    summary: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=10)
    related_people: Optional[List[str]] = None
    related_projects: Optional[List[str]] = None
    related_ventures: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None


class MemoryResponse(BaseModel):
    id: str
    user_id: str
    title: str
    type: str
    body: str
    summary: Optional[str] = None
    is_ai_summary: bool
    source: str
    memory_date: datetime
    importance: int
    related_people: List[str] = []
    related_projects: List[str] = []
    related_ventures: List[str] = []
    tags: List[str] = []
    visibility: str
    embedding_status: str = "pending"
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- IDEAS SCHEMAS (Task 19) ---
class IdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    venture_id: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    target_users: Optional[str] = None
    market: Optional[str] = None
    potential_score: int = Field(default=5, ge=1, le=10)
    status: str = Field(
        default="draft", pattern="^(draft|evaluating|validated|rejected|converted)$"
    )
    assumptions: List[str] = []
    risks: List[str] = []
    resources: List[str] = []
    evidence: List[str] = []
    next_step: Optional[str] = None


class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    venture_id: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    target_users: Optional[str] = None
    market: Optional[str] = None
    potential_score: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = Field(None, pattern="^(draft|evaluating|validated|rejected|converted)$")
    assumptions: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    evidence: Optional[List[str]] = None
    next_step: Optional[str] = None


class IdeaResponse(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    title: str
    problem: Optional[str] = None
    solution: Optional[str] = None
    target_users: Optional[str] = None
    market: Optional[str] = None
    potential_score: int
    status: str
    assumptions: List[str] = []
    risks: List[str] = []
    resources: List[str] = []
    evidence: List[str] = []
    next_step: Optional[str] = None
    converted_project_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class IdeaConvertResponse(BaseModel):
    idea_id: str
    project_id: str
    status: str = "converted"
    message: str = "Idea successfully transformed into an actionable Project."


# --- DECISIONS SCHEMAS (Task 20) ---
class DecisionCreate(BaseModel):
    context: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    rationale: Optional[str] = None
    alternatives: List[str] = []
    expected_impact: Optional[str] = None
    decision_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    supporting_people: List[str] = []
    supporting_documents: List[str] = []


class DecisionUpdate(BaseModel):
    context: Optional[str] = None
    decision: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    rationale: Optional[str] = None
    alternatives: Optional[List[str]] = None
    expected_impact: Optional[str] = None
    decision_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    supporting_people: Optional[List[str]] = None
    supporting_documents: Optional[List[str]] = None


class DecisionResponse(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    context: str
    decision: str
    rationale: Optional[str] = None
    alternatives: List[str] = []
    expected_impact: Optional[str] = None
    decision_date: datetime
    review_date: Optional[datetime] = None
    supporting_people: List[str] = []
    supporting_documents: List[str] = []
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- DOCUMENTS SCHEMAS (Task 21) ---
class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    sanitized_filename: str
    mime_type: str
    extension: str
    size_bytes: int
    checksum: str
    storage_bucket: str
    storage_path: str
    processing_status: str
    extracted_text: Optional[str] = None
    chunking_state: str = "unprocessed"
    error_state: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentProcessResponse(BaseModel):
    document_id: str
    status: str
    chunks_created: int = 0
    message: str


# --- SEARCH & AI SCHEMAS (Tasks 22 & 23) ---
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    entity_types: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    id: str
    entity_type: str
    title: str
    snippet: str
    # Confidence is unavailable until real vector ranking (G4). Never invent a constant.
    score: Optional[float] = None
    confidence_available: bool = False
    search_mode: str = "keyword"


class SearchResultResponse(BaseModel):
    query: str
    results: List[SearchResultItem] = []
    total_matches: int = 0


class AIContentGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    context_record_ids: List[str] = []
    tone: str = "professional"
    output_format: str = "markdown"


class AIContentGenerateResponse(BaseModel):
    generated_text: str
    provider_used: str
    model_used: str
    source_citations: List[str] = []
    citations: List[Dict[str, str]] = []


class AICoverletterRequest(BaseModel):
    achievement_id: str
    target_role: str
    company_name: str
    job_description: Optional[str] = None


class AILinkedInPostRequest(BaseModel):
    achievement_id: str
    tone: str = "engaging"  # engaging, thought_leader, technical
    include_hashtags: bool = True


# --- ACHIEVEMENTS & PORTFOLIO SCHEMAS (Tasks 25 & 26) ---
class AchievementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    venture_id: Optional[str] = None
    problem: Optional[str] = None
    responsibilities: List[str] = []
    impact: Optional[str] = None
    skills: List[str] = []
    date: Optional[datetime] = None


class AchievementUpdate(BaseModel):
    title: Optional[str] = None
    role: Optional[str] = None
    problem: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    impact: Optional[str] = None
    skills: Optional[List[str]] = None
    date: Optional[datetime] = None


class AchievementResponse(BaseModel):
    id: str
    user_id: str
    venture_id: Optional[str] = None
    title: str
    role: str
    problem: Optional[str] = None
    responsibilities: List[str] = []
    impact: Optional[str] = None
    skills: List[str] = []
    date: datetime
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PortfolioCaseStudyCreate(BaseModel):
    achievement_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    project_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    problem_statement: Optional[str] = None
    solution_details: Optional[str] = None
    metrics_impact: Optional[str] = None
    skills_demonstrated: List[str] = []


class PortfolioCaseStudyUpdate(BaseModel):
    title: Optional[str] = None
    project_name: Optional[str] = None
    role: Optional[str] = None
    problem_statement: Optional[str] = None
    solution_details: Optional[str] = None
    metrics_impact: Optional[str] = None
    skills_demonstrated: Optional[List[str]] = None


class PortfolioCaseStudyResponse(BaseModel):
    id: str
    user_id: str
    achievement_id: Optional[str] = None
    title: str
    project_name: str
    role: str
    problem_statement: Optional[str] = None
    solution_details: Optional[str] = None
    metrics_impact: Optional[str] = None
    skills_demonstrated: List[str] = []
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- CONTENT SCHEMAS (Task 27) ---
class ContentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    content_type: str = Field(default="article", pattern="^(article|post|newsletter|memo|script)$")
    status: str = Field(default="draft", pattern="^(draft|under_review|published|archived)$")
    audience: Optional[str] = None
    objective: Optional[str] = None
    source_records: List[str] = []
    provider_metadata: Dict[str, Any] = {}
    publication_metadata: Dict[str, Any] = {}


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|under_review|published|archived)$")
    audience: Optional[str] = None
    objective: Optional[str] = None
    source_records: Optional[List[str]] = None
    provider_metadata: Optional[Dict[str, Any]] = None
    publication_metadata: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = "Updated content body"


class ContentResponse(BaseModel):
    id: str
    user_id: str
    content_type: str
    title: str
    body: str
    status: str
    audience: Optional[str] = None
    objective: Optional[str] = None
    source_records: List[str] = []
    provider_metadata: Dict[str, Any] = {}
    publication_metadata: Dict[str, Any] = {}
    current_version_number: int
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContentVersionResponse(BaseModel):
    id: str
    user_id: str
    content_id: str
    version_number: int
    title: str
    body: str
    change_summary: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
