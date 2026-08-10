from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, settings
from app.integrations.storage_client import StorageService


def test_production_settings_reject_placeholder_configuration() -> None:
    with pytest.raises(ValidationError, match="Production configuration is missing real values"):
        Settings(_env_file=None, ENVIRONMENT="production", APP_ENV="production")


def test_production_storage_requires_supabase_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
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
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    storage = StorageService()
    _, _, _, _, relative_path = await storage.save_upload(
        "test-user", "notes.txt", b"local development only", "text/plain"
    )

    expected = tmp_path / ".storage_buckets" / storage.bucket_name / relative_path
    assert expected.read_bytes() == b"local development only"
