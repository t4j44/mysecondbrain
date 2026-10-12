"""Strict proposals; evidence is mandatory for every durable candidate."""
import calendar
import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Candidate(StrictModel):
    description: str = Field(min_length=1, max_length=2000)
    evidence_text: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0, le=1)
    interpretation: bool = False
    from_speaker: str | None = None
    to_speaker: str | None = None
    due_at: AwareDatetime | None = None
    due_evidence: str | None = None

    @model_validator(mode='after')
    def explicit_due(self):
        if self.due_at and not self.due_evidence:
            raise ValueError('Deadlines require explicit transcript evidence.')
        if self.due_at:
            evidence = (self.due_evidence or '').casefold().translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))
            evidence = re.sub(r'(?<=\d)(st|nd|rd|th)\b', '', evidence)
            evidence = re.sub(r'[,\s]+', ' ', evidence).strip()
            date = self.due_at.date()
            names = [calendar.month_name[date.month].casefold(), calendar.month_abbr[date.month].casefold(),
                ['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর'][date.month-1]]
            explicit = re.search(rf'(?<!\d){date.isoformat()}(?!\d)', evidence) or any(
                re.search(rf'(?<!\w)(?:{name} 0?{date.day} {date.year}|0?{date.day} {name} {date.year})(?!\w)', evidence)
                for name in names)
            if not explicit:
                raise ValueError('Deadline evidence must name an unambiguous date and year matching the due date.')
        return self


class MeetingIntelligence(StrictModel):
    summary: str = Field(min_length=1, max_length=4000)
    topics: list[str] = Field(default_factory=list, max_length=50)
    decisions: list[Candidate] = Field(default_factory=list, max_length=50)
    action_items: list[Candidate] = Field(default_factory=list, max_length=50)
    commitments: list[Candidate] = Field(default_factory=list, max_length=50)
    follow_ups: list[Candidate] = Field(default_factory=list, max_length=50)
    important_facts: list[Candidate] = Field(default_factory=list, max_length=50)
    customer_feedback: list[Candidate] = Field(default_factory=list, max_length=50)
    questions_open: list[Candidate] = Field(default_factory=list, max_length=50)
    people_mentions: list[Candidate] = Field(default_factory=list, max_length=50)
    venture_candidates: list[Candidate] = Field(default_factory=list, max_length=50)
    project_candidates: list[Candidate] = Field(default_factory=list, max_length=50)
    relationship_updates: list[Candidate] = Field(default_factory=list, max_length=50)
    memory_candidates: list[Candidate] = Field(default_factory=list, max_length=50)
    lesson_candidates: list[Candidate] = Field(default_factory=list, max_length=50)


class CaptureCreate(StrictModel):
    request_id: UUID
    title: str = Field(default='New meeting', min_length=1, max_length=255)
    meeting_date: AwareDatetime
    recording_permission: Literal[True]
    provider_terms_accepted: Literal[True]
    venture_id: UUID | None = None


class UploadAuthorize(StrictModel):
    mime_type: str = Field(max_length=100)


class SpeakerMapping(StrictModel):
    speaker: str = Field(min_length=1, max_length=100)
    kind: Literal['me', 'person', 'unknown']
    person_id: UUID | None = None
    confirmed: Literal[True]

    @model_validator(mode='after')
    def person_required(self):
        if (self.kind == 'person') != (self.person_id is not None):
            raise ValueError('Choose a person only for a person mapping.')
        return self


class ConfirmIntelligence(StrictModel):
    confirmed: Literal[True]
    # None is Save All. An explicit list implements selective review.
    selections: list[str] | None = Field(default=None, max_length=700)


class CaptureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    state: str
    duration_seconds: int
    retained_until: datetime | None
    audio_deleted_at: datetime | None
    intelligence: dict
    transcript_segments: list[dict]
    speaker_mappings: dict
    confirmed_at: datetime | None
    error_code: str | None
    data_mode: str
    receipt: dict
