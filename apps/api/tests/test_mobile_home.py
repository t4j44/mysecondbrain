from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event, select

from app.models import (
    interactions as _interaction_models,  # noqa: F401 - include production participant mapping
)
from app.models.entities import (
    AuditLog,
    ContextEvent,
    EntityEdge,
    Interaction,
    Meeting,
    Person,
    Project,
)
from app.models.meetings import MeetingParticipant
from app.services.relationships import RelationshipService
from tests.conftest import TestingSessionLocal, test_engine


@pytest.mark.asyncio
async def test_empty_home_commits_a_schema_valid_audit_and_remains_owner_scoped(async_client, auth_headers, other_auth_headers, test_user_id):
    assert AuditLog.__table__.c.resource_type.nullable is False
    for _ in range(2):
        response = await async_client.get('/api/v1/relationships/home', headers=auth_headers)
        assert response.status_code == 200, response.text
        assert response.json()['activation']['counts']['people'] == 0
        assert response.json()['followups'] == []
        assert response.headers['cache-control'] == 'private, no-store'
    async with TestingSessionLocal() as db:
        logs = (await db.execute(select(AuditLog).where(AuditLog.user_id == test_user_id))).scalars().all()
        assert len(logs) == 1
        assert logs[0].target_entity == 'relationship_home'
    response = await async_client.get('/api/v1/relationships/home', headers=other_auth_headers)
    assert response.status_code == 200
    assert response.json()['recent_activity'] == []


async def seed_home(db, owner, other, size=6):
    now = datetime.now(timezone.utc)
    for number in range(size):
        project = Project(user_id=owner, name=f'Synthetic project {number}', status='active')
        person = Person(user_id=owner, name=f'Synthetic person {number}')
        foreign = Person(user_id=other, name=f'PRIVATE foreign {number}')
        meeting = Meeting(user_id=owner, title=f'Synthetic meeting {number}', start_time=now+timedelta(days=1), end_time=now+timedelta(days=1,hours=1), status='scheduled')
        db.add_all([project, person, foreign, meeting])
        await db.flush()
        interaction = Interaction(user_id=owner, person_id=person.id, project_id=project.id, title='Synthetic meeting note', summary='Recorded context', interaction_type='note', date=now)
        deleted = Interaction(user_id=owner, title='Deleted evidence', interaction_type='note', date=now, deleted_at=now)
        deleted_event = ContextEvent(user_id=owner, event_type='manual_capture', title='Deleted context', occurred_at=now, source_type='manual', deleted_at=now)
        db.add_all([interaction, deleted, deleted_event])
        await db.flush()
        extra = Person(user_id=owner, name=f'Deleted source contact {number}')
        db.add(extra)
        await db.flush()
        db.add_all([
            MeetingParticipant(user_id=owner, meeting_id=meeting.id, person_id=person.id),
            MeetingParticipant(user_id=owner, meeting_id=meeting.id, person_id=foreign.id),
            EntityEdge(user_id=owner, source_entity_type='person', source_entity_id=foreign.id, target_entity_type='project', target_entity_id=project.id, relationship_type='user_confirmed'),
            EntityEdge(user_id=owner, source_entity_type='person', source_entity_id=extra.id, target_entity_type='project', target_entity_id=project.id, relationship_type='discussed', metadata_payload={'interaction_id': str(deleted.id)}),
            EntityEdge(user_id=owner, source_entity_type='person', source_entity_id=extra.id, target_entity_type='project', target_entity_id=project.id, relationship_type='mentioned', source_event_id=deleted_event.id),
        ])
    await db.commit()


@pytest.mark.asyncio
async def test_home_batches_projects_meetings_and_preserves_deleted_evidence_checks(test_user_id, other_user_id):
    async with TestingSessionLocal() as db:
        await seed_home(db, test_user_id, other_user_id)
        statements = []
        connection = await db.connection()
        def count(_conn, _cursor, statement, _parameters, _context, _many):
            # The shared ASGI app can have independent worker sessions. Count
            # this request's connection, rather than unrelated background SQL.
            if _conn is connection.sync_connection:
                statements.append(statement)
        event.listen(test_engine.sync_engine, 'before_cursor_execute', count)
        try:
            home = await RelationshipService(db, test_user_id).home()
        finally:
            event.remove(test_engine.sync_engine, 'before_cursor_execute', count)
        assert len(home['projects']) == 6 and len(home['meetings']) == 6
        assert len(statements) <= 16, f'Home query budget exceeded: {len(statements)}'
        for project in home['projects']:
            assert len(project['people']) == 1
            assert project['people'][0]['name'].startswith('Synthetic person')
        for meeting in home['meetings']:
            assert len(meeting['people']) == 1
            assert meeting['people'][0]['title'].startswith('Synthetic person')
