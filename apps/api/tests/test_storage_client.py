from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings, settings
from app.integrations.storage_client import StorageService


def test_production_settings_reject_placeholder_configuration() -> None:
    # Explicit empty secrets so OS env from CI/local pytest does not leak into this case.
    with pytest.raises(ValidationError, match="Production configuration is missing real values"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            APP_ENV="production",
            SUPABASE_URL="",
            SUPABASE_SECRET_KEY="",
            SUPABASE_SERVICE_ROLE_KEY="",
            TOKEN_ENCRYPTION_KEY="placeholder_should_fail",
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
        )


def test_production_settings_valid_with_supabase_secret_key() -> None:
    """Verify production settings validate successfully with modern SUPABASE_SECRET_KEY without requiring SUPABASE_JWT_SECRET."""
    prod_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        APP_ENV="production",
        SUPABASE_URL="https://prod.supabase.co",
        SUPABASE_SECRET_KEY="sb_secret_real_production_key_123456789",
        SUPABASE_SERVICE_ROLE_KEY="",
        TOKEN_ENCRYPTION_KEY="real_fernet_production_master_encryption_key",
        DATABASE_URL="postgresql+asyncpg://postgres:pass@db.prod.supabase.co:5432/postgres",
        MCP_ISSUER_URL="https://tajs-second-brain.onrender.com",
        MCP_RESOURCE_SERVER_URL="https://tajs-second-brain.onrender.com/mcp",
    )
    assert prod_settings.is_production() is True
    assert prod_settings.supabase_secret == "sb_secret_real_production_key_123456789"
    assert prod_settings.supabase_jwks_url == "https://prod.supabase.co/auth/v1/.well-known/jwks.json"


def test_production_settings_valid_with_legacy_service_role_key() -> None:
    """Verify production settings maintain backward compatibility with SUPABASE_SERVICE_ROLE_KEY."""
    prod_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        APP_ENV="production",
        SUPABASE_URL="https://prod.supabase.co",
        SUPABASE_SECRET_KEY="",  # force legacy path; do not inherit CI mock secret
        SUPABASE_SERVICE_ROLE_KEY="legacy_service_role_secret_key_12345",
        TOKEN_ENCRYPTION_KEY="real_fernet_production_master_encryption_key",
        DATABASE_URL="postgresql+asyncpg://postgres:pass@db.prod.supabase.co:5432/postgres",
        MCP_ISSUER_URL="https://tajs-second-brain.onrender.com",
        MCP_RESOURCE_SERVER_URL="https://tajs-second-brain.onrender.com/mcp",
    )
    assert prod_settings.supabase_secret == "legacy_service_role_secret_key_12345"


def test_storage_service_headers_with_modern_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify StorageService constructs correct headers using modern SUPABASE_SECRET_KEY."""
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://prod.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "sb_secret_modern_key_abc123")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    storage = StorageService()
    assert storage.use_supabase is True
    headers = storage._service_headers
    assert headers["apikey"] == "sb_secret_modern_key_abc123"
    assert headers["Authorization"] == "Bearer sb_secret_modern_key_abc123"


def test_storage_service_headers_with_legacy_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify StorageService constructs correct headers with legacy fallback."""
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://prod.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "legacy_service_key_xyz789")

    storage = StorageService()
    assert storage.use_supabase is True
    headers = storage._service_headers
    assert headers["apikey"] == "legacy_service_key_xyz789"
    assert headers["Authorization"] == "Bearer legacy_service_key_xyz789"


def test_production_storage_requires_supabase_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    with pytest.raises(RuntimeError, match="Production document storage requires"):
        StorageService()


@pytest.mark.asyncio
async def test_development_storage_uses_local_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    storage = StorageService()
    _, _, _, _, relative_path = await storage.save_upload(
        "test-user", "notes.txt", b"local development only", "text/plain"
    )

    expected = tmp_path / ".storage_buckets" / storage.bucket_name / relative_path
    assert expected.read_bytes() == b"local development only"

    # Local files must be served through an authenticated download, never a fake URL.
    with pytest.raises(RuntimeError, match='authenticated download'):
        await storage.get_signed_url(relative_path)
    assert await storage.read_file(relative_path) == b"local development only"
    with pytest.raises(ValueError):
        await storage.read_file('../outside.txt')

    # Test local delete
    deleted = await storage.delete_file(relative_path)
    assert deleted is True
    assert not expected.exists()


@pytest.mark.asyncio
async def test_supabase_save_upload_with_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://prod.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "sb_secret_test_upload_key_123")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    recorded_requests = []

    async def mock_post(self, url, headers=None, content=None, **kwargs):
        recorded_requests.append({"url": str(url), "headers": headers, "content": content})
        req = httpx.Request("POST", str(url), headers=headers)
        return httpx.Response(200, json={"Key": "test-key"}, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    storage = StorageService(bucket_name="test-bucket")
    sanitized, ext, size, checksum, relative_path = await storage.save_upload(
        "usr_123", "test_file.txt", b"secret storage content", "text/plain"
    )

    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req["url"].startswith("https://prod.supabase.co/storage/v1/object/test-bucket/usr_123/")
    assert req["headers"]["apikey"] == "sb_secret_test_upload_key_123"
    assert req["headers"]["Authorization"] == "Bearer sb_secret_test_upload_key_123"
    assert req["headers"]["x-upsert"] == "false"
    assert req["content"] == b"secret storage content"
    assert sanitized == "test_file.txt"
    assert ext == "txt"
    assert size == len(b"secret storage content")


@pytest.mark.asyncio
async def test_supabase_get_signed_url_with_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://prod.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "sb_secret_test_sign_key_456")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    async def mock_post(self, url, headers=None, json=None, **kwargs):
        assert headers["apikey"] == "sb_secret_test_sign_key_456"
        assert headers["Authorization"] == "Bearer sb_secret_test_sign_key_456"
        assert json == {"expiresIn": 1800}
        req = httpx.Request("POST", str(url), headers=headers)
        return httpx.Response(
            200,
            json={"signedURL": "/object/sign/test-bucket/usr_123/file.txt?token=xyz"},
            request=req,
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    storage = StorageService(bucket_name="test-bucket")
    signed_url = await storage.get_signed_url("usr_123/file.txt", expires_seconds=1800)
    assert signed_url == "https://prod.supabase.co/storage/v1/object/sign/test-bucket/usr_123/file.txt?token=xyz"


@pytest.mark.asyncio
async def test_supabase_delete_file_with_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://prod.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", "sb_secret_test_del_key_789")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    async def mock_request(self, method, url, headers=None, json=None, **kwargs):
        assert method == "DELETE"
        assert url == "https://prod.supabase.co/storage/v1/object/test-bucket"
        assert headers["apikey"] == "sb_secret_test_del_key_789"
        assert headers["Authorization"] == "Bearer sb_secret_test_del_key_789"
        assert json == {"prefixes": ["usr_123/file.txt"]}
        req = httpx.Request(method, str(url), headers=headers)
        return httpx.Response(200, json={"message": "Successfully deleted"}, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

    storage = StorageService(bucket_name="test-bucket")
    success = await storage.delete_file("usr_123/file.txt")
    assert success is True
