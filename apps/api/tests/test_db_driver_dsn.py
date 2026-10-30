"""Prevent hosted Supabase URI schemes from selecting a missing synchronous driver."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.dsn import to_async_dsn


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://postgres.staging:example@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
        "postgresql+asyncpg://postgres.staging:example@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
        "postgres://postgres.staging:example@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
    ],
)
async def test_supabase_url_selects_asyncpg_without_network_access(url: str) -> None:
    dsn = to_async_dsn(url)
    assert dsn.startswith("postgresql+asyncpg://")
    engine = create_async_engine(dsn, pool_pre_ping=True)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "asyncpg"
    finally:
        await engine.dispose()


def test_sqlite_url_left_unchanged_for_isolated_unit_tests() -> None:
    url = "sqlite+aiosqlite:///:memory:"
    assert to_async_dsn(url) == url
