from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.core.errors import NotFoundError
from app.dependencies.database import rls_db_session
from app.models.entities import Commitment, Person
from app.services.meeting_preparation import prepare
from tests.integration.conftest import requires_postgres
from tests.integration.test_assistant_connections_postgres import (
    assistant_owners as assistant_owners,
)
from tests.test_meeting_preparation import seed_preparation

pytestmark = [pytest.mark.postgres, requires_postgres]


async def test_preparation_reads_under_owner_rls_and_reflects_correction(pg_engine, assistant_owners):
    owner, other = assistant_owners
    async with rls_db_session(owner) as db:
        meeting, person, _, promise = await seed_preparation(db, owner)
        assert await db.scalar(text('SELECT current_user')) == 'authenticated'
        assert (await prepare(db, owner, meeting.id))['people'][0]['commitments'][0]['source']['id'] == str(promise.id)
    async with rls_db_session(other) as db:
        with pytest.raises(NotFoundError):
            await prepare(db, other, meeting.id)
    async with rls_db_session(owner) as db:
        (await db.get(Person, person.id)).notes = 'Corrected saved note'
        (await db.get(Commitment, promise.id)).deleted_at = datetime.now(timezone.utc)
        await db.commit()
        card = (await prepare(db, owner, meeting.id))['people'][0]
        assert card['notes'] == 'Corrected saved note' and card['commitments'] == []
