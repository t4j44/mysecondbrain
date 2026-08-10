from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- PEOPLE SCHEMAS (Task 15) ---
class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    relationship_type: str = Field(default="contact", max_length=100)
    notes: Optional[str] = None
    tags: List[str] = []
    follow_up_date: Optional[datetime] = None
    metadata_payload: Dict[str, Any] = {}


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    relationship_type: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    follow_up_date: Optional[datetime] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class PersonResponse(BaseModel):
    id: str
    user_id: str
    name: str
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    relationship_type: str
    last_interaction_at: Optional[datetime] = None
    notes: Optional[str] = None
    tags: List[str] = []
    follow_up_date: Optional[datetime] = None
    metadata_payload: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- ORGANIZATIONS SCHEMAS (Task 15) ---
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class OrganizationResponse(BaseModel):
    id: str
    user_id: str
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- INTERACTIONS SCHEMAS (Task 16) ---
class InteractionCreate(BaseModel):
    person_id: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    meeting_id: Optional[str] = None
    interaction_type: str = Field(default="meeting", pattern="^(meeting|call|email|notes|coffee)$")
    title: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = None
    detailed_notes: Optional[str] = None
    participants: List[str] = []
    date: Optional[datetime] = None
    location: Optional[str] = None
    insights: List[str] = []
    commitments: List[str] = []
    next_action: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class InteractionUpdate(BaseModel):
    person_id: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    meeting_id: Optional[str] = None
    interaction_type: Optional[str] = Field(None, pattern="^(meeting|call|email|notes|coffee)$")
    title: Optional[str] = None
    summary: Optional[str] = None
    detailed_notes: Optional[str] = None
    participants: Optional[List[str]] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    insights: Optional[List[str]] = None
    commitments: Optional[List[str]] = None
    next_action: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class InteractionResponse(BaseModel):
    id: str
    user_id: str
    person_id: Optional[str] = None
    venture_id: Optional[str] = None
    project_id: Optional[str] = None
    meeting_id: Optional[str] = None
    interaction_type: str
    title: str
    summary: Optional[str] = None
    detailed_notes: Optional[str] = None
    participants: List[str] = []
    date: datetime
    location: Optional[str] = None
    insights: List[str] = []
    commitments: List[str] = []
    next_action: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    markdown_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- MEETINGS SCHEMAS (Task 17) ---
class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    status: str = Field(
        default="scheduled", pattern="^(scheduled|completed|cancelled|rescheduled)$"
    )
    participants: List[str] = []
    notes: Optional[str] = None
    summary: Optional[str] = None
    decisions_list: List[str] = []
    action_items: List[str] = []
    calendar_source: str = "local"
    external_event_id: Optional[str] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled|rescheduled)$")
    participants: Optional[List[str]] = None
    notes: Optional[str] = None
    summary: Optional[str] = None
    decisions_list: Optional[List[str]] = None
    action_items: Optional[List[str]] = None


class MeetingResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    status: str
    participants: List[str] = []
    notes: Optional[str] = None
    summary: Optional[str] = None
    decisions_list: List[str] = []
    action_items: List[str] = []
    calendar_source: str
    external_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
