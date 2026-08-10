import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import synonym
from sqlalchemy.types import TEXT, TypeDecorator

from app.models.base import Base, FlexibleUUID
from app.utils.identifiers import generate_uuid


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string in DB (works across PostgreSQL & SQLite tests)."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            return {}


class JSONEncodedList(TypeDecorator):
    """Represents a list of items or tags as a json-encoded text column."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return "[]"
        return json.dumps(value)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Any:
        if not value:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"

    id: Any = Column(String(36), primary_key=True)  # Supabase user_id matches id here
    email: Any = Column(String(255), nullable=False)
    full_name: Any = Column(String(255), nullable=True)
    display_name: Any = Column(String(255), nullable=True)
    headline: Any = Column(String(255), nullable=True)
    bio: Any = Column(Text, nullable=True)
    timezone: Any = Column(String(100), default="UTC")
    locale: Any = Column(String(20), default="en-US")
    current_mission: Any = Column(String(500), nullable=True)
    avatar_url: Any = Column(String(1024), nullable=True)
    onboarding_status: Any = Column(String(50), default="in_progress")
    settings: Any = Column(JSONEncodedDict, default=dict)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Venture(Base):
    __tablename__ = "ventures"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_user_venture_slug"),)

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    name: Any = Column(String(255), nullable=False)
    slug: Any = Column(String(255), nullable=False)
    vision: Any = Column(Text, nullable=True)
    mission: Any = Column(Text, nullable=True)
    description: Any = Column(Text, nullable=True)
    status: Any = Column(String(50), default="active", nullable=False)
    priority: Any = Column(String(50), default="medium", nullable=False)
    start_date: Any = Column(DateTime(timezone=True), nullable=True)
    target_date: Any = Column(DateTime(timezone=True), nullable=True)
    metadata_payload: Any = Column(JSONEncodedDict, default=dict)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class Person(Base):
    __tablename__ = "people"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    organization_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    name: Any = Column(String(255), nullable=False)
    role: Any = Column(String(255), nullable=True)
    company: Any = Column(String(255), nullable=True)
    industry: Any = Column(String(255), nullable=True)
    location: Any = Column(String(255), nullable=True)
    email: Any = Column(String(255), nullable=True)
    phone: Any = Column(String(50), nullable=True)
    linkedin_url: Any = Column(String(1024), nullable=True)
    relationship_type: Any = Column(String(100), default="contact", nullable=False)
    last_interaction_at: Any = Column(DateTime(timezone=True), nullable=True)
    notes: Any = Column(Text, nullable=True)
    tags: Any = Column(JSONEncodedList, default=list)
    follow_up_date: Any = Column(DateTime(timezone=True), nullable=True)
    metadata_payload: Any = Column(JSONEncodedDict, default=dict)
    meta = synonym("metadata_payload")
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)

class Organization(Base):
    __tablename__ = "organizations"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    name: Any = Column(String(255), nullable=False)
    domain: Any = Column(String(255), nullable=True)
    industry: Any = Column(String(255), nullable=True)
    location: Any = Column(String(255), nullable=True)
    website_url: Any = Column(String(1024), nullable=True)
    description: Any = Column(Text, nullable=True)
    notes: Any = Column(Text, nullable=True)
    tags: Any = Column(JSONEncodedList, default=list)
    meta: Any = Column(JSONEncodedDict, default=dict)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)

class Interaction(Base):
    __tablename__ = "interactions"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    person_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    venture_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    project_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    meeting_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    interaction_type: Any = Column(String(50), default="meeting", nullable=False)
    title: Any = Column(String(255), nullable=False)
    summary: Any = Column(Text, nullable=True)
    detailed_notes: Any = Column(Text, nullable=True)
    participants: Any = Column(JSONEncodedList, default=list)
    date: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    location: Any = Column(String(255), nullable=True)
    insights: Any = Column(JSONEncodedList, default=list)
    key_takeaways: Any = Column(JSONEncodedList, default=list)
    commitments: Any = Column(JSONEncodedList, default=list)
    next_action: Any = Column(String(500), nullable=True)
    next_actions: Any = Column(JSONEncodedList, default=list)
    follow_up_date: Any = Column(DateTime(timezone=True), nullable=True)
    markdown_path: Any = Column(String(1024), nullable=True)
    meta: Any = Column(JSONEncodedDict, default=dict)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)

class Project(Base):
    __tablename__ = "projects"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    venture_id: Any = Column(String(36), nullable=True, index=True)
    name: Any = Column(String(255), nullable=False)
    description: Any = Column(Text, nullable=True)
    status: Any = Column(String(50), default="in_progress", nullable=False)
    priority: Any = Column(String(50), default="medium", nullable=False)
    progress: Any = Column(Integer, default=0, nullable=False)
    start_date: Any = Column(DateTime(timezone=True), nullable=True)
    target_date: Any = Column(DateTime(timezone=True), nullable=True)
    completion_date: Any = Column(DateTime(timezone=True), nullable=True)
    member_links: Any = Column(JSONEncodedList, default=list)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    venture_id: Any = Column(String(36), nullable=True, index=True)
    project_id: Any = Column(String(36), nullable=True, index=True)
    person_id: Any = Column(String(36), nullable=True, index=True)
    title: Any = Column(String(500), nullable=False)
    description: Any = Column(Text, nullable=True)
    status: Any = Column(String(50), default="todo", nullable=False)
    priority: Any = Column(String(50), default="medium", nullable=False)
    start_date: Any = Column(DateTime(timezone=True), nullable=True)
    due_date: Any = Column(DateTime(timezone=True), nullable=True, index=True)
    completion_date: Any = Column(DateTime(timezone=True), nullable=True)
    estimated_effort: Any = Column(String(100), nullable=True)
    tags: Any = Column(JSONEncodedList, default=list)
    calendar_sync_metadata: Any = Column(JSONEncodedDict, default=dict)
    gcal_event_id: Any = Column(String(255), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    venture_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    title: Any = Column(String(255), nullable=False)
    description: Any = Column(Text, nullable=True)
    start_time: Any = Column(DateTime(timezone=True), nullable=False)
    end_time: Any = Column(DateTime(timezone=True), nullable=False)
    location: Any = Column(String(255), nullable=True)
    status: Any = Column(String(50), default="scheduled")
    participants: Any = Column(JSONEncodedList, default=list)
    notes: Any = Column(Text, nullable=True)
    summary: Any = Column(Text, nullable=True)
    decisions_list: Any = Column(JSONEncodedList, default=list)
    action_items: Any = Column(JSONEncodedList, default=list)
    calendar_source: Any = Column(String(100), default="local")
    external_event_id: Any = Column(String(255), nullable=True)
    recording_url: Any = Column(String(1024), nullable=True)
    meta: Any = Column(JSONEncodedDict, default=dict)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)

    meeting_date = synonym("start_time")
    transcript_text = synonym("notes")
    ai_summary = synonym("summary")

    @property
    def duration_minutes(self) -> int:
        if not self.start_time or not self.end_time:
            return 0
        return max(0, int((self.end_time - self.start_time).total_seconds() // 60))

    @duration_minutes.setter
    def duration_minutes(self, value: Optional[int]) -> None:
        if value is not None:
            start = self.start_time or utc_now()
            self.start_time = start
            self.end_time = start + timedelta(minutes=value)

    @property
    def participant_person_ids(self) -> list[Any]:
        return [getattr(item, "person_id", item) for item in (self.participants or [])]


class Memory(Base):
    __tablename__ = "memories"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    title: Any = Column(String(255), nullable=False)
    type: Any = Column(String(100), default="note", nullable=False)
    body: Any = Column(Text, nullable=False)
    summary: Any = Column(Text, nullable=True)
    is_ai_summary: Any = Column(Boolean, default=False)
    source: Any = Column(String(255), default="user_author")
    memory_date: Any = Column(DateTime(timezone=True), default=utc_now)
    importance: Any = Column(Integer, default=5)
    related_people: Any = Column(JSONEncodedList, default=list)
    related_projects: Any = Column(JSONEncodedList, default=list)
    related_ventures: Any = Column(JSONEncodedList, default=list)
    tags: Any = Column(JSONEncodedList, default=list)
    linked_venture_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    linked_person_id: Any = Column(FlexibleUUID, nullable=True, index=True)
    meta: Any = Column(JSONEncodedDict, default=dict)
    visibility: Any = Column(String(50), default="private")
    embedding_status: Any = Column(String(50), default="pending")
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)

    content = synonym("body")
    category = synonym("type")


class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    entity_type: Any = Column(String(100), nullable=False)
    entity_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    content: Any = Column(Text, nullable=False)
    # Stored as JSON array string in tests / fallback, or mapped to vector in live Postgres
    embedding: Any = Column(Text, nullable=True)
    metadata_payload: Any = Column(JSONEncodedDict, default=dict)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Idea(Base):
    __tablename__ = "ideas"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    venture_id: Any = Column(String(36), nullable=True, index=True)
    title: Any = Column(String(255), nullable=False)
    problem: Any = Column(Text, nullable=True)
    solution: Any = Column(Text, nullable=True)
    target_users: Any = Column(String(500), nullable=True)
    market: Any = Column(String(500), nullable=True)
    potential_score: Any = Column(Integer, default=5)
    status: Any = Column(String(50), default="draft", nullable=False)
    assumptions: Any = Column(JSONEncodedList, default=list)
    risks: Any = Column(JSONEncodedList, default=list)
    resources: Any = Column(JSONEncodedList, default=list)
    evidence: Any = Column(JSONEncodedList, default=list)
    next_step: Any = Column(String(500), nullable=True)
    converted_project_id: Any = Column(String(36), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class Decision(Base):
    __tablename__ = "decisions"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    venture_id: Any = Column(String(36), nullable=True, index=True)
    project_id: Any = Column(String(36), nullable=True, index=True)
    context: Any = Column(Text, nullable=False)
    decision: Any = Column(Text, nullable=False)
    rationale: Any = Column(Text, nullable=True)
    alternatives: Any = Column(JSONEncodedList, default=list)
    expected_impact: Any = Column(Text, nullable=True)
    decision_date: Any = Column(DateTime(timezone=True), default=utc_now)
    review_date: Any = Column(DateTime(timezone=True), nullable=True)
    supporting_people: Any = Column(JSONEncodedList, default=list)
    supporting_documents: Any = Column(JSONEncodedList, default=list)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class Document(Base):
    __tablename__ = "documents"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    filename: Any = Column(String(255), nullable=False)
    sanitized_filename: Any = Column(String(255), nullable=False)
    mime_type: Any = Column(String(100), nullable=False)
    extension: Any = Column(String(20), nullable=False)
    size_bytes: Any = Column(Integer, nullable=False)
    checksum: Any = Column(String(128), nullable=False, index=True)
    storage_bucket: Any = Column(String(100), nullable=False)
    storage_path: Any = Column(String(1024), nullable=False)
    processing_status: Any = Column(String(50), default="pending")
    extracted_text: Any = Column(Text, nullable=True)
    chunking_state: Any = Column(String(50), default="unprocessed")
    error_state: Any = Column(String(500), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class KPI(Base):
    __tablename__ = "kpis"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    venture_id: Any = Column(String(36), nullable=True, index=True)
    project_id: Any = Column(String(36), nullable=True, index=True)
    category: Any = Column(String(100), nullable=False)  # founder, network, learning
    name: Any = Column(String(255), nullable=False)
    description: Any = Column(Text, nullable=True)
    unit: Any = Column(String(50), default="count")
    target: Any = Column(Float, default=0.0, nullable=False)
    current_value: Any = Column(Float, default=0.0, nullable=False)
    period: Any = Column(String(50), default="weekly")
    evidence_docs: Any = Column(JSONEncodedList, default=list)
    is_active: Any = Column(Boolean, default=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class KPIEntry(Base):
    __tablename__ = "kpi_entries"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    kpi_id: Any = Column(String(36), nullable=False, index=True)
    entry_date: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    numeric_value: Any = Column(Float, nullable=True)
    text_value: Any = Column(String(500), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Achievement(Base):
    __tablename__ = "achievements"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    venture_id: Any = Column(String(36), nullable=True, index=True)
    title: Any = Column(String(255), nullable=False)
    role: Any = Column(String(255), nullable=False)
    problem: Any = Column(Text, nullable=True)
    responsibilities: Any = Column(JSONEncodedList, default=list)
    impact: Any = Column(Text, nullable=True)
    skills: Any = Column(JSONEncodedList, default=list)
    date: Any = Column(DateTime(timezone=True), default=utc_now)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class PortfolioCaseStudy(Base):
    __tablename__ = "portfolio_case_studies"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    achievement_id: Any = Column(String(36), nullable=True, index=True)
    title: Any = Column(String(255), nullable=False)
    project_name: Any = Column(String(255), nullable=False)
    role: Any = Column(String(255), nullable=False)
    problem_statement: Any = Column(Text, nullable=True)
    solution_details: Any = Column(Text, nullable=True)
    metrics_impact: Any = Column(Text, nullable=True)
    skills_demonstrated: Any = Column(JSONEncodedList, default=list)
    is_ai_generated: Any = Column(Boolean, default=False)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    content_type: Any = Column(String(100), default="article", nullable=False)
    title: Any = Column(String(500), nullable=False)
    body: Any = Column(Text, nullable=False)
    status: Any = Column(
        String(50), default="draft", nullable=False
    )  # draft, under_review, published
    audience: Any = Column(String(255), nullable=True)
    objective: Any = Column(String(500), nullable=True)
    source_records: Any = Column(JSONEncodedList, default=list)
    provider_metadata: Any = Column(JSONEncodedDict, default=dict)
    publication_metadata: Any = Column(JSONEncodedDict, default=dict)
    current_version_number: Any = Column(Integer, default=1)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    content_id: Any = Column(String(36), nullable=False, index=True)
    version_number: Any = Column(Integer, nullable=False)
    title: Any = Column(String(500), nullable=False)
    body: Any = Column(Text, nullable=False)
    change_summary: Any = Column(String(500), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class WeeklyReview(Base):
    __tablename__ = "weekly_reviews"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    title: Any = Column(String(255), nullable=False)
    review_date: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    period_start: Any = Column(DateTime(timezone=True), nullable=False)
    period_end: Any = Column(DateTime(timezone=True), nullable=False)
    completed_tasks: Any = Column(JSONEncodedList, default=list)
    overdue_tasks: Any = Column(JSONEncodedList, default=list)
    project_progress: Any = Column(JSONEncodedList, default=list)
    meetings_summary: Any = Column(JSONEncodedList, default=list)
    interactions_summary: Any = Column(JSONEncodedList, default=list)
    new_ideas: Any = Column(JSONEncodedList, default=list)
    decisions_made: Any = Column(JSONEncodedList, default=list)
    achievements_recorded: Any = Column(JSONEncodedList, default=list)
    kpi_changes: Any = Column(JSONEncodedList, default=list)
    user_reflections: Any = Column(Text, nullable=True)
    is_ai_generated: Any = Column(Boolean, default=False)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    archived_at: Any = Column(DateTime(timezone=True), nullable=True)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("user_id", "provider_name", name="uq_user_provider"),)

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    provider_name: Any = Column(
        String(100), nullable=False
    )  # google, google_drive, google_calendar
    account_identifier: Any = Column(String(255), nullable=True)
    encrypted_tokens: Any = Column(Text, nullable=True)  # Protected field, AES-256-GCM encrypted
    scopes: Any = Column(JSONEncodedList, default=list)
    is_connected: Any = Column(Boolean, default=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    job_type: Any = Column(
        String(100), nullable=False
    )  # sync_google_drive, export_markdown, document_processing
    status: Any = Column(
        String(50), default="pending", nullable=False
    )  # pending, processing, completed, failed
    retry_count: Any = Column(Integer, default=0)
    error_code: Any = Column(String(100), nullable=True)
    error_message: Any = Column(Text, nullable=True)
    result_payload: Any = Column(JSONEncodedDict, default=dict)
    started_at: Any = Column(DateTime(timezone=True), nullable=True)
    completed_at: Any = Column(DateTime(timezone=True), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class ExportRecord(Base):
    __tablename__ = "exports"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    export_type: Any = Column(String(100), default="full")  # record, module, full
    status: Any = Column(String(50), default="pending", nullable=False)
    file_path: Any = Column(String(1024), nullable=True)
    signed_url: Any = Column(String(2048), nullable=True)
    expires_at: Any = Column(DateTime(timezone=True), nullable=True)
    retry_count: Any = Column(Integer, default=0)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Any = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Any = Column(String(36), nullable=False, index=True)
    event_type: Any = Column(
        String(100), nullable=False
    )  # profile_update, integration_connected, etc.
    target_entity: Any = Column(String(100), nullable=True)
    target_id: Any = Column(String(36), nullable=True)
    details: Any = Column(JSONEncodedDict, default=dict)
    timestamp: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    request_id: Any = Column(String(100), nullable=True)
