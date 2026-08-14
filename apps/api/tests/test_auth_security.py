from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.constants import ErrorCode
from app.core.security import decrypt_token, encrypt_token


@pytest.mark.asyncio
async def test_missing_auth_header(async_client):
    response = await async_client.get("/api/v1/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == ErrorCode.AUTHENTICATION_REQUIRED.value


@pytest.mark.asyncio
async def test_invalid_jwt_token(async_client):
    response = await async_client.get(
        "/api/v1/me", headers={"Authorization": "Bearer invalid_malformed_token_string"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "Invalid access token provided" in data["error"]["message"]
    assert data["error"]["code"] == ErrorCode.INVALID_ACCESS_TOKEN.value


@pytest.mark.asyncio
async def test_opaque_secret_key_rejected_as_user_jwt(async_client):
    """Verify that modern server secret keys (sb_secret_...) are never treated as user JWTs."""
    response = await async_client.get(
        "/api/v1/me", headers={"Authorization": "Bearer sb_secret_production_admin_master_key_12345"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == ErrorCode.INVALID_ACCESS_TOKEN.value


@pytest.mark.asyncio
async def test_expired_jwt_token(async_client, test_user_id):
    payload = {
        "sub": test_user_id,
        "email": "taj@founder.local",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired!
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
    }
    secret = settings.SUPABASE_JWT_SECRET or settings.JWT_SECRET
    expired_token = jwt.encode(payload, secret, algorithm="HS256")
    response = await async_client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "Access token has expired" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_valid_supabase_jwks_asymmetric_jwt(async_client, test_user_id, monkeypatch):
    """Verify modern Supabase RS256 JWT verification using cached JWKS signing key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    # 1. Generate RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # 2. Mock PyJWK signing key
    class MockSigningKey:
        key = pub_pem

    class MockJWKClient:
        def get_signing_key_from_jwt(self, token: str):
            return MockSigningKey()

    monkeypatch.setattr("app.dependencies.auth.get_jwks_client", lambda url: MockJWKClient())
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://mock-project.supabase.co")

    # 3. Create RS256 token signed by Supabase Auth with key ID
    payload = {
        "sub": test_user_id,
        "email": "taj@founder.local",
        "role": "founder",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    rs256_token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "supabase-key-1"})

    # 4. Request /api/v1/me and verify identity
    response = await async_client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {rs256_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == test_user_id
    assert response.json()["email"] == "taj@founder.local"


@pytest.mark.asyncio
async def test_production_fails_closed_on_invalid_jwks_signature(async_client, test_user_id, monkeypatch):
    """In production mode, invalid asymmetric tokens strictly fail closed without falling back."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://mock-project.supabase.co")

    # Key pair A for server JWKS, Key pair B for rogue attacker
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_pub_pem = server_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    rogue_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    class MockSigningKey:
        key = server_pub_pem

    class MockJWKClient:
        def get_signing_key_from_jwt(self, token: str):
            return MockSigningKey()

    monkeypatch.setattr("app.dependencies.auth.get_jwks_client", lambda url: MockJWKClient())

    # Token signed with rogue key
    payload = {
        "sub": test_user_id,
        "email": "rogue@attacker.local",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    forged_token = jwt.encode(payload, rogue_key, algorithm="RS256", headers={"kid": "supabase-key-1"})

    response = await async_client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {forged_token}"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == ErrorCode.INVALID_ACCESS_TOKEN.value


@pytest.mark.asyncio
async def test_rls_tenant_isolation(async_client, auth_headers, other_auth_headers):
    """
    Verify strict Row Level Security / Tenant Isolation (ADR-004 & Task 3).
    User B must never read or modify User A's private records!
    """
    # 1. Founder Taj (User A) creates a confidential venture
    venture_data = {
        "name": "Confidential AI Project",
        "slug": "confidential-ai",
        "vision": "Super-secret model architecture",
    }
    create_res = await async_client.post(
        "/api/v1/ventures", json=venture_data, headers=auth_headers
    )
    assert create_res.status_code == 201
    venture_id = create_res.json()["id"]

    # 2. Intruder (User B) attempts to read User A's venture directly by ID
    intruder_read = await async_client.get(
        f"/api/v1/ventures/{venture_id}", headers=other_auth_headers
    )
    assert (
        intruder_read.status_code == 404
    )  # RLS returns Resource Not Found rather than leaking existence!

    # 3. Intruder (User B) lists ventures and should see an empty list
    intruder_list = await async_client.get("/api/v1/ventures", headers=other_auth_headers)
    assert intruder_list.status_code == 200
    assert len(intruder_list.json()["items"]) == 0

    # 4. Founder Taj (User A) can see their own record
    owner_read = await async_client.get(f"/api/v1/ventures/{venture_id}", headers=auth_headers)
    assert owner_read.status_code == 200
    assert owner_read.json()["vision"] == "Super-secret model architecture"


def test_token_encryption_and_decryption_service():
    """Verify AES Fernet symmetric encryption of third-party integration credentials (Task 6)."""
    raw_secret = "1//04_refresh_token_super_confidential"
    encrypted = encrypt_token(raw_secret)
    assert encrypted != raw_secret
    assert encrypted is not None

    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_secret
