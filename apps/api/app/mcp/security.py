"""
MCP Authentication, Authorization, Scopes, Rate Limiting, and Audit Security Layer
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mcp import MCPCredentialService

# Capability Scopes
SCOPE_PEOPLE_READ = "mcp:people:read"
SCOPE_MEMORY_READ = "mcp:memory:read"
SCOPE_PROJECTS_READ = "mcp:projects:read"
SCOPE_TASKS_READ = "mcp:tasks:read"
SCOPE_RELATIONSHIPS_READ = "mcp:relationships:read"
SCOPE_CALENDAR_READ = "mcp:calendar:read"
SCOPE_CONTENT_DRAFT = "mcp:content:draft"

ALL_SCOPES = [
    SCOPE_PEOPLE_READ,
    SCOPE_MEMORY_READ,
    SCOPE_PROJECTS_READ,
    SCOPE_TASKS_READ,
    SCOPE_RELATIONSHIPS_READ,
    SCOPE_CALENDAR_READ,
    SCOPE_CONTENT_DRAFT,
]


class MCPScopeError(Exception):
    pass


class MCPRateLimitError(Exception):
    pass


def verify_scope(granted_scopes: List[str], required_scope: str) -> bool:
    if not granted_scopes:
        raise MCPScopeError("No scopes granted.")
    if "*" in granted_scopes or "mcp:all" in granted_scopes:
        return True
    if required_scope in granted_scopes:
        return True
    if required_scope.endswith(":read") and (
        "mcp:read" in granted_scopes or "mcp:group:read" in granted_scopes
    ):
        return True
    if required_scope.endswith(":draft") and (
        "mcp:draft" in granted_scopes or "mcp:group:draft" in granted_scopes
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
