from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import Depends
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging import logger
from app.db.rls import (
    IDENTITY_PROBE_SQL,
    RLS_ROLE,
    IdentityStatements,
    identity_statements,
)
from app.db.schema_verify import SchemaVerificationError, verify_migrated_schema
from app.dependencies.auth import AuthenticatedUser, get_current_user

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


def _supports_rls(session: AsyncSession) -> bool:
    """
    Identity can only be injected on PostgreSQL. The SQLite unit-test fallback has no roles,
    no GUCs and no RLS; there the isolated in-memory fixture is the only tenant boundary
    (see docs/production-recovery/G2_RLS_SECURITY_GATE.md).
    """
    bind = getattr(session, "bind", None) or engine
    return bool(bind.dialect.name == "postgresql")


def _install_identity_listener(session: AsyncSession, statements: IdentityStatements) -> None:
    """
    Re-inject the caller identity at the start of every transaction on this session.

    Services commit mid-request; because identity is transaction-local it must be restored
    when SQLAlchemy begins the next transaction, otherwise post-commit queries would run
    without claims and RLS would (correctly) deny them.
    """

    @event.listens_for(session.sync_session, "after_begin")
    def _reapply_identity(_session: Any, _transaction: Any, connection: Any) -> None:
        for statement, params in statements:
            connection.execute(text(statement), params)


@asynccontextmanager
async def rls_db_session(
    user_id: str, *, email: Optional[str] = None, role: str = RLS_ROLE
) -> AsyncGenerator[AsyncSession, None]:
    """
    Open a user-scoped session whose transactions run under the caller's Supabase claims
    and the `authenticated` role, so PostgreSQL RLS is the authorization boundary.

    This is the single place that performs identity injection. Endpoints must never issue
    SET LOCAL / set_config themselves.
    """
    statements = identity_statements(user_id, email=email, role=role)
    async with AsyncSessionLocal() as session:
        if _supports_rls(session):
            _install_identity_listener(session, statements)
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_rls_db_session(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession, None]:
    """
    The only database dependency available to authenticated API endpoints.

    Identity comes from the verified JWT via get_current_user; client-supplied user ids can
    never reach the RLS claims.
    """
    async with rls_db_session(user.id, email=user.email) as session:
        yield session


@asynccontextmanager
async def admin_db_session(*, reason: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Privileged system context: no caller claims and no role switch, so the session runs as
    the owning connection role and RLS does not constrain it.

    Reserved for background jobs, MCP credential verification and health probes. This is
    deliberately an async context manager and NOT a FastAPI dependency so it cannot be
    injected into a user-facing endpoint (enforced by tests/test_g2_rls_security.py).
    """
    logger.debug("Opening privileged admin database session.", extra={"admin_reason": reason})
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def current_identity(session: AsyncSession) -> Dict[str, Any]:
    """Return the transaction's active database user and injected claims (diagnostics/tests)."""
    result = await session.execute(text(IDENTITY_PROBE_SQL))
    row = result.mappings().one()
    return dict(row)


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
