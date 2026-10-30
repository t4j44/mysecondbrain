from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.context_events import validate_timezone


class AssistantPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=0)
    timezone: str = Field(min_length=1, max_length=100)
    quiet_start_minute: int = Field(default=1320, ge=0, le=1439)
    quiet_end_minute: int = Field(default=480, ge=0, le=1439)
    quiet_enabled: bool = True
    telegram_enabled: bool = False
    include_details: bool = False
    daily_cap: int = Field(default=3, ge=1, le=5)
    consent: bool = False

    @field_validator('timezone')
    @classmethod
    def known_timezone(cls, value):
        return validate_timezone(value)

    @model_validator(mode='after')
    def valid_consent_and_window(self):
        if self.quiet_enabled and self.quiet_start_minute == self.quiet_end_minute:
            raise ValueError('Choose different quiet-hour start and end times, or disable quiet hours.')
        if self.telegram_enabled and not self.consent:
            raise ValueError('Explicit permission is required for Telegram notifications.')
        return self


class TelegramActor(BaseModel):
    id: int = Field(gt=0, le=2**52 - 1, strict=True)
    is_bot: bool = False


class TelegramChat(BaseModel):
    id: int = Field(ge=-(2**52 - 1), le=2**52 - 1, strict=True)
    type: Literal['private', 'group', 'supergroup', 'channel']


class TelegramMessage(BaseModel):
    date: int = Field(ge=0, strict=True)
    sender: TelegramActor = Field(alias='from')
    chat: TelegramChat
    text: str = Field(default='', max_length=4096)


class TelegramCallbackMessage(BaseModel):
    message_id: int = Field(gt=0, strict=True)
    date: int = Field(ge=0, strict=True)
    sender: TelegramActor | None = Field(default=None, alias='from')
    chat: TelegramChat


class TelegramCallback(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    sender: TelegramActor = Field(alias='from')
    message: TelegramCallbackMessage | None = None
    data: str = Field(default='', max_length=64)


class TelegramUpdate(BaseModel):
    update_id: int = Field(ge=0, le=2**63 - 1, strict=True)
    message: TelegramMessage | None = None
    callback_query: TelegramCallback | None = None
