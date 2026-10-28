from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.context_events import validate_timezone


class CommitmentActionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    expected_revision: int = Field(ge=1, strict=True)
    action: Literal['done', 'working', 'snooze', 'help', 'cancel']
    snoozed_until: AwareDatetime | None = None
    timezone: str | None = Field(default=None, max_length=100)

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        return validate_timezone(value) if value else value

    @model_validator(mode='after')
    def snooze_requires_explicit_time(self):
        if self.action == 'snooze' and (self.snoozed_until is None or not self.timezone):
            raise ValueError('Choose a reminder time and timezone.')
        if self.action != 'snooze' and (self.snoozed_until is not None or self.timezone is not None):
            raise ValueError('Only Snooze accepts a reminder time.')
        return self
