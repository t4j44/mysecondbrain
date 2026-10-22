"""Dashboard endpoint contract against the canonical NOT NULL schema and RLS."""
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.v1.endpoints.relationships import home
from app.dependencies.auth import AuthenticatedUser
from app.models.entities import AuditLog
from tests.integration.conftest import requires_postgres
from tests.integration.test_relationship_privacy import identity

pytestmark = [pytest.mark.postgres, requires_postgres]


@pytest.mark.asyncio
async def test_empty_dashboard_audit_write_satisfies_migrated_schema(pg_engine):
    owner = str(uuid4())
    async with pg_engine.begin() as conn:
        await conn.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:id AS uuid),:email)'), {'id': owner, 'email': owner+'@mobile-fixture.invalid'})
    try:
        factory = async_sessionmaker(pg_engine, expire_on_commit=False)
        async with factory() as db:
            await identity(db, owner)
            result = await home(user=AuthenticatedUser(id=owner, email='synthetic@mobile-fixture.invalid', role='authenticated'), db=db)
            assert result['activation']['counts']['people'] == 0
            assert result['followups'] == []
            await identity(db, owner)
            audit = (await db.execute(select(AuditLog).where(AuditLog.user_id == owner))).scalar_one()
            assert audit.target_entity == 'relationship_home'
    finally:
        async with pg_engine.begin() as conn:
            await conn.execute(text('DELETE FROM auth.users WHERE id=CAST(:id AS uuid)'), {'id': owner})
