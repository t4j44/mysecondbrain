import io
import json
import zipfile
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.ai.temporal import temporal_answer, time_window
from app.mcp.tools import MCPDomainTools
from app.models.entities import ContextEvent, EntityEdge, Interaction, Memory, Person, Project
from app.services.account import portable_export
from app.services.context_events import create_event, delete_event
from tests.conftest import TestingSessionLocal


def test_calendar_windows_follow_user_timezone_and_dst():
    clock = datetime(2026, 3, 9, 18, tzinfo=timezone.utc)
    start, end = time_window('yesterday', 'America/New_York', clock)
    assert (end - start).total_seconds() == 23 * 3600
    start, end = time_window('last week', 'Asia/Dhaka', datetime(2026, 9, 28, 1, tzinfo=timezone.utc))
    assert start.isoformat() == '2026-09-20T18:00:00+00:00'
    assert end.isoformat() == '2026-09-27T18:00:00+00:00'
    with pytest.raises(ValueError):
        time_window('between 2026-09-29 and 2026-09-01', 'UTC')


@pytest.mark.asyncio
async def test_temporal_context_uses_happened_time_and_isolates_owner(test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        for owner, label, stamp, privacy in [
            (test_user_id, 'Inside', '2026-09-01T19:00:00+00:00', 'private'),
            (test_user_id, 'Earlier', '2026-09-01T17:00:00+00:00', 'private'),
            (test_user_id, 'Restricted', '2026-09-01T20:00:00+00:00', 'restricted'),
            (other_user_id, 'Foreign', '2026-09-01T20:00:00+00:00', 'private'),
        ]:
            await create_event(db, owner, key=label, title=label, summary=label, event_type='ai_session',
                source_type='mcp', occurred_at=datetime.fromisoformat(stamp), privacy_class=privacy)
        await db.commit()
        result = await temporal_answer(db, test_user_id, 'What AI sessions did I record between 2026-09-02 and 2026-09-02?', 'Asia/Dhaka')
        assert len(result['citations']) == 1 and result['citations'][0]['title'] == 'Inside'
        assert '2026-09-02T01:00:00+06:00' in result['generated_text']
        assert 'Foreign' not in result['generated_text'] and 'Restricted' not in result['generated_text']
        empty = await temporal_answer(db, test_user_id, 'What happened between 2025-01-01 and 2025-01-02?', 'UTC')
        assert not empty['citations'] and 'No supporting records' in empty['generated_text']


@pytest.mark.asyncio
async def test_mcp_event_original_provenance_retry_and_erasure(test_user_id):
    async with TestingSessionLocal() as db:
        db.add(Project(user_id=test_user_id, name='Second Brain Extended'))
        await db.commit()
        domain = MCPDomainTools(db=db, user_id=test_user_id)
        request = {'summary': 'Original exact AI session summary.', 'provider': 'synthetic_gemini',
            'client_request_id': 'first', 'session_reference': 'stable-session',
            'project_hint': 'Second Brain', 'occurred_at': '2026-08-01T09:30:00+06:00', 'event_timezone': 'Asia/Dhaka',
            'session_payload': {'objective': 'Synthetic objective', 'unknown_secret': 'must not persist'}}
        saved = await domain.finalize_work_session(**request)
        await db.commit()
        retry = await domain.finalize_work_session(**{**request, 'client_request_id': 'retry'})
        assert retry['idempotent_replayed'] and retry['context_event_id'] == saved['context_event_id']
        event = await db.get(ContextEvent, saved['context_event_id'])
        assert event.raw_text == request['summary']
        assert event.raw_payload == {'objective': 'Synthetic objective'}
        assert event.source_provider == 'synthetic_gemini' and event.timezone == 'Asia/Dhaka'
        assert event.project_id is None  # partial-name matching must not guess a project
        assert len(saved['created_records']['memories']) == 1
        assert (await db.execute(select(EntityEdge).where(EntityEdge.source_event_id == event.id))).scalars().all()
        await delete_event(db, test_user_id, event.id)
        await db.commit()
        assert (await db.scalar(select(Interaction))).deleted_at
        assert (await db.scalar(select(Memory))).deleted_at
        with pytest.raises(ValueError, match='deleted'):
            await domain.finalize_work_session(**{**request, 'client_request_id': 'another-retry'})
        exported = await portable_export(db, test_user_id)
        with zipfile.ZipFile(io.BytesIO(exported)) as archive:
            tables = json.loads(archive.read('data.json'))['tables']
            assert not tables['context_events'] and not tables['memories'] and not tables['interactions']


@pytest.mark.asyncio
async def test_mcp_person_match_never_overwrites_identity_and_ambiguity_fails(test_user_id):
    async with TestingSessionLocal() as db:
        first = Person(user_id=test_user_id, name='Ahmed', company=None)
        db.add(first)
        await db.commit()
        domain = MCPDomainTools(db=db, user_id=test_user_id)
        matched = await domain.create_person('Ahmed', company='Unconfirmed company', notes='Unconfirmed fact')
        assert matched['deduplicated'] and first.company is None and first.notes is None
        db.add(Person(user_id=test_user_id, name='Ahmed'))
        await db.commit()
        with pytest.raises(ValueError, match='Ambiguous'):
            await domain.create_person('Ahmed')
