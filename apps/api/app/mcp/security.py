"""
MCP Authentication, Authorization, Scopes, Rate Limiting, and Audit Security Layer
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mcp import MCPCredentialService

# Capability Scopes - Read & Draft
SCOPE_PEOPLE_READ = "mcp:people:read"
SCOPE_MEMORY_READ = "mcp:memory:read"
SCOPE_PROJECTS_READ = "mcp:projects:read"
SCOPE_TASKS_READ = "mcp:tasks:read"
SCOPE_RELATIONSHIPS_READ = "mcp:relationships:read"
SCOPE_CALENDAR_READ = "mcp:calendar:read"
SCOPE_CONTENT_DRAFT = "mcp:content:draft"

# Capability Scopes - Write & Operations
SCOPE_MEMORY_WRITE = "mcp:memory:write"
SCOPE_TASKS_WRITE = "mcp:tasks:write"
SCOPE_PROJECTS_WRITE = "mcp:projects:write"
SCOPE_PEOPLE_WRITE = "mcp:people:write"
SCOPE_DECISIONS_WRITE = "mcp:decisions:write"
SCOPE_SESSIONS_WRITE = "mcp:sessions:write"
SCOPE_EVIDENCE_WRITE = "mcp:evidence:write"
SCOPE_WRITE_ALL = "mcp:write"

ALL_SCOPES = [
    SCOPE_PEOPLE_READ,
    SCOPE_MEMORY_READ,
    SCOPE_PROJECTS_READ,
    SCOPE_TASKS_READ,
    SCOPE_RELATIONSHIPS_READ,
    SCOPE_CALENDAR_READ,
    SCOPE_CONTENT_DRAFT,
    SCOPE_MEMORY_WRITE,
    SCOPE_TASKS_WRITE,
    SCOPE_PROJECTS_WRITE,
    SCOPE_PEOPLE_WRITE,
    SCOPE_DECISIONS_WRITE,
    SCOPE_SESSIONS_WRITE,
    SCOPE_EVIDENCE_WRITE,
]


class MCPScopeError(Exception):
    pass


class MCPRateLimitError(Exception):
    pass


def _normalize_scope(scope: str) -> str:
    """Normalize scope strings e.g. 'tasks:write' -> 'mcp:tasks:write'."""
    s = scope.strip().lower()
    if not s.startswith("mcp:") and s not in {"*", "all"}:
        return f"mcp:{s}"
    return s


def verify_scope(granted_scopes: List[str], required_scope: str) -> bool:
    if not granted_scopes:
        raise MCPScopeError("No scopes granted.")

    norm_granted = {_normalize_scope(s) for s in granted_scopes}
    norm_required = _normalize_scope(required_scope)

    # Superuser / wildcard grants
    if "*" in granted_scopes or "mcp:all" in norm_granted or "all" in granted_scopes:
        return True

    # Exact match (normalized)
    if norm_required in norm_granted:
        return True

    # Write group grant
    if norm_required.endswith(":write") and (
        "mcp:write" in norm_granted or "write" in granted_scopes
    ):
        return True

    # Read group grant
    if norm_required.endswith(":read") and (
        "mcp:read" in norm_granted
        or "read" in granted_scopes
        or "mcp:group:read" in norm_granted
    ):
        return True

    # Draft group grant
    if norm_required.endswith(":draft") and (
        "mcp:draft" in norm_granted
        or "draft" in granted_scopes
        or "mcp:group:draft" in norm_granted
    ):
        return True

    raise MCPScopeError(f"Scope '{required_scope}' is not granted.")


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int = 60):
        self.limit_per_minute = limit_per_minute
        self.windows: Dict[str, List[float]] = {}

    def check_and_record(self, client_id: str) -> bool:
        now = time.time()
        timestamps = self.windows.get(client_id, [])
        valid_timestamps = [t for t in timestamps if now - t <= 60.0]
        if len(valid_timestamps) >= self.limit_per_minute:
            self.windows[client_id] = valid_timestamps
            return False
        valid_timestamps.append(now)
        self.windows[client_id] = valid_timestamps
        return True


class MCPSecurityContext(BaseModel):
    user_id: str
    credential_id: str
    client_name: str
    granted_scopes: List[str]


credential_service = MCPCredentialService()


async def authorize_mcp_request(
    db: AsyncSession,
    api_key: Optional[str],
    required_scope: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
) -> MCPSecurityContext:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing MCP authentication API key. Provide X-MCP-API-KEY header.",
        )

    clean_key = api_key.replace("Bearer ", "").strip()
    verified = await credential_service.repo.verify_api_key(db, clean_key)

    if not verified or verified.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, inactive, or revoked MCP credential.",
        )

    granted_scopes = verified.get("scopes", [])
    try:
        verify_scope(granted_scopes, required_scope)
    except MCPScopeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"MCP credential lacks required capability scope '{required_scope}'. Granted: {granted_scopes}",
        ) from exc

    return MCPSecurityContext(
        user_id=str(verified["user_id"]),
        credential_id=str(verified["credential_id"]),
        client_name=str(verified.get("client_name", "Unknown MCP Client")),
        granted_scopes=granted_scopes,
    )
