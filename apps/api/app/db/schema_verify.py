"""Runtime schema verification against migrated PostgreSQL (never create_all)."""

from __future__ import annotations

from typing import List, Set

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.core.logging import logger
from app.db.schema_contract import (
    APPLICATION_REQUIRED_COLUMNS,
    APPLICATION_REQUIRED_FOREIGN_KEYS,
    APPLICATION_REQUIRED_TABLES,
    EMBEDDING_VECTOR_DIMENSIONS,
    missing_tables,
    type_matches,
)


class SchemaVerificationError(RuntimeError):
    """Raised when the live database does not match the migration contract."""


async def _list_public_tables(conn: AsyncConnection) -> Set[str]:
    result = await conn.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
        )
    )
    return {row[0] for row in result.fetchall()}


async def _column_types(conn: AsyncConnection, table: str) -> dict[str, str]:
    result = await conn.execute(
        text(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table
            """
        ),
        {"table": table},
    )
    out: dict[str, str] = {}
    for name, data_type, udt_name in result.fetchall():
        # Prefer udt_name for domains/enums/vector (often USER-DEFINED in data_type).
        out[name] = f"{data_type}|{udt_name}"
    return out


async def _foreign_keys(conn: AsyncConnection) -> Set[tuple[str, str, str, str]]:
    result = await conn.execute(
        text(
            """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
            """
        )
    )
    return {(r[0], r[1], r[2], r[3]) for r in result.fetchall()}


async def _vector_dimensions(conn: AsyncConnection, table: str, column: str) -> int | None:
    result = await conn.execute(
        text(
            """
            SELECT a.atttypmod
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relname = :table
              AND a.attname = :column
              AND NOT a.attisdropped
            """
        ),
        {"table": table, "column": column},
    )
    row = result.fetchone()
    if not row or row[0] is None:
        return None
    # pgvector stores dimensions in atttypmod
    return int(row[0])


async def verify_migrated_schema(engine: AsyncEngine) -> None:
    """
    Connect and assert required tables/columns/FKs/vector dims exist.

    Does not create or alter schema. Fail closed on mismatch.
    """
    dialect = engine.dialect.name
    if dialect == "sqlite":
        raise SchemaVerificationError(
            "SQLite cannot satisfy the Supabase migration schema contract. "
            "Point DATABASE_URL at migrated PostgreSQL for non-unit environments."
        )
    if dialect != "postgresql":
        raise SchemaVerificationError(
            f"Unsupported database dialect '{dialect}'. Expected postgresql after migrations."
        )

    errors: List[str] = []
    async with engine.connect() as conn:
        present = await _list_public_tables(conn)
        for missing in missing_tables(present):
            errors.append(f"missing required table: public.{missing}")

        for table, cols in APPLICATION_REQUIRED_COLUMNS.items():
            if table not in present:
                continue
            live = await _column_types(conn, table)
            for col, expected in cols.items():
                if col not in live:
                    errors.append(f"missing column: {table}.{col}")
                    continue
                if not type_matches(live[col], expected):
                    errors.append(
                        f"type mismatch: {table}.{col} has '{live[col]}', expected family '{expected}'"
                    )

        live_fks = await _foreign_keys(conn)
        for fk in APPLICATION_REQUIRED_FOREIGN_KEYS:
            key = (fk["table"], fk["column"], fk["ref_table"], fk["ref_column"])
            if key not in live_fks:
                errors.append(
                    "missing FK: "
                    f"{fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}"
                )

        for table, column in (("embeddings", "embedding"), ("memory_embeddings", "embedding")):
            if table not in present:
                continue
            dims = await _vector_dimensions(conn, table, column)
            if dims is not None and dims != EMBEDDING_VECTOR_DIMENSIONS:
                errors.append(
                    f"vector dimension mismatch: {table}.{column} is {dims}, "
                    f"expected {EMBEDDING_VECTOR_DIMENSIONS}"
                )

        # Extensions presence (best-effort)
        ext = await conn.execute(
            text(
                "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp', 'pgcrypto')"
            )
        )
        found_ext = {r[0] for r in ext.fetchall()}
        for required_ext in ("vector",):
            if required_ext not in found_ext:
                errors.append(f"missing extension: {required_ext}")

    if errors:
        detail = "; ".join(errors[:25])
        more = f" (+{len(errors) - 25} more)" if len(errors) > 25 else ""
        raise SchemaVerificationError(
            f"Database schema is incompatible with supabase/migrations contract: {detail}{more}"
        )

    logger.info(
        "Schema verification passed (%s required tables present).",
        len(APPLICATION_REQUIRED_TABLES),
    )
