from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, settings
from app.integrations.storage_client import StorageService


def test_production_settings_reject_placeholder_configuration() -> None:
    with pytest.raises(ValidationError, match="Production configuration is missing real values"):
        Settings(_env_file=None, ENVIRONMENT="production", APP_ENV="production")


def test_production_settings_valid_with_supabase_secret_key() -> None:
    """Verify production settings validate successfully with modern SUPABASE_SECRET_KEY without requiring SUPABASE_JWT_SECRET."""
    prod_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        APP_ENV="production",
        SUPABASE_URL="https://prod.supabase.co",
        SUPABASE_SECRET_KEY="sb_secret_real_production_key_123456789",
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
