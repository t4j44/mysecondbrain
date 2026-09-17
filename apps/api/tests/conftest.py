from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.dependencies import database as database_module
from app.dependencies.database import get_rls_db_session
from app.main import app
from app.models.entities import Base

# Configure SQLite in-memory asynchronous engine for self-contained, fast unit testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


# Override the database dependency for unit tests. SQLite has no roles, GUCs or RLS, so the
# isolated in-memory database is the tenant boundary here; real RLS is proven only by the
# postgres integration suite in tests/integration/.
async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_rls_db_session] = override_get_db_session

# Paths that open their own session (MCP tool invocation, job runner, probes) go through the
# canonical factory, so the unit suite redirects the factory itself at the SQLite fixture.
database_module.AsyncSessionLocal = TestingSessionLocal


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Create all declarative tables in the temporary in-memory database before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def test_user_id() -> str:
    return "00000000-0000-4000-a000-000000000001"


@pytest.fixture
def other_user_id() -> str:
    return "99999999-9999-4000-a999-999999999999"


@pytest.fixture
def auth_headers(test_user_id: str) -> dict:
    payload = {
        "aud": "authenticated",
        "iss": settings.SUPABASE_URL.rstrip("/") + "/auth/v1",
        "sub": test_user_id,
        "email": "taj@founder.local",
        "role": "founder",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    # Must match decode_and_verify_token: SUPABASE_JWT_SECRET takes precedence over JWT_SECRET
    secret = settings.SUPABASE_JWT_SECRET or settings.JWT_SECRET
    token = jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(other_user_id: str) -> dict:
    payload = {
        "aud": "authenticated",
        "iss": settings.SUPABASE_URL.rstrip("/") + "/auth/v1",
        "sub": other_user_id,
        "email": "intruder@external.local",
        "role": "viewer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    secret = settings.SUPABASE_JWT_SECRET or settings.JWT_SECRET
    token = jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}
