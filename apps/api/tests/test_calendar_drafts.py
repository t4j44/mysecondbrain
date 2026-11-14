from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError as SchemaError
from sqlalchemy import func, select

from app.core.errors import ValidationError
from app.models.entities import Meeting
from app.services.calendar_drafts import CalendarDraft, calendar_draft
from tests.conftest import TestingSessionLocal

NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)


def payload(**changes):
    return CalendarDraft(request_id=uuid4(), **{'title': 'Synthetic call', 'local_start': '2027-01-15T10:30',
        'host_timezone': 'Asia/Dhaka', 'guest_timezone': 'America/New_York', 'duration_minutes': 30, **changes})


def test_timezone_preview_has_same_instant_and_elapsed_duration():
    result = calendar_draft(payload(), NOW)
    assert result['starts_at'] == '2027-01-15T04:30:00+00:00'
    assert result['host_start'] == '2027-01-15T10:30:00+06:00'
    assert result['guest_start'] == '2027-01-14T23:30:00-05:00'
    assert 'DTSTART:20270115T043000Z\r\nDTEND:20270115T050000Z' in result['calendar']
    assert 'STATUS:TENTATIVE' in result['calendar']
    assert 'ATTENDEE' not in result['calendar'] and 'VALARM' not in result['calendar']
    assert result['status'] == 'draft'


def test_spring_clock_gap_rejected_and_repeated_hour_requires_choice():
    with pytest.raises(ValidationError, match='does not exist'):
        calendar_draft(payload(local_start='2027-03-14T02:30', host_timezone='America/New_York'), NOW)
    with pytest.raises(ValidationError, match='occurs twice'):
        calendar_draft(payload(local_start='2027-11-07T01:30', host_timezone='America/New_York'), NOW)
    early = calendar_draft(payload(local_start='2027-11-07T01:30', host_timezone='America/New_York', occurrence='earlier'), NOW)
    late = calendar_draft(payload(local_start='2027-11-07T01:30', host_timezone='America/New_York', occurrence='later'), NOW)
    assert early['starts_at'] == '2027-11-07T05:30:00+00:00'
    assert late['starts_at'] == '2027-11-07T06:30:00+00:00'


def test_duration_across_dst_is_elapsed_minutes_not_wall_clock_difference():
    result = calendar_draft(payload(local_start='2027-03-14T01:45', host_timezone='America/New_York'), NOW)
    assert result['host_start'].endswith('01:45:00-05:00')
    assert result['host_end'].endswith('03:15:00-04:00')


@pytest.mark.parametrize('change', [
    {'host_timezone': 'Unknown/Place'}, {'guest_timezone': '../../etc/passwd'},
    {'duration_minutes': 0}, {'duration_minutes': 481}, {'title': '  '},
    {'title': 'bad\x00input'}, {'local_start': '2027-01-01T10:00Z'}, {'local_start': '9999-01-01T10:00'},
])
def test_invalid_input_fails_before_calendar_generation(change):
    with pytest.raises(SchemaError):
        payload(**change)


def test_calendar_text_cannot_inject_properties_and_utf8_folds_safely():
    draft = payload(title='বাংলা😀' * 20 + '\r\nATTENDEE:malicious@example.invalid', location='Room; A, B\\C')
    result = calendar_draft(draft, NOW)['calendar']
    assert all(len(line.encode('utf-8')) <= 75 for line in result.split('\r\n'))
    unfolded = result.replace('\r\n ', '')
    assert '\r\nATTENDEE:' not in unfolded
    assert '\\nATTENDEE:' in unfolded
    assert 'LOCATION:Room\\; A\\, B\\\\C' in unfolded
    assert unfolded.count('BEGIN:VEVENT') == 1
    assert 'বাংলা😀' * 20 in unfolded


async def test_authenticated_preview_writes_no_meeting_or_invitation(async_client, auth_headers, other_auth_headers):
    data = payload().model_dump(mode='json')
    path = '/api/v1/meetings/schedule/preview'
    assert (await async_client.post(path, json=data)).status_code == 401
    for headers in (auth_headers, other_auth_headers):
        response = await async_client.post(path, headers=headers, json=data)
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'private, no-store'
        assert response.json()['status'] == 'draft'
    async with TestingSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Meeting)) == 0
