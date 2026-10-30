"""
Assert that every ORM column resolves to the SAME PostgreSQL type the canonical
migrations created.

The existing schema contract checks that names exist. It passed while 117 columns
had the wrong TYPE, which is why G1 reported PASS twice while the application
could not insert a single row. This script closes that gap.

Usage:
    set POSTGRES_TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/brain_test
    python scripts/db/check_type_drift.py

Exit code 0 when the ORM and the migrated schema agree; 1 otherwise.
Wire this into CI next to the schema contract check.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

for _module in ("entities", "crm", "interactions", "meetings", "memories", "rag"):
    try:
        importlib.import_module(f"app.models.{_module}")
    except ModuleNotFoundError:
        pass

from app.models.base import Base  # noqa: E402
from app.models.enums import ENUM_VALUES  # noqa: E402

PG_DIALECT = postgresql.dialect()

# text / varchar / citext are interchangeable for our purposes; nothing else is.
INTERCHANGEABLE = {"varchar", "text", "citext"}
ALIASES = {
    "character varying": "varchar",
    "timestamp with time zone": "timestamptz",
    "timestamp without time zone": "timestamp",
    "double precision": "float8",
    "boolean": "bool",
    "character": "char",
}


def normalise(raw: str) -> str:
    value = re.sub(r"\(\d+(,\d+)?\)", "", raw.lower().strip())
    return ALIASES.get(value, value)


def orm_type(column) -> str:
    """Resolve the column through load_dialect_impl, so TypeDecorators report honestly."""
    try:
        return normalise(str(column.type.compile(dialect=PG_DIALECT)))
    except Exception as exc:  # pragma: no cover - surfaces as a reported mismatch
        return f"<uncompilable: {exc}>"


def compare_enum_labels(
    live_enums: dict[str, tuple[str, ...]],
    declared: dict[str, tuple[str, ...]],
) -> list[tuple[str, str, str]]:
    """Return mismatches where a shared enum type name has different labels.

    Matching type names with mismatching labels MUST fail. Enums present only
    in one side are also reported so the vocabularies stay in sync.
    """
    mismatches: list[tuple[str, str, str]] = []
    for name in sorted(set(live_enums) | set(declared)):
        db_labels = live_enums.get(name)
        app_labels = declared.get(name)
        if db_labels is None:
            mismatches.append((name, "<absent from database>", ",".join(app_labels or ())))
            continue
        if app_labels is None:
            mismatches.append((name, ",".join(db_labels), "<absent from ENUM_VALUES>"))
            continue
        if db_labels != app_labels:
            mismatches.append((name, ",".join(db_labels), ",".join(app_labels)))
    return mismatches


async def main() -> int:
    url = os.getenv("POSTGRES_TEST_DATABASE_URL", "").strip()
    if not url:
        print("POSTGRES_TEST_DATABASE_URL is not set. Point it at a migrated dev database.")
        return 2
    if "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url, future=True)
    try:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT table_name, column_name, data_type, udt_name "
                        "FROM information_schema.columns WHERE table_schema = 'public'"
                    )
                )
            ).all()
            enum_rows = (
                await conn.execute(
                    text(
                        "SELECT t.typname, e.enumlabel "
                        "FROM pg_type t "
                        "JOIN pg_enum e ON e.enumtypid = t.oid "
                        "JOIN pg_namespace n ON n.oid = t.typnamespace "
                        "WHERE n.nspname = 'public' "
                        "ORDER BY t.typname, e.enumsortorder"
                    )
                )
            ).all()
    finally:
        await engine.dispose()

    live: dict[str, dict[str, str]] = {}
    for table, column, data_type, udt in rows:
        if data_type == "ARRAY":
            resolved = udt.lstrip("_") + "[]"
        elif data_type == "USER-DEFINED":
            resolved = udt
        else:
            resolved = data_type
        live.setdefault(table, {})[column] = resolved

    live_enums: dict[str, list[str]] = {}
    for typname, label in enum_rows:
        live_enums.setdefault(typname, []).append(label)
    live_enum_tuples = {name: tuple(labels) for name, labels in live_enums.items()}

    mismatches: list[tuple[str, str, str, str]] = []
    missing: list[tuple[str, str]] = []
    absent_tables: list[str] = []

    for key in sorted(Base.metadata.tables):
        table = Base.metadata.tables[key]
        if table.name not in live:
            absent_tables.append(table.name)
            continue
        for column in table.columns:
            if column.name not in live[table.name]:
                missing.append((table.name, column.name))
                continue
            declared = orm_type(column)
            actual = normalise(live[table.name][column.name])
            if declared == actual:
                continue
            if {declared, actual} <= INTERCHANGEABLE:
                continue
            mismatches.append((table.name, column.name, declared, actual))

    enum_mismatches = compare_enum_labels(live_enum_tuples, ENUM_VALUES)

    def report(title: str, items, render) -> None:
        print(f"\n{title}: {len(items)}")
        current = None
        for item in items:
            if item[0] != current:
                print(f"  {item[0]}:")
                current = item[0]
            print(f"      {render(item)}")

    if absent_tables:
        print(f"\nORM TABLES ABSENT FROM THE MIGRATED SCHEMA: {len(absent_tables)}")
        for name in absent_tables:
            print(f"  - {name}")
    report("TYPE MISMATCHES", mismatches, lambda i: f"{i[1]:28} ORM {i[2]:18} | DB {i[3]}")
    report("COLUMNS MISSING FROM THE DATABASE", missing, lambda i: f"- {i[1]}")
    report(
        "ENUM VALUE MISMATCHES",
        enum_mismatches,
        lambda i: f"DB [{i[1]}] | ENUM_VALUES [{i[2]}]",
    )

    total = len(mismatches) + len(missing) + len(absent_tables) + len(enum_mismatches)
    print(f"\n{'DRIFT: ' + str(total) if total else 'CLEAN: ORM matches the migrated schema.'}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
