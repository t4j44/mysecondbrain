"""
G1 ONE SCHEMA regression tests (unit category).

These assert schema *authority* rules only. They do NOT prove PostgreSQL parity —
that requires the postgres integration suite in tests/integration/.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql, sqlite

from app.config import Settings
from app.db.schema_contract import (
    APPLICATION_REQUIRED_TABLES,
    EMBEDDING_VECTOR_DIMENSIONS,
    MIGRATION_FILES,
    ORM_OBSOLETE_TABLES,
)
from app.models.base import Base, SafeArray, UUIDString

REPO_ROOT = Path(__file__).resolve().parents[3]
API_APP = REPO_ROOT / "apps" / "api" / "app"
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"


def test_uuid_array_normalizes_loaded_record_ids_for_asyncpg():
    from uuid import UUID

    identity = 'b7e50c8c-cd8c-4416-83ad-774780ff976a'
    column = SafeArray(postgresql.UUID(as_uuid=False))
    values = column.process_bind_param([UUIDString(identity), UUID(identity), None], postgresql.dialect())
    assert values == [identity, identity, None]
    assert all(type(item) is str for item in values[:2])
    assert column.process_bind_param(None, postgresql.dialect()) is None


def _python_sources() -> list[Path]:
    return [
        path
        for path in API_APP.rglob("*.py")
        if "__pycache__" not in path.parts and "_quarantine" not in path.parts
    ]


def test_runtime_never_creates_schema():
    """Base.metadata.create_all must not appear anywhere in application runtime code."""
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _python_sources()
        if "create_all(" in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"create_all found in runtime code: {offenders}"


def test_single_canonical_engine():
    """Exactly one module may construct the application engine."""
    engine_modules = sorted(
        str(path.relative_to(API_APP)).replace("\\", "/")
        for path in _python_sources()
        if "create_async_engine(" in path.read_text(encoding="utf-8")
    )
    assert engine_modules == ["dependencies/database.py"], engine_modules


def test_migration_contract_matches_migrations_directory():
    on_disk = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert on_disk == sorted(MIGRATION_FILES)
    assert MIGRATION_FILES == sorted(MIGRATION_FILES), "migrations must be lexicographically ordered"


@pytest.mark.parametrize("environment", ["integration", "e2e", "staging"])
def test_sqlite_forbidden_outside_unit_tests(environment: str):
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT=environment,
            APP_ENV=environment,
            DATABASE_URL="sqlite+aiosqlite:///./brain_dev.db",
            _env_file=None,
        )
    assert "SQLite is forbidden" in str(exc_info.value)


def test_sqlite_forbidden_in_production():
    """Production rejects SQLite even when every other production secret is valid."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            APP_ENV="production",
            SUPABASE_URL="https://prod.supabase.co",
            SUPABASE_SECRET_KEY="sb_secret_real_production_key_123456789",
            TOKEN_ENCRYPTION_KEY="real_fernet_production_master_encryption_key",
            MCP_ISSUER_URL="https://tajs-second-brain.onrender.com",
            MCP_RESOURCE_SERVER_URL="https://tajs-second-brain.onrender.com/mcp",
            DATABASE_URL="sqlite+aiosqlite:///./brain_dev.db",
        )
    message = str(exc_info.value)
    assert "SQLite" in message or "must point to PostgreSQL" in message


def test_postgres_url_accepted_for_integration_environment():
    settings = Settings(
        ENVIRONMENT="integration",
        APP_ENV="integration",
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres",
        _env_file=None,
    )
    assert settings.requires_postgres() is True
    assert settings.uses_sqlite() is False


def _all_mapped_tables() -> set[str]:
    from app.models import crm, entities, interactions, meetings, rag  # noqa: F401

    return set(Base.metadata.tables.keys())


def test_orm_tables_are_classified_against_migrations():
    """Every mapped table is either canonical-required or explicitly recorded as obsolete."""
    mapped = _all_mapped_tables()
    unclassified = mapped - set(APPLICATION_REQUIRED_TABLES) - set(ORM_OBSOLETE_TABLES)
    assert unclassified == set(), f"unclassified ORM tables: {sorted(unclassified)}"


def test_rag_tables_are_mapped():
    mapped = _all_mapped_tables()
    for table in ("documents", "document_chunks", "embeddings", "embedding_jobs"):
        assert table in mapped


def test_embedding_column_uses_pgvector_on_postgres():
    from app.models.rag import Embedding

    column_type = Embedding.__table__.c.embedding.type
    pg_impl = column_type.load_dialect_impl(postgresql.dialect())
    assert type(pg_impl).__module__.startswith("pgvector"), type(pg_impl)
    assert pg_impl.dim == EMBEDDING_VECTOR_DIMENSIONS

    # SQLite unit fallback must remain a plain text column, never a fake vector type.
    sqlite_impl = column_type.load_dialect_impl(sqlite.dialect())
    assert "vector" not in str(sqlite_impl).lower()


def test_document_model_maps_canonical_column_names():
    from app.models.entities import Document

    assert Document.filename.expression.name == "original_filename"
    assert Document.size_bytes.expression.name == "file_size"
    assert "title" in Document.__table__.c
