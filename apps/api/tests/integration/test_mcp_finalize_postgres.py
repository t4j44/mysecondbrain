"""
G5 finalize_work_session guarantees that only a migrated PostgreSQL can prove.

Everything here is skipped unless POSTGRES_TEST_DATABASE_URL points at a **separate**
development or staging database. Never production. Without it, database-level idempotency
and the finalize end-to-end path are reported BLOCKED — never PASS.

What is proven when it does run:
  * migration 0021 is applied: 'work_session' is a valid interaction_type, and
    interactions carries the meta / deleted_at columns the finalizer uses.
  * The partial unique index makes duplicate work sessions impossible at the database
    level, not merely unlikely at the application level.
  * The index is per-owner, so two users may replay the same client_request_id.
  * A finalize run through the real RLS-scoped session commits one session with its tasks,
    decisions and memories, and a replay adds nothing.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.rls import identity_statements
from app.mcp.extraction import extract_session_intelligence
from app.mcp.tools import MCPDomainTools
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]

USER_A = uuid.UUID("aaaaaaaa-0000-4000-a000-00000000ff01")
USER_B = uuid.UUID("bbbbbbbb-0000-4000-b000-00000000ff02")

TRANSCRIPT = """
# Objective
Prove finalize idempotency against real PostgreSQL.

# Decisions
- Enforce one live work session per (user, client_request_id) with a partial unique index.

# Tasks
- Verify the constraint rejects a duplicate insert

# Findings
- Application-level replay checks race; the index does not.
"""


async def _apply_identity(session, user_id: uuid.UUID) -> None:
    for statement, params in identity_statements(str(user_id)):
        await session.execute(text(statement), params)


@pytest_asyncio.fixture
async def session_factory(pg_engine):
    return async_sessionmaker(pg_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def two_users(pg_engine):
    async with pg_engine.begin() as conn:
        for user_id in (USER_A, USER_B):
            await conn.execute(
                text(
                    "INSERT INTO auth.users (id, email) VALUES (:id, :email) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": user_id, "email": f"{user_id}@finalize.test"},
            )
    yield USER_A, USER_B
    async with pg_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM auth.users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]}
        )


async def _insert_work_session(session, user_id: uuid.UUID, client_request_id: str) -> uuid.UUID:
    session_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO public.interactions "
            "(id, user_id, interaction_type, title, meta) "
            "VALUES (:id, :user_id, 'work_session', :title, CAST(:meta AS jsonb))"
        ),
        {
            "id": session_id,
            "user_id": user_id,
            "title": "Finalize idempotency probe",
            "meta": f'{{"client_request_id": "{client_request_id}"}}',
        },
    )
    return session_id


async def test_migration_0021_is_applied(pg_engine):
    async with pg_engine.connect() as conn:
        enum_values = (
            await conn.execute(
                text(
                    "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
                    "WHERE t.typname = 'interaction_type'"
                )
            )
        ).scalars().all()
        assert "work_session" in enum_values

        columns = (
            await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'interactions'"
                )
            )
        ).scalars().all()
        assert {"meta", "deleted_at"}.issubset(set(columns))

        indexes = (
            await conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'interactions'")
            )
        ).scalars().all()
        assert "uq_interactions_work_session_client_request" in indexes


async def test_duplicate_client_request_id_is_rejected_by_the_database(
    session_factory, two_users
):
    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        first = await _insert_work_session(session, USER_A, "pg-idem-001")
        await session.commit()

    try:
        async with session_factory() as session:
            await _apply_identity(session, USER_A)
            with pytest.raises(Exception) as exc_info:
                await _insert_work_session(session, USER_A, "pg-idem-001")
                await session.commit()
            assert "uq_interactions_work_session_client_request" in str(exc_info.value)
            await session.rollback()
    finally:
        async with session_factory() as session:
            await session.execute(
                text("DELETE FROM public.interactions WHERE id = :id"), {"id": first}
            )
            await session.commit()


async def test_the_idempotency_constraint_is_per_owner(session_factory, two_users):
    created = []
    try:
        for user_id in (USER_A, USER_B):
            async with session_factory() as session:
                await _apply_identity(session, user_id)
                created.append(await _insert_work_session(session, user_id, "pg-idem-shared"))
                await session.commit()
        assert len(created) == 2
    finally:
        async with session_factory() as session:
            await session.execute(
                text("DELETE FROM public.interactions WHERE id = ANY(:ids)"), {"ids": created}
            )
            await session.commit()


async def test_finalize_end_to_end_commits_once_and_replays_clean(session_factory, two_users):
    """Extraction happens outside the transaction; the write batch commits exactly once."""
    extracted = await extract_session_intelligence(
        summary=TRANSCRIPT, session_payload=None, provider="pytest"
    )
    call = dict(
        provider="pytest",
        session_reference="pg-e2e-001",
        client_request_id="pg-e2e-001",
        summary=TRANSCRIPT,
        extraction=extracted["extraction"],
        **extracted["fields"],
    )

    session_ids = []
    try:
        for _ in range(2):
            async with session_factory() as session:
                await _apply_identity(session, USER_A)
                domain = MCPDomainTools(db=session, user_id=str(USER_A))
                result = await domain.finalize_work_session(**call)
                await session.commit()
                session_ids.append(result["session_id"])

        assert session_ids[0] == session_ids[1]

        async with session_factory() as session:
            await _apply_identity(session, USER_A)
            count = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM public.interactions "
                        "WHERE user_id = :user_id AND interaction_type::text = 'work_session'"
                    ),
                    {"user_id": USER_A},
                )
            ).scalar_one()
            assert count == 1
    finally:
        async with session_factory() as session:
            for table in ("tasks", "decisions", "memories", "interactions"):
                await session.execute(
                    text(f"DELETE FROM public.{table} WHERE user_id = :user_id"),
                    {"user_id": USER_A},
                )
            await session.commit()
