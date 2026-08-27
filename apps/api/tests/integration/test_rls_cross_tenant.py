"""
G2 cross-tenant RLS enforcement against a migrated development/staging PostgreSQL.

Everything here is skipped unless POSTGRES_TEST_DATABASE_URL points at a **separate**
development or staging database. Never production. Without that, G2 cross-tenant and pool
isolation are reported BLOCKED — never PASS.

What is proven when it does run:
  * User B cannot SELECT / UPDATE / DELETE User A's row.
  * With the application's user_id filter deliberately removed, RLS still hides the row
    (real defense in depth, not just an ORM WHERE clause).
  * Identity is transaction-local: a recycled pooled connection carries no prior claims.
  * The admin context is a genuinely separate authorization domain.
  * Every public table owning a user_id has RLS enabled with owner-scoped policies.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.rls import IDENTITY_PROBE_SQL, RLS_ROLE, identity_statements
from app.db.schema_contract import RLS_POLICY_EXEMPT_TABLES
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]

USER_A = uuid.UUID("aaaaaaaa-0000-4000-a000-000000000001")
USER_B = uuid.UUID("bbbbbbbb-0000-4000-b000-000000000002")


async def _apply_identity(session, user_id: uuid.UUID) -> None:
    """Inject transaction-local claims exactly the way the API dependency does."""
    for statement, params in identity_statements(str(user_id)):
        await session.execute(text(statement), params)


@pytest_asyncio.fixture
async def session_factory(pg_engine):
    return async_sessionmaker(pg_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def two_users(pg_engine):
    """Create two real users and remove everything they own afterwards."""
    async with pg_engine.begin() as conn:
        for user_id in (USER_A, USER_B):
            await conn.execute(
                text(
                    "INSERT INTO auth.users (id, email) VALUES (:id, :email) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": user_id, "email": f"{user_id}@rls.test"},
            )
    yield USER_A, USER_B
    async with pg_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM auth.users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]}
        )


@pytest_asyncio.fixture
async def venture_of_user_a(session_factory, two_users):
    """User A creates a record through an RLS-scoped transaction."""
    venture_id = uuid.uuid4()
    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        await session.execute(
            text(
                "INSERT INTO public.ventures (id, user_id, name) "
                "VALUES (:id, :user_id, :name)"
            ),
            {"id": venture_id, "user_id": USER_A, "name": "Justor AI"},
        )
        await session.commit()
    yield venture_id
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM public.ventures WHERE id = :id"), {"id": venture_id}
        )
        await session.commit()


async def test_user_b_cannot_read_user_a_record(session_factory, venture_of_user_a):
    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        result = await session.execute(
            text("SELECT id FROM public.ventures WHERE id = :id"), {"id": venture_of_user_a}
        )
        assert result.first() is None


async def test_user_b_cannot_update_user_a_record(session_factory, venture_of_user_a):
    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        result = await session.execute(
            text("UPDATE public.ventures SET name = 'stolen' WHERE id = :id"),
            {"id": venture_of_user_a},
        )
        assert result.rowcount == 0
        await session.commit()

    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        owner_view = await session.execute(
            text("SELECT name FROM public.ventures WHERE id = :id"), {"id": venture_of_user_a}
        )
        assert owner_view.scalar_one() == "Justor AI"


async def test_user_b_cannot_delete_user_a_record(session_factory, venture_of_user_a):
    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        result = await session.execute(
            text("DELETE FROM public.ventures WHERE id = :id"), {"id": venture_of_user_a}
        )
        assert result.rowcount == 0
        await session.commit()

    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        still_there = await session.execute(
            text("SELECT 1 FROM public.ventures WHERE id = :id"), {"id": venture_of_user_a}
        )
        assert still_there.first() is not None


async def test_rls_blocks_user_b_even_without_an_application_user_id_filter(
    session_factory, venture_of_user_a
):
    """
    Defense in depth: the query below is deliberately missing the application's
    `WHERE user_id = :caller` filter. RLS alone must still hide User A's row.
    """
    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        unscoped = await session.execute(text("SELECT id, user_id FROM public.ventures"))
        rows = unscoped.all()
        assert all(row.user_id == USER_B for row in rows), rows
        assert venture_of_user_a not in [row.id for row in rows]


async def test_user_b_cannot_insert_a_row_owned_by_user_a(session_factory, two_users):
    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        with pytest.raises(Exception) as exc_info:
            await session.execute(
                text(
                    "INSERT INTO public.ventures (id, user_id, name) "
                    "VALUES (:id, :user_id, 'impersonated')"
                ),
                {"id": uuid.uuid4(), "user_id": USER_A},
            )
        assert "row-level security" in str(exc_info.value).lower()
        await session.rollback()


async def test_claims_do_not_survive_a_commit_without_reinjection(session_factory, two_users):
    """
    Identity is transaction-local. After a commit the claims are gone until the session
    dependency re-injects them, which is what makes pooled connections safe.
    """
    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        await session.commit()
        identity = (await session.execute(text(IDENTITY_PROBE_SQL))).mappings().one()
        assert not identity["subject"]
        assert not identity["claims"]


async def test_pooled_connection_carries_no_previous_user_claims(session_factory, two_users):
    """Request as A -> release the connection -> request as B -> no trace of A."""
    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        first = (await session.execute(text(IDENTITY_PROBE_SQL))).mappings().one()
        assert str(USER_A) in first["claims"]
        await session.commit()

    async with session_factory() as session:
        fresh = (await session.execute(text(IDENTITY_PROBE_SQL))).mappings().one()
        assert str(USER_A) not in (fresh["claims"] or "")
        assert not fresh["subject"]

        await _apply_identity(session, USER_B)
        scoped = (await session.execute(text(IDENTITY_PROBE_SQL))).mappings().one()
        assert str(USER_B) in scoped["claims"]
        assert str(USER_A) not in scoped["claims"]
        await session.rollback()


async def test_rls_role_is_active_inside_a_scoped_transaction(session_factory, two_users):
    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        current_role = (await session.execute(text("SELECT current_user"))).scalar_one()
        assert current_role == RLS_ROLE
        await session.rollback()


async def test_admin_context_is_a_separate_authorization_domain(
    session_factory, venture_of_user_a
):
    """The admin context sets no claims, keeps the owner role, and is not RLS-limited."""
    async with session_factory() as session:
        current_role = (await session.execute(text("SELECT current_user"))).scalar_one()
        assert current_role != RLS_ROLE
        visible = await session.execute(
            text("SELECT 1 FROM public.ventures WHERE id = :id"), {"id": venture_of_user_a}
        )
        assert visible.first() is not None


async def test_token_vault_is_unreachable_for_the_authenticated_role(session_factory, two_users):
    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        with pytest.raises(Exception) as exc_info:
            await session.execute(text("SELECT 1 FROM public.integration_tokens"))
        assert "permission denied" in str(exc_info.value).lower()
        await session.rollback()


async def test_every_user_owned_table_has_rls_with_owner_policies(pg_engine):
    """Catalog-level audit: no table owning a user_id may be left unprotected."""
    async with pg_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    """
                    SELECT c.relname AS table_name,
                           c.relrowsecurity AS rls_enabled,
                           (SELECT count(*) FROM pg_policies p
                             WHERE p.schemaname = 'public' AND p.tablename = c.relname
                           ) AS policy_count
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_attribute a ON a.attrelid = c.oid
                    WHERE n.nspname = 'public'
                      AND c.relkind = 'r'
                      AND a.attname = 'user_id'
                      AND a.attnum > 0
                      AND NOT a.attisdropped
                    ORDER BY c.relname
                    """
                )
            )
        ).all()

    assert rows, "no user-owned tables found; is the database migrated?"
    unprotected = [r.table_name for r in rows if not r.rls_enabled]
    assert unprotected == [], unprotected
    policyless = [
        r.table_name
        for r in rows
        if r.policy_count == 0 and r.table_name not in RLS_POLICY_EXEMPT_TABLES
    ]
    assert policyless == [], policyless


async def test_all_policies_reference_auth_uid(pg_engine):
    async with pg_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT tablename, policyname, qual, with_check FROM pg_policies "
                    "WHERE schemaname = 'public'"
                )
            )
        ).all()

    assert rows
    for row in rows:
        predicate = f"{row.qual or ''} {row.with_check or ''}"
        assert "auth.uid()" in predicate, (row.tablename, row.policyname, predicate)
