from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    meeting_date: datetime
    venture_id: Optional[UUID] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    recording_url: Optional[str] = None
    transcript_text: Optional[str] = None
    ai_summary: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MeetingCreate(MeetingBase):
    participant_person_ids: List[UUID] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    meeting_date: Optional[datetime] = None
    venture_id: Optional[UUID] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    recording_url: Optional[str] = None
    transcript_text: Optional[str] = None
    ai_summary: Optional[str] = None
    action_items: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    participant_person_ids: Optional[List[UUID]] = None


class MeetingResponse(MeetingBase):
    id: UUID
    user_id: UUID
    participant_person_ids: List[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Wrapped single meeting
class MeetingWrappedResponse(BaseModel):
    data: MeetingResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# Wrapped list of meetings
class MeetingListResponse(BaseModel):
    data: List[MeetingResponse]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
