from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.ai.provider import GeminiLLMProvider
from app.ai.structured import relevant_contacts, structured_answer
from app.models.entities import Interaction, Person, Task
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_overdue_tasks_use_dates_and_owner_without_ai(test_user_id, other_user_id, monkeypatch):
    inference = AsyncMock(side_effect=AssertionError('Structured answers must not call Gemini'))
    monkeypatch.setattr(GeminiLLMProvider, 'generate_content', inference)
    monkeypatch.setattr(GeminiLLMProvider, 'embed_text', inference)
    now = datetime.now(timezone.utc)
    async with TestingSessionLocal() as db:
        due = Task(user_id=test_user_id, title='Send prototype', due_date=now - timedelta(days=1))
        db.add_all([due,
            Task(user_id=test_user_id, title='Completed', status='done', due_date=now - timedelta(days=1)),
            Task(user_id=test_user_id, title='Upcoming', due_date=now + timedelta(days=1)),
            Task(user_id=other_user_id, title='Foreign', due_date=now - timedelta(days=1)),
            Task(user_id=test_user_id, title='Archived', archived_at=now, due_date=now - timedelta(days=1))])
        await db.commit()
        answer = await structured_answer(db, test_user_id, 'Show overdue tasks')
        assert answer['source_citations'] == [str(due.id)]
        assert answer['provider_used'] == 'database'
        assert 'Send prototype' in answer['generated_text'] and 'Foreign' not in answer['generated_text']
        assert await structured_answer(db, test_user_id, 'Show overdue tasks for a specific project') is None
        inference.assert_not_awaited()


@pytest.mark.asyncio
async def test_contact_suggestions_follow_saved_evidence_and_filter_foreign_archived(test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        person = Person(user_id=test_user_id, name='Research partner')
        archived = Person(user_id=test_user_id, name='Archived researcher', archived_at=datetime.now(timezone.utc))
        foreign = Person(user_id=other_user_id, name='Foreign researcher')
        db.add_all([person, archived, foreign])
        await db.flush()
        source = Interaction(user_id=test_user_id, person_id=person.id, title='Met at launch', summary='Discussed robotics navigation')
        db.add_all([source,
            Interaction(user_id=test_user_id, person_id=archived.id, title='Robotics', summary='robotics'),
            Interaction(user_id=other_user_id, person_id=foreign.id, title='Robotics', summary='private robotics')])
        await db.commit()
        result = await relevant_contacts(db, test_user_id, 'robotics')
        assert [item['person_id'] for item in result] == [str(person.id)]
        assert result[0]['evidence'][0]['id'] == str(source.id)
        answer = await structured_answer(db, test_user_id, 'Who might help me with robotics?')
        assert 'Research partner' in answer['generated_text'] and 'Foreign researcher' not in answer['generated_text']
        assert str(source.id) in answer['source_citations']
