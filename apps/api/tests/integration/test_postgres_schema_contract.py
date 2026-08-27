"""
Schema-drift check: the migrated PostgreSQL database must satisfy the application contract.

Fails CI whenever migrations and application requirements drift apart. Skipped (reported as
POSTGRES INTEGRATION BLOCKED) when no development/staging database is configured.
"""

import pytest
from sqlalchemy import text

from app.db.schema_contract import (
    APPLICATION_REQUIRED_COLUMNS,
    APPLICATION_REQUIRED_FOREIGN_KEYS,
    APPLICATION_REQUIRED_TABLES,
    EMBEDDING_VECTOR_DIMENSIONS,
)
from app.db.schema_verify import verify_migrated_schema

from .conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]


async def test_migrated_schema_satisfies_contract(pg_engine):
    """Single authoritative drift gate — raises SchemaVerificationError listing every mismatch."""
    await verify_migrated_schema(pg_engine)


async def test_required_tables_present(pg_engine):
    async with pg_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
        )
        present = {row[0] for row in result.fetchall()}
    assert sorted(set(APPLICATION_REQUIRED_TABLES) - present) == []


async def test_required_columns_present(pg_engine):
    missing: list[str] = []
    async with pg_engine.connect() as conn:
        for table, columns in APPLICATION_REQUIRED_COLUMNS.items():
            result = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :table"
                ),
                {"table": table},
            )
            live = {row[0] for row in result.fetchall()}
            missing.extend(f"{table}.{column}" for column in columns if column not in live)
    assert missing == []


async def test_required_foreign_keys_present(pg_engine):
    async with pg_engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT tc.table_name, kcu.column_name,
                       ccu.table_name AS ref_table, ccu.column_name AS ref_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
                """
            )
        )
        live = {(r[0], r[1], r[2], r[3]) for r in result.fetchall()}
    for fk in APPLICATION_REQUIRED_FOREIGN_KEYS:
        assert (fk["table"], fk["column"], fk["ref_table"], fk["ref_column"]) in live


async def test_pgvector_dimensions(pg_engine):
    async with pg_engine.connect() as conn:
        for table in ("embeddings", "memory_embeddings"):
            result = await conn.execute(
                text(
                    """
                    SELECT a.atttypmod
                    FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = 'public' AND c.relname = :table
                      AND a.attname = 'embedding' AND NOT a.attisdropped
                    """
                ),
                {"table": table},
            )
            row = result.fetchone()
            assert row is not None, f"{table}.embedding column missing"
            assert row[0] == EMBEDDING_VECTOR_DIMENSIONS
