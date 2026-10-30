import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.meeting_intelligence import CaptureResponse


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
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias='meta')
    capture: CaptureResponse | None = None
    id: UUID
    user_id: UUID
    participant_person_ids: List[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @computed_field  # type: ignore[prop-decorator]  # Pydantic supports computed properties; mypy does not.
    @property
    def review_token(self) -> str | None:
        """Snapshot identity, not an authorization credential or an AI approval."""
        if not self.capture:
            return None
        snapshot = {
            'id': str(self.id), 'title': self.title, 'date': self.meeting_date.isoformat(),
            'venture_id': str(self.venture_id) if self.venture_id else None,
            'location': self.location,
            'context': {key: self.metadata.get(key) for key in
                ('purpose', 'agenda', 'timezone', 'project_id', 'review_version')},
            'capture': self.capture.model_dump(mode='json', include={
                'intelligence', 'transcript_segments', 'speaker_mappings'}),
        }
        return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'),
            ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


# Wrapped single meeting
class MeetingWrappedResponse(BaseModel):
    data: MeetingResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# Wrapped list of meetings
class MeetingListResponse(BaseModel):
    data: List[MeetingResponse]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
