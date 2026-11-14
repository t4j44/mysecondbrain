"""Private calendar-file drafts. No reservation, provider call, or persistent write."""
from datetime import timedelta, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, NaiveDatetime, field_validator

from app.core.errors import ValidationError
from app.services.context_events import validate_timezone


class CalendarDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    title: str = Field(min_length=1, max_length=255)
    local_start: NaiveDatetime
    host_timezone: str = Field(max_length=100)
    guest_timezone: str = Field(max_length=100)
    duration_minutes: int = Field(ge=5, le=480)
    location: str = Field(default='', max_length=255)
    occurrence: Literal['earlier', 'later'] | None = None

    @field_validator('host_timezone', 'guest_timezone')
    @classmethod
    def zone(cls, value):
        return validate_timezone(value)

    @field_validator('title', 'location')
    @classmethod
    def safe_text(cls, value):
        if any(ord(char) < 32 and char not in '\r\n\t' for char in value):
            raise ValueError('Remove control characters.')
        return value.strip()

    @field_validator('title')
    @classmethod
    def nonempty_title(cls, value):
        if not value:
            raise ValueError('Enter a meeting title.')
        return value

    @field_validator('local_start')
    @classmethod
    def bounded_date(cls, value):
        if not 2000 <= value.year <= 2100:
            raise ValueError('Choose a year between 2000 and 2100.')
        return value.replace(second=0, microsecond=0)


def resolve_start(payload):
    local, zone = payload.local_start, ZoneInfo(payload.host_timezone)
    candidates = sorted({local.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
        for fold in (0, 1)
        if local.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == local})
    if not candidates:
        raise ValidationError('This local time does not exist because the clocks move forward. Choose another time.')
    if len(candidates) > 1 and payload.occurrence is None:
        raise ValidationError('This local time occurs twice because the clocks move back. Choose the earlier or later occurrence.')
    return candidates[-1] if payload.occurrence == 'later' else candidates[0]


def escape_text(value):
    return value.replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,').replace('\t', ' ')


def fold_line(value):
    """RFC 5545 content lines: at most 75 UTF-8 octets, including continuation space."""
    lines, current = [], ''
    for char in value:
        if len((current + char).encode('utf-8')) > 75:
            lines.append(current)
            current = ' '
        current += char
    return '\r\n'.join([*lines, current])


def calendar_draft(payload, now):
    start = resolve_start(payload)
    end = start + timedelta(minutes=payload.duration_minutes)
    stamp = lambda value: value.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')  # noqa: E731
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Second Brain//Private calendar draft//EN',
        'CALSCALE:GREGORIAN', 'BEGIN:VEVENT', f'UID:{payload.request_id}@second-brain.invalid',
        'DTSTAMP:' + stamp(now), 'DTSTART:' + stamp(start), 'DTEND:' + stamp(end),
        'STATUS:TENTATIVE', 'CLASS:PRIVATE', 'TRANSP:TRANSPARENT',
        'SUMMARY:' + escape_text(payload.title),
        'DESCRIPTION:Draft only. No time reserved or invitation sent. Check availability and agree the time manually.']
    if payload.location:
        lines += ['LOCATION:' + escape_text(payload.location)]
    lines += ['END:VEVENT', 'END:VCALENDAR']
    return {'status': 'draft', 'starts_at': start.isoformat(), 'ends_at': end.isoformat(),
        'host_start': start.astimezone(ZoneInfo(payload.host_timezone)).isoformat(),
        'host_end': end.astimezone(ZoneInfo(payload.host_timezone)).isoformat(),
        'guest_start': start.astimezone(ZoneInfo(payload.guest_timezone)).isoformat(),
        'guest_end': end.astimezone(ZoneInfo(payload.guest_timezone)).isoformat(),
        'calendar': '\r\n'.join(fold_line(line) for line in lines) + '\r\n'}
