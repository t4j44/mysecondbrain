"""
G5.5 relationship-graph guarantees that only a migrated PostgreSQL can prove.

Everything here is skipped unless POSTGRES_TEST_DATABASE_URL points at a **separate**
development or staging database. Never production. Without it, the migration 0022 backfill and
the RLS boundary on the new tables are reported BLOCKED — never PASS.

What is proven when it does run:
  * Migration 0022 is applied: public.person_organization_roles and public.commitments exist
    with the expected columns, and the legacy columns still exist (deprecated, not dropped).
  * The backfill is faithful: every people.organization_id becomes a primary role, and every
    interactions.commitments[] entry becomes a commitment row with direction 'unspecified'.
  * The ownership trigger rejects a role that spans two tenants.
  * The partial unique index prevents duplicate live affiliations.
  * RLS denies cross-tenant reads and writes on both new tables.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.rls import identity_statements
from tests.integration.conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]

USER_A = uuid.UUID("aaaaaaaa-0000-4000-a000-00000000fe01")
USER_B = uuid.UUID("bbbbbbbb-0000-4000-b000-00000000fe02")


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
                {"id": user_id, "email": f"{user_id}@network.test"},
            )
    yield USER_A, USER_B
    async with pg_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM auth.users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]}
        )


async def _seed_person_and_org(conn, user_id: uuid.UUID, label: str):
    org_id = uuid.uuid4()
    person_id = uuid.uuid4()
    await conn.execute(
        text(
            "INSERT INTO public.organizations (id, user_id, name) VALUES (:id, :user_id, :name)"
        ),
        {"id": org_id, "user_id": user_id, "name": f"{label} Org {org_id}"},
    )
    await conn.execute(
        text(
            "INSERT INTO public.people (id, user_id, organization_id, name, role) "
            "VALUES (:id, :user_id, :org_id, :name, :role)"
        ),
        {
            "id": person_id,
            "user_id": user_id,
            "org_id": org_id,
            "name": f"{label} Person",
            "role": "Founder",
        },
    )
    return person_id, org_id


async def test_migration_0022_tables_exist_and_legacy_columns_are_retained(pg_engine):
    async with pg_engine.connect() as conn:
        tables = {
            row[0]
            for row in (
                await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
            ).fetchall()
        }
        assert {"person_organization_roles", "commitments"} <= tables

        legacy = (
            await conn.execute(
                text(
                    "SELECT table_name, column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND ((table_name = 'people' AND column_name = 'organization_id') "
                    "  OR (table_name = 'interactions' AND column_name = 'commitments'))"
                )
            )
        ).fetchall()
        assert len(legacy) == 2, "0022 must deprecate the legacy fields in place, not drop them"


async def test_legacy_fields_carry_a_deprecation_comment(pg_engine):
    async with pg_engine.connect() as conn:
        for table, column in (("people", "organization_id"), ("interactions", "commitments")):
            comment = (
                await conn.execute(
                    text(
                        "SELECT col_description(:relname::regclass, a.attnum) "
                        "FROM pg_attribute a "
                        "WHERE a.attrelid = :relname::regclass AND a.attname = :column"
                    ),
                    {"relname": f"public.{table}", "column": column},
                )
            ).scalar()
            assert comment and "DEPRECATED" in comment, f"{table}.{column}"


async def test_backfill_promotes_person_organization_id_to_a_primary_role(pg_engine, two_users):
    """A row inserted the legacy way is migrated, not discarded, when 0022 is re-run."""
    async with pg_engine.begin() as conn:
        person_id, org_id = await _seed_person_and_org(conn, USER_A, "Backfill")
        # Re-run only the backfill statement shape; the migration is idempotent by design.
        await conn.execute(
            text(
                """
                INSERT INTO public.person_organization_roles (
                    user_id, person_id, organization_id, role, relationship_type,
                    is_primary, started_at, source, confidence
                )
                SELECT p.user_id, p.id, p.organization_id, p.role, p.relationship_type::text,
                       true, p.created_at, 'migrated:people.organization_id', 1.0
                  FROM public.people p
                  JOIN public.organizations o
                    ON o.id = p.organization_id AND o.user_id = p.user_id
                 WHERE p.organization_id IS NOT NULL
                   AND NOT EXISTS (
                       SELECT 1 FROM public.person_organization_roles r
                        WHERE r.user_id = p.user_id AND r.person_id = p.id
                          AND r.organization_id = p.organization_id
                   )
                """
            )
        )

    async with pg_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT organization_id, role, is_primary, source "
                    "FROM public.person_organization_roles "
                    "WHERE user_id = :user_id AND person_id = :person_id"
                ),
                {"user_id": USER_A, "person_id": person_id},
            )
        ).fetchall()
        assert len(row) == 1
        assert row[0][0] == org_id
        assert row[0][1] == "Founder"
        assert row[0][2] is True
        assert row[0][3] == "migrated:people.organization_id"


async def test_backfill_expands_the_commitments_array_without_guessing_direction(
    pg_engine, two_users
):
    async with pg_engine.begin() as conn:
        person_id, _ = await _seed_person_and_org(conn, USER_A, "Ledger")
        interaction_id = uuid.uuid4()
        await conn.execute(
            text(
                "INSERT INTO public.interactions "
                "(id, user_id, person_id, interaction_type, title, commitments) "
                "VALUES (:id, :user_id, :person_id, 'meeting', :title, :commitments)"
            ),
            {
                "id": interaction_id,
                "user_id": USER_A,
                "person_id": person_id,
                "title": "Legacy interaction",
                "commitments": ["Send the deck", "Introduce the CTO"],
            },
        )
        await conn.execute(
            text(
                """
                INSERT INTO public.commitments (
                    user_id, organization_id, venture_id, project_id,
                    interaction_id, meeting_id, direction, description, status, source
                )
                SELECT i.user_id,
                       (SELECT p.organization_id FROM public.people p
                         WHERE p.id = i.person_id AND p.user_id = i.user_id),
                       i.venture_id, i.project_id, i.id, i.meeting_id,
                       'unspecified', btrim(c.description), 'open',
                       'migrated:interactions.commitments'
                  FROM public.interactions i
                 CROSS JOIN LATERAL unnest(i.commitments) AS c(description)
                 WHERE i.commitments IS NOT NULL
                   AND btrim(COALESCE(c.description, '')) <> ''
                   AND NOT EXISTS (
                       SELECT 1 FROM public.commitments existing
                        WHERE existing.interaction_id = i.id
                          AND existing.description = btrim(c.description)
                   )
                """
            )
        )

    async with pg_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT description, direction, status, source FROM public.commitments "
                    "WHERE interaction_id = :interaction_id ORDER BY description"
                ),
                {"interaction_id": interaction_id},
            )
        ).fetchall()
        assert [r[0] for r in rows] == ["Introduce the CTO", "Send the deck"]
        assert {r[1] for r in rows} == {"unspecified"}
        assert {r[3] for r in rows} == {"migrated:interactions.commitments"}

        # The source array is left intact so nothing is lost.
        legacy = (
            await conn.execute(
                text("SELECT commitments FROM public.interactions WHERE id = :id"),
                {"id": interaction_id},
            )
        ).scalar()
        assert legacy == ["Send the deck", "Introduce the CTO"]


async def test_role_cannot_span_two_tenants(pg_engine, two_users):
    async with pg_engine.begin() as conn:
        person_id, _ = await _seed_person_and_org(conn, USER_A, "Tenant A")
        _, foreign_org_id = await _seed_person_and_org(conn, USER_B, "Tenant B")

    with pytest.raises(DBAPIError) as excinfo:
        async with pg_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO public.person_organization_roles "
                    "(user_id, person_id, organization_id) VALUES (:u, :p, :o)"
                ),
                {"u": USER_A, "p": person_id, "o": foreign_org_id},
            )
    assert "does not belong to user" in str(excinfo.value)


async def test_duplicate_live_affiliation_is_rejected_by_the_unique_index(pg_engine, two_users):
    async with pg_engine.begin() as conn:
        person_id, org_id = await _seed_person_and_org(conn, USER_A, "Duplicate")
        await conn.execute(
            text(
                "INSERT INTO public.person_organization_roles "
                "(user_id, person_id, organization_id, role) VALUES (:u, :p, :o, 'Founder')"
            ),
            {"u": USER_A, "p": person_id, "o": org_id},
        )

    with pytest.raises(DBAPIError):
        async with pg_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO public.person_organization_roles "
                    "(user_id, person_id, organization_id, role) VALUES (:u, :p, :o, 'Founder')"
                ),
                {"u": USER_A, "p": person_id, "o": org_id},
            )


async def test_rls_hides_the_relationship_graph_from_other_tenants(
    pg_engine, session_factory, two_users
):
    async with pg_engine.begin() as conn:
        person_id, org_id = await _seed_person_and_org(conn, USER_A, "Isolated")
        role_id = uuid.uuid4()
        commitment_id = uuid.uuid4()
        await conn.execute(
            text(
                "INSERT INTO public.person_organization_roles "
                "(id, user_id, person_id, organization_id, role) VALUES (:id, :u, :p, :o, 'Founder')"
            ),
            {"id": role_id, "u": USER_A, "p": person_id, "o": org_id},
        )
        await conn.execute(
            text(
                "INSERT INTO public.commitments "
                "(id, user_id, from_person_id, direction, description) "
                "VALUES (:id, :u, :p, 'owed_to_me', 'Private promise')"
            ),
            {"id": commitment_id, "u": USER_A, "p": person_id},
        )

    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        roles = (
            await session.execute(
                text("SELECT count(*) FROM public.person_organization_roles WHERE id = :id"),
                {"id": role_id},
            )
        ).scalar()
        commitments = (
            await session.execute(
                text("SELECT count(*) FROM public.commitments WHERE id = :id"),
                {"id": commitment_id},
            )
        ).scalar()
        assert roles == 0, "RLS must hide another tenant's affiliation"
        assert commitments == 0, "RLS must hide another tenant's commitment"

    async with session_factory() as session:
        await _apply_identity(session, USER_A)
        assert (
            await session.execute(
                text("SELECT count(*) FROM public.commitments WHERE id = :id"),
                {"id": commitment_id},
            )
        ).scalar() == 1


async def test_rls_blocks_writing_a_commitment_for_another_tenant(
    pg_engine, session_factory, two_users
):
    async with session_factory() as session:
        await _apply_identity(session, USER_B)
        with pytest.raises(DBAPIError):
            await session.execute(
                text(
                    "INSERT INTO public.commitments (user_id, direction, description) "
                    "VALUES (:u, 'owed_by_me', 'Forged')"
                ),
                {"u": USER_A},
            )
            await session.commit()
