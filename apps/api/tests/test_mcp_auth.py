import pytest
import pytest_asyncio

from app.mcp.security import (
    SCOPE_CONTENT_DRAFT,
    SCOPE_PEOPLE_READ,
    MCPScopeError,
    SlidingWindowRateLimiter,
    verify_scope,
)
from app.models.entities import Profile
from app.repositories.mcp import MCPCredentialRepository


@pytest_asyncio.fixture
async def sample_profile(prepare_database, test_user_id: str):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        profile = Profile(id=test_user_id, email="taj@founder.local", settings={})
        session.add(profile)
        await session.commit()
    return test_user_id


@pytest.mark.asyncio
async def test_mcp_credential_repository_lifecycle(sample_profile):
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        repo = MCPCredentialRepository()
        # 1. Create Credential
        cred = await repo.create_credential(
            session, sample_profile, "Claude Desktop", "stdio", [SCOPE_PEOPLE_READ]
        )
        plaintext = cred["plaintext_key"]
        assert plaintext.startswith("sb_mcp_")
        assert cred["client_name"] == "Claude Desktop"
        assert cred["scopes"] == [SCOPE_PEOPLE_READ]
        assert cred["revoked_at"] is None

        # 2. Verify Credential Success
        verified = await repo.verify_api_key(session, plaintext)
        assert verified is not None
        assert verified["user_id"] == sample_profile
        assert verified["credential_id"] == cred["credential_id"]

        # 3. Verify Credential Failure (wrong key)
        wrong_res = await repo.verify_api_key(session, "sb_mcp_invalid_token")
        assert wrong_res is None

        # 4. Rotate Credential
        rot_cred = await repo.rotate_credential(session, sample_profile, cred["credential_id"])
        new_plaintext = rot_cred["plaintext_key"]
        assert new_plaintext != plaintext
        old_verify = await repo.verify_api_key(session, plaintext)
        assert old_verify is None
        new_verify = await repo.verify_api_key(session, new_plaintext)
        assert new_verify["user_id"] == sample_profile

        # 5. Revoke Credential
        revoked_cred = await repo.revoke_credential(
            session, sample_profile, rot_cred["credential_id"]
        )
        assert revoked_cred["status"] == "revoked"
        revoked_verify = await repo.verify_api_key(session, new_plaintext)
        assert revoked_verify is None


def test_mcp_scope_enforcement():
    # Direct match
    assert verify_scope([SCOPE_PEOPLE_READ], SCOPE_PEOPLE_READ) is True

    # Group mcp:read covers read scopes
    assert verify_scope(["mcp:read"], SCOPE_PEOPLE_READ) is True

    # Group mcp:draft covers draft scopes
    assert verify_scope(["mcp:draft"], SCOPE_CONTENT_DRAFT) is True

    # Wildcards cover everything
    assert verify_scope(["mcp:all"], SCOPE_CONTENT_DRAFT) is True
    assert verify_scope(["*"], SCOPE_PEOPLE_READ) is True

    # Unauthorized attempt raises MCPScopeError
    with pytest.raises(MCPScopeError):
        verify_scope(["mcp:read"], SCOPE_CONTENT_DRAFT)


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter(limit_per_minute=100)
    client_id = "test-rate-limit-client"
    # Consume 99 tokens
    for _ in range(99):
        assert limiter.check_and_record(client_id) is True
    # 100th allowed
    assert limiter.check_and_record(client_id) is True
    # 101st rejected
    assert limiter.check_and_record(client_id) is False
