"""Staging DSN diagnostics must identify bad parsing without leaking secrets."""

import pytest

from app.db.staging_dns_diagnostics import inspect_staging_db_url


EXPECTED = "aws-0-ap-southeast-1.pooler.supabase.com"


@pytest.mark.parametrize(
    ("dsn", "expected_match"),
    [
        (
            "postgresql://postgres.example:secret@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
            True,
        ),
        (
            "postgresql+asyncpg://postgres.example:secret@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
            True,
        ),
        (
            "postgresql+asyncpg://postgres.example:secret@wrong.supabase.com:5432/postgres",
            False,
        ),
        (
            "postgresql+asyncpg://postgres.example:PA@SS@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
            False,
        ),
    ],
)
def test_staging_database_target_match(dsn: str, expected_match: bool) -> None:
    result = inspect_staging_db_url(dsn, EXPECTED)
    assert result["hostname_matches_supabase_pooler"] is expected_match
    assert result["driver_is_asyncpg"] is True
    assert result["password_is_set"] is True
    assert "secret" not in str(result)
    assert "PA" not in str(result)
    assert "postgres.example" not in str(result)


def test_placeholder_detected_without_logging_credential() -> None:
    dsn = (
        "postgresql+asyncpg://postgres.example:%5BYOUR-PASSWORD%5D@"
        "aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    )
    result = inspect_staging_db_url(dsn, EXPECTED)
    assert result["password_looks_like_placeholder"] is True
    assert "[YOUR-PASSWORD]" not in str(result)


def test_bad_port_never_leaks_url() -> None:
    dsn = "postgresql+asyncpg://postgres.example:topsecret@server.invalid:wrong/postgres"
    assert inspect_staging_db_url(dsn, EXPECTED) == {"parsed": False}
