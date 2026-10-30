"""
Regenerate the strict ORM -> database column drift inventory.

Compares every SQLAlchemy mapped column against the canonical schema. The database side
is taken from live introspection when POSTGRES_TEST_DATABASE_URL is set, and otherwise
derived statically by parsing supabase/migrations in order.

    python scripts/db/orm_drift_report.py [--json]
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))


def orm_tables() -> Dict[str, Any]:
    import app.models.crm  # noqa: F401
    import app.models.entities  # noqa: F401
    import app.models.interactions  # noqa: F401
    import app.models.meetings  # noqa: F401
    import app.models.memories  # noqa: F401
    import app.models.rag  # noqa: F401
    from app.models.base import Base

    return dict(Base.metadata.tables)


async def live_schema(url: str) -> Dict[str, Dict[str, str]]:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.db.dsn import to_async_dsn

    url = to_async_dsn(url)
    if not url.startswith("postgresql+asyncpg://"):
        raise SystemExit(
            "POSTGRES_TEST_DATABASE_URL must be a PostgreSQL URL using asyncpg; "
            "SQLite and other database dialects are not supported."
        )
    engine = create_async_engine(url, future=True)
    try:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT table_name, column_name, data_type, udt_name, is_nullable "
                        "FROM information_schema.columns WHERE table_schema = 'public'"
                    )
                )
            ).all()
    finally:
        await engine.dispose()
    schema: Dict[str, Dict[str, str]] = {}
    for table, column, data_type, udt, nullable in rows:
        if data_type == "ARRAY":
            resolved = udt.lstrip("_") + "[]"
        elif data_type == "USER-DEFINED":
            resolved = udt
        else:
            resolved = data_type
        schema.setdefault(table, {})[column] = resolved
    return schema


def static_schema() -> Dict[str, Dict[str, str]]:
    from app.db.migration_schema import derive_schema

    return {name: dict(t.columns) for name, t in derive_schema().items()}


def _normalise_type(raw: str) -> str:
    value = (raw or "").lower().strip().replace("extensions.", "")
    user_defined = re.search(r"user-defined\(([^)]+)\)", value)
    if user_defined:
        value = user_defined.group(1)
    if value.startswith("array("):
        value = value[6:-1].lstrip("_") + "[]"
    value = re.sub(r"\(\d+(,\d+)?\)", "", value)
    return {
        "character varying": "varchar",
        "timestamp with time zone": "timestamptz",
        "double precision": "float8",
        "float": "float8",
        "boolean": "bool",
    }.get(value, value)


def _orm_type(column: Any) -> str:
    from sqlalchemy.dialects import postgresql

    return _normalise_type(str(column.type.compile(dialect=postgresql.dialect())))


def _types_equivalent(orm: str, db: str) -> bool:
    if orm == db or {orm, db} <= {"text", "varchar", "citext"}:
        return True
    return orm.startswith("vector") and db.startswith("vector")


def build_report() -> Dict[str, Any]:
    url = (os.getenv("POSTGRES_TEST_DATABASE_URL") or "").strip()
    if url:
        db = asyncio.run(live_schema(url))
        source = "live introspection"
    else:
        db = static_schema()
        source = "static derivation from supabase/migrations"

    tables = orm_tables()
    missing_tables: List[str] = []
    missing_columns: Dict[str, List[Dict[str, str]]] = {}
    type_mismatches: Dict[str, List[Dict[str, str]]] = {}

    for table_name, table in sorted(tables.items()):
        if table_name not in db:
            missing_tables.append(table_name)
            continue
        db_columns = db[table_name]
        for column in table.columns:
            if column.name in db_columns:
                orm_type = _orm_type(column)
                db_type = _normalise_type(db_columns[column.name])
                if not _types_equivalent(orm_type, db_type):
                    type_mismatches.setdefault(table_name, []).append(
                        {
                            "column": column.name,
                            "orm_type": orm_type,
                            "db_type": db_type,
                        }
                    )
                continue
            attribute = next(
                (k for k, v in _attribute_map(table_name).items() if v == column.name),
                column.name,
            )
            missing_columns.setdefault(table_name, []).append(
                {
                    "attribute": attribute,
                    "column": column.name,
                    "orm_type": str(column.type),
                    "orm_nullable": str(column.nullable),
                }
            )

    return {
        "source": source,
        "orm_tables": len(tables),
        "db_tables": len(db),
        "missing_tables": sorted(missing_tables),
        "missing_columns": missing_columns,
        "missing_column_count": sum(len(v) for v in missing_columns.values()),
        "affected_tables": len(missing_columns),
        "type_mismatches": type_mismatches,
        "type_mismatch_count": sum(len(v) for v in type_mismatches.values()),
    }


_ATTR_CACHE: Dict[str, Dict[str, str]] = {}


def _attribute_map(table_name: str) -> Dict[str, str]:
    """attribute name -> physical column name for one mapped table."""
    if table_name in _ATTR_CACHE:
        return _ATTR_CACHE[table_name]
    from sqlalchemy import inspect as sa_inspect

    from app.models.base import Base

    mapping: Dict[str, str] = {}
    for mapper in Base.registry.mappers:
        if mapper.local_table is None or mapper.local_table.name != table_name:
            continue
        for prop in mapper.column_attrs:
            for col in prop.columns:
                mapping[prop.key] = col.name
        sa_inspect(mapper.class_)
    _ATTR_CACHE[table_name] = mapping
    return mapping


def main() -> int:
    report = build_report()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
        return 0
    print(f"schema source   : {report['source']}")
    print(f"ORM tables      : {report['orm_tables']}")
    print(f"DB public tables: {report['db_tables']}")
    print(f"\nORM tables with no database table ({len(report['missing_tables'])}):")
    print("  " + (", ".join(report["missing_tables"]) or "none"))
    print(f"\nORM columns not in the database ({report['missing_column_count']}), "
          f"across {report['affected_tables']} tables:")
    for table, columns in sorted(report["missing_columns"].items()):
        print(f"  {table}:")
        for entry in columns:
            suffix = "" if entry["attribute"] == entry["column"] else f"  (attr {entry['attribute']})"
            print(f"      - {entry['column']}  [{entry['orm_type']}]{suffix}")
    print(f"\nORM column type mismatches ({report['type_mismatch_count']}):")
    for table, columns in sorted(report["type_mismatches"].items()):
        print(f"  {table}:")
        for entry in columns:
            print(f"      - {entry['column']}  ORM {entry['orm_type']} | DB {entry['db_type']}")
    return 1 if (
        report["missing_tables"]
        or report["missing_column_count"]
        or report["type_mismatch_count"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
