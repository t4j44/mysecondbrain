"""Strict proposals; evidence is mandatory for every durable candidate."""
import calendar
import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class EvidenceRef(StrictModel):
    segment_id: str = Field(min_length=1, max_length=100)
    speaker_id: str = Field(min_length=1, max_length=100)
    start_seconds: float = Field(ge=0, allow_inf_nan=False)
    end_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    quote: str = Field(min_length=1, max_length=4000)


class SupportedText(StrictModel):
    text: str = Field(min_length=1, max_length=2000)
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=20)


class AgendaItem(SupportedText):
    source: Literal['provided', 'inferred'] = 'inferred'


class DiscussionSection(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    kind: Literal['primary', 'secondary', 'side', 'operational', 'relationship', 'other'] = 'primary'
    summary: str = Field(min_length=1, max_length=12000)
    key_points: list[SupportedText] = Field(default_factory=list, max_length=100)
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=100)
    importance: Literal['high', 'medium', 'low'] = 'medium'


class Candidate(StrictModel):
    description: str = Field(min_length=1, max_length=2000)
    evidence_text: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0, le=1)
    interpretation: bool = False
    from_speaker: str | None = None
    to_speaker: str | None = None
    due_at: AwareDatetime | None = None
    due_evidence: str | None = None
    evidence: list[EvidenceRef] = Field(default_factory=list, max_length=20)
    condition: str | None = Field(default=None, max_length=2000)

    @model_validator(mode='after')
    def explicit_due(self):
        if self.condition is not None and not self.condition.strip():
            raise ValueError('Condition must contain source text.')
        if re.search(r'\b(?:if|unless|provided that|subject to)\b|যদি|হলে', self.evidence_text, re.I) and not self.condition:
            raise ValueError('Conditional statements must preserve their condition explicitly.')
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


# Explicit allowlist: new output fields must never become selectable CRM writes.
CANDIDATE_FIELDS = (
    'decisions', 'action_items', 'commitments', 'follow_ups', 'important_facts',
    'customer_feedback', 'questions_open', 'people_mentions', 'venture_candidates',
    'project_candidates', 'relationship_updates', 'memory_candidates', 'lesson_candidates',
    'risks', 'ideas', 'important_numbers_or_dates',
)


class MeetingIntelligence(StrictModel):
    @model_validator(mode='before')
    @classmethod
    def preserve_legacy_conditions(cls, value):
        # Old persisted proposals had no condition field. Retain their entire
        # conditional quotation rather than discarding it or accepting an
        # unconditional promise. New v2 provider output stays strict.
        if isinstance(value, dict) and value.get('schema_version', 1) == 1:
            value = dict(value)
            for field in CANDIDATE_FIELDS:
                if field in value:
                    value[field] = [dict(item, condition=item['evidence_text'])
                        if isinstance(item, dict) and not item.get('condition')
                        and re.search(r'\b(?:if|unless|provided that|subject to)\b|যদি|হলে',
                            item.get('evidence_text', ''), re.I)
                        else item for item in value[field]]
        return value

    schema_version: Literal[1, 2] = 1
    summary: str = Field(min_length=1, max_length=4000)
    executive_summary: str = Field(default='', max_length=32000)
    detailed_summary: str = Field(default='', max_length=2000000)
    suggested_title: SupportedText | None = None
    purpose: SupportedText | None = None
    agenda_items: list[AgendaItem] = Field(default_factory=list, max_length=200)
    discussion_sections: list[DiscussionSection] = Field(default_factory=list, max_length=500)
    topics: list[str] = Field(default_factory=list, max_length=500)
    decisions: list[Candidate] = Field(default_factory=list, max_length=500)
    action_items: list[Candidate] = Field(default_factory=list, max_length=500)
    commitments: list[Candidate] = Field(default_factory=list, max_length=500)
    follow_ups: list[Candidate] = Field(default_factory=list, max_length=500)
    important_facts: list[Candidate] = Field(default_factory=list, max_length=500)
    customer_feedback: list[Candidate] = Field(default_factory=list, max_length=500)
    questions_open: list[Candidate] = Field(default_factory=list, max_length=500)
    people_mentions: list[Candidate] = Field(default_factory=list, max_length=500)
    venture_candidates: list[Candidate] = Field(default_factory=list, max_length=500)
    project_candidates: list[Candidate] = Field(default_factory=list, max_length=500)
    relationship_updates: list[Candidate] = Field(default_factory=list, max_length=500)
    memory_candidates: list[Candidate] = Field(default_factory=list, max_length=500)
    lesson_candidates: list[Candidate] = Field(default_factory=list, max_length=500)
    risks: list[Candidate] = Field(default_factory=list, max_length=500)
    ideas: list[Candidate] = Field(default_factory=list, max_length=500)
    important_numbers_or_dates: list[Candidate] = Field(default_factory=list, max_length=500)


class NotesUpdate(StrictModel):
    expected_version: int = Field(ge=0)
    markdown: str = Field(max_length=100000)


class MeetingReview(StrictModel):
    expected_version: int = Field(ge=0)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    purpose: str | None = Field(default=None, max_length=4000)
    agenda: str | None = Field(default=None, max_length=16000)
    timezone: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=255)
    project_id: UUID | None = None
    venture_id: UUID | None = None

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        if value is not None:
            from app.services.context_events import validate_timezone
            return validate_timezone(value)
        return value


class CaptureCreate(StrictModel):
    request_id: UUID
    title: str = Field(default='New meeting', min_length=1, max_length=255)
    meeting_date: AwareDatetime
    recording_permission: Literal[True]
    provider_terms_accepted: Literal[True]
    non_sensitive_recording: bool = False
    venture_id: UUID | None = None
    timezone: str | None = Field(default=None, max_length=100)

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        return MeetingReview.valid_timezone(value)


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
