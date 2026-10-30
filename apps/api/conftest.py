"""
Root pytest configuration.

The unit test category runs against an isolated in-memory SQLite fixture, so the
environment is pinned here *before* app.config is imported. supabase/migrations remains
the canonical schema; PostgreSQL parity is proven only by tests/integration/.
"""

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("APP_ENV", "test")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
