"""
Pydantic Schemas for AI Content Engine & Version History
Module Owner: Agent 9
Enforces explicit user approval (zero auto-publishing) & claim validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContentType(str, Enum):
    LINKEDIN_POST = "linkedin_post"
    FOUNDER_STORY = "founder_story"
    PROJECT_UPDATE = "project_update"
    CASE_STUDY = "case_study"
    ARTICLE = "article"
    WEEKLY_REFLECTION = "weekly_reflection"
    INVESTOR_UPDATE = "investor_update"
    PROFESSIONAL_SUMMARY = "professional_summary"
    UPDATE = "update"  # DB compatibility


class ContentStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentCitation(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    claim_supported: str


class ClaimValidationResult(BaseModel):
    claim_text: str
    status: str = Field(..., description="supported, unsupported_metric, potential_conflict")
    reason: Optional[str] = None
    source_reference: Optional[str] = None


class ContentVersionResource(BaseModel):
    id: str
    user_id: str
    content_id: str
    version_number: int
    body_snapshot: str
    title_snapshot: str
    change_summary: Optional[str] = None
    created_by: str = "user"  # user | ai_assistant
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- GENERATION REQUEST ---
class ContentGenerateRequest(BaseModel):
    content_type: ContentType
    topic: Optional[str] = None
    objective: Optional[str] = None
    target_audience: Optional[str] = "Founders, AI Product Managers, & Investors"
    source_record_ids: List[str] = Field(
        ..., min_length=1, description="Selected UUIDs of underlying memories/meetings/achievements"
    )
    tone: Optional[str] = "Direct, authentic, reflective, analytical"
    length: Optional[str] = "medium"
    anonymize_third_parties: bool = True


# --- MANUAL CREATE / UPDATE REQUESTS ---
class ContentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    content_type: ContentType = ContentType.LINKEDIN_POST
    current_body: str = Field(..., min_length=10)
    venture_id: Optional[str] = None
    objective: Optional[str] = None
    target_audience: Optional[str] = None
    status: ContentStatus = ContentStatus.DRAFT
    cited_record_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    current_body: Optional[str] = None
    status: Optional[ContentStatus] = None
    published_url: Optional[str] = None
    change_note: Optional[str] = Field(
        None, description="Note for automated version history tracking"
    )
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("status", mode="before")
    @classmethod
    def check_status(cls, v):
        if isinstance(v, str):
            v = v.lower()
        return v


class SectionRegenerateRequest(BaseModel):
    section_id_or_title: str
    current_section_text: str = Field(..., min_length=5)
    instruction: str = Field(
        ..., min_length=3, description="e.g. make this more operational, remove buzzwords"
    )
    source_record_ids: List[str] = Field(default_factory=list)
    tone: Optional[str] = None
    length: str = "maintain"


# --- RESOURCE RESPONSE ---
class ContentItemResource(ContentCreateRequest):
    id: str
    user_id: str
    published_url: Optional[str] = None
    published_date: Optional[str] = None
    cited_sources: List[ContentCitation] = Field(default_factory=list)
    claim_validation_results: List[ClaimValidationResult] = Field(default_factory=list)
    latest_version_number: int = 1
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContentResponse(BaseModel):
    data: ContentItemResource
    meta: Dict[str, Any]


class ContentListResponse(BaseModel):
    data: List[ContentItemResource]
    pagination: Dict[str, Any]
    meta: Dict[str, Any]


class ContentVersionListResponse(BaseModel):
    data: List[ContentVersionResource]
    meta: Dict[str, Any]
