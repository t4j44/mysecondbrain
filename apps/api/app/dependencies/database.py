from typing import Any, AsyncGenerator, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging import logger
from app.db.schema_verify import SchemaVerificationError, verify_migrated_schema

# Canonical application engine. supabase/migrations owns the schema; this module never
# creates or alters tables (see docs/production-recovery/G1_DATABASE_SCHEMA_GATE.md).
_IS_SQLITE = settings.uses_sqlite()

_engine_kwargs: Dict[str, Any] = {
    "echo": settings.LOG_LEVEL.upper() == "DEBUG",
    "future": True,
}
if _IS_SQLITE:
    # Isolated unit-test fallback only; forbidden for integration/e2e/staging/production.
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator yielding an asynchronous SQLAlchemy database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def verify_database_ready() -> None:
    """
    Connect and verify the migrated schema at startup. Never creates tables.

    Fails closed when the live database does not satisfy the migration contract.
    """
    if settings.requires_postgres() and _IS_SQLITE:
        raise SchemaVerificationError(
            f"SQLite is forbidden for environment '{settings.ENVIRONMENT}'. "
            "Point DATABASE_URL at a migrated PostgreSQL database."
        )

    if not settings.DATABASE_SCHEMA_VERIFY:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.warning(
            "DATABASE_SCHEMA_VERIFY is disabled; connectivity checked without schema verification."
        )
        return

    if _IS_SQLITE:
        # Unit-test fallback: connectivity only. SQLite can never satisfy the pgvector contract.
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.warning(
            "Running against SQLite (unit-test fallback). Schema verification skipped; "
            "supabase/migrations remains the canonical schema."
        )
        return

    await verify_migrated_schema(engine)
