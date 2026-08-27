"""
Bootstrap an empty PostgreSQL database from the canonical supabase/migrations.

Usage (PowerShell):
    $env:POSTGRES_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    python scripts/db/bootstrap_migrations.py

Steps: safety check -> auth shim (local containers only) -> migrations 1..N in order ->
schema validation against app/db/schema_contract.py.

Refuses any URL that looks like production. Never point this at the production project.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

PRODUCTION_MARKERS = ("prod", "production", "live")

# Supabase provides auth.users natively; plain Postgres containers do not. The migrations
# reference auth.users(id), so local bootstrap creates a minimal stand-in.
AUTH_SHIM_SQL = """
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY,
    email TEXT,
    raw_user_meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def resolve_target_url() -> str:
    url = (os.getenv("POSTGRES_TEST_DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit(
            "POSTGRES_TEST_DATABASE_URL is not set. Configure a separate development/staging "
            "PostgreSQL or Supabase project (see docs/production-recovery/G1_DATABASE_SCHEMA_GATE.md)."
        )
    lowered = url.lower()
    if any(marker in lowered for marker in PRODUCTION_MARKERS):
        raise SystemExit(f"Refusing to bootstrap a production-looking database: {lowered[:40]}...")
    return url


def asyncpg_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


def sqlalchemy_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    return url.replace("postgresql://", "postgresql+asyncpg://")


def migration_paths() -> list[Path]:
    from app.db.schema_contract import MIGRATION_FILES

    on_disk = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    if on_disk != sorted(MIGRATION_FILES):
        raise SystemExit(
            "Migration contract drift: supabase/migrations does not match "
            f"app/db/schema_contract.MIGRATION_FILES.\n  on disk: {on_disk}\n  contract: {sorted(MIGRATION_FILES)}"
        )
    return [MIGRATIONS_DIR / name for name in MIGRATION_FILES]


async def apply_migrations(url: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(asyncpg_url(url))
    try:
        await conn.execute(AUTH_SHIM_SQL)
        print("auth.users shim ensured (no-op on Supabase).")
        for path in migration_paths():
            print(f"applying {path.name} ...")
            await conn.execute(path.read_text(encoding="utf-8"))
    finally:
        await conn.close()


async def validate(url: str) -> None:
    from app.db.schema_verify import verify_migrated_schema
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(sqlalchemy_url(url), future=True)
    try:
        await verify_migrated_schema(engine)
    finally:
        await engine.dispose()


async def main() -> int:
    from app.db.schema_verify import SchemaVerificationError

    url = resolve_target_url()
    await apply_migrations(url)
    try:
        await validate(url)
    except SchemaVerificationError as exc:
        print(f"SCHEMA VALIDATION FAILED: {exc}")
        return 1
    print("Bootstrap complete: migrations applied and schema contract validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
