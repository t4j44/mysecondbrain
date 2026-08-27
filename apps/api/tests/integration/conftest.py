import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

POSTGRES_URL = os.getenv("POSTGRES_TEST_DATABASE_URL", "").strip()

requires_postgres = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="POSTGRES INTEGRATION BLOCKED: set POSTGRES_TEST_DATABASE_URL to a migrated "
    "development/staging PostgreSQL database (never production).",
)


@pytest.fixture(autouse=True)
def prepare_database():
    """Override the SQLite unit-test fixture: integration tests use migrated PostgreSQL."""
    yield


@pytest_asyncio.fixture
async def pg_engine():
    engine = create_async_engine(POSTGRES_URL, future=True, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()
