"""Secret-safe diagnostics for the isolated staging PostgreSQL connection.

This module never logs connection strings, usernames or passwords.
"""
from __future__ import annotations

import asyncio
import socket
from typing import Any

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.db.dsn import to_async_dsn


def inspect_staging_db_url(url: str, expected_host: str) -> dict[str, Any]:
    """Only return non-secret booleans/driver/port describing parsed DSN."""
    try:
        parsed = make_url(to_async_dsn(url))
        host = (parsed.host or "").lower().rstrip(".")
        expected = expected_host.lower().rstrip(".")
        password = parsed.password or ""
        return {
            "parsed": True,
            "driver_is_asyncpg": parsed.drivername == "postgresql+asyncpg",
            "hostname_matches_supabase_pooler": bool(expected) and host == expected,
            "port_is_5432": parsed.port == 5432,
            "database_is_postgres": parsed.database == "postgres",
            "password_is_set": bool(password),
            "password_looks_like_placeholder": password in {
                "[YOUR-PASSWORD]", "YOUR_PASSWORD", "YOUR-PASSWORD"
            },
        }
    except (ArgumentError, ValueError, TypeError):
        return {"parsed": False}


async def can_resolve_expected_host(expected_host: str) -> str:
    """Check only the public expected hostname, never an untrusted DSN hostname."""
    try:
        await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(
                expected_host, 5432, type=socket.SOCK_STREAM
            ),
            timeout=5,
        )
    except (OSError, asyncio.TimeoutError):
        return "failed"
    return "resolved"
