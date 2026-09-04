"""
One explicit backend contract for PostgreSQL connection URLs.

The application talks to PostgreSQL over **asyncpg** only; psycopg2 is not a dependency
and is not installed by requirements.txt. A bare ``postgresql://`` URL makes SQLAlchemy
select psycopg2 and fail with ``No module named 'psycopg2'``.

Operators may therefore write either scheme in configuration and documentation, and the
application normalizes to ``postgresql+asyncpg://`` before creating an engine. The raw
libpq form (``postgresql://``) is what asyncpg.connect() itself expects, so both
directions are provided.
"""

from __future__ import annotations

ASYNC_SCHEME = "postgresql+asyncpg://"
LIBPQ_SCHEME = "postgresql://"

_SYNC_PREFIXES = (
    "postgresql+psycopg2://",
    "postgresql+psycopg://",
    "postgres://",
    LIBPQ_SCHEME,
)


def to_async_dsn(url: str) -> str:
    """Return `url` with the asyncpg driver selected explicitly."""
    candidate = (url or "").strip()
    if not candidate:
        return candidate
    if candidate.startswith(ASYNC_SCHEME):
        return candidate
    for prefix in _SYNC_PREFIXES:
        if candidate.startswith(prefix):
            return ASYNC_SCHEME + candidate[len(prefix) :]
    return candidate


def to_libpq_dsn(url: str) -> str:
    """Return `url` in the plain libpq form that ``asyncpg.connect()`` accepts."""
    candidate = (url or "").strip()
    if candidate.startswith(ASYNC_SCHEME):
        return LIBPQ_SCHEME + candidate[len(ASYNC_SCHEME) :]
    return candidate
