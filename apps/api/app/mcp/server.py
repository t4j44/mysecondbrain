"""Official MCP SDK server mounted into the unified FastAPI process."""

from typing import Any, Optional, cast

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl

from app.core.config import settings
from app.dependencies.database import AsyncSessionLocal
from app.mcp.security import (
    SCOPE_CALENDAR_READ,
    SCOPE_CONTENT_DRAFT,
    SCOPE_MEMORY_READ,
    SCOPE_PEOPLE_READ,
    SCOPE_PROJECTS_READ,
    SCOPE_RELATIONSHIPS_READ,
    SCOPE_TASKS_READ,
    verify_scope,
)
from app.mcp.tools import MCPDomainTools
from app.repositories.mcp import MCPCredentialRepository


class DatabaseTokenVerifier(TokenVerifier):
    """Validate opaque MCP credentials against the shared application database."""

    def __init__(self) -> None:
        self.repo = MCPCredentialRepository()

    async def verify_token(self, token: str) -> AccessToken | None:
        async with AsyncSessionLocal() as db:
            verified = await self.repo.verify_api_key(db, token)
        if not verified or verified.get("status") != "active":
            return None
        return AccessToken(
            token=token,
            client_id=str(verified["credential_id"]),
            scopes=list(verified.get("scopes", [])),
            resource=settings.MCP_RESOURCE_SERVER_URL,
            subject=str(verified["user_id"]),
            claims={"client_name": str(verified.get("client_name", "MCP client"))},
        )


mcp_server = MCPServer(
    name="tajs-second-brain",
    title="Taj's Second Brain",
    description="User-scoped founder operations, CRM, memory, project, and drafting tools.",
    version="1.0.0",
    token_verifier=DatabaseTokenVerifier(),
    auth=AuthSettings(
        issuer_url=cast(AnyHttpUrl, settings.MCP_ISSUER_URL),
        resource_server_url=cast(AnyHttpUrl, settings.MCP_RESOURCE_SERVER_URL),
    ),
)

READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, open_world_hint=False
)
DRAFT_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, open_world_hint=False
)


def _authenticated_user_id(required_scope: str) -> str:
    access_token = get_access_token()
    if not access_token or not access_token.subject:
        raise PermissionError("A valid MCP bearer credential is required.")
    verify_scope(access_token.scopes, required_scope)
    return access_token.subject


async def _domain(required_scope: str) -> tuple[Any, MCPDomainTools]:
    user_id = _authenticated_user_id(required_scope)
    db = AsyncSessionLocal()
    return db, MCPDomainTools(db=db, user_id=user_id)


@mcp_server.tool(annotations=READ_ONLY)
async def search_people(query: Optional[str] = None, limit: int = 20) -> list[dict[str, Any]]:
    """Search the authenticated user's CRM contacts."""
    db, domain = await _domain(SCOPE_PEOPLE_READ)
    async with db:
        return await domain.search_people(query=query, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def search_memory(
    query: Optional[str] = None, category: Optional[str] = None, limit: int = 20
) -> list[dict[str, Any]]:
    """Search the authenticated user's memories and notes."""
    db, domain = await _domain(SCOPE_MEMORY_READ)
    async with db:
        return await domain.search_memory(query=query, category=category, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_projects(
    status: Optional[str] = None, limit: int = 20
) -> list[dict[str, Any]]:
    """List the authenticated user's projects."""
    db, domain = await _domain(SCOPE_PROJECTS_READ)
    async with db:
        return await domain.get_projects(status=status, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_tasks(status: Optional[str] = None, limit: int = 20) -> list[dict[str, Any]]:
    """List the authenticated user's tasks."""
    db, domain = await _domain(SCOPE_TASKS_READ)
    async with db:
        return await domain.get_tasks(status=status, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_relationship_history(
    person_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    """Return the authenticated user's interaction history for a contact."""
    db, domain = await _domain(SCOPE_RELATIONSHIPS_READ)
    async with db:
        return await domain.get_relationship_history(person_id=person_id, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_calendar(limit: int = 20) -> list[dict[str, Any]]:
    """List the authenticated user's upcoming meetings."""
    db, domain = await _domain(SCOPE_CALENDAR_READ)
    async with db:
        return await domain.get_calendar(limit=limit)


@mcp_server.tool(annotations=DRAFT_ONLY)
async def generate_linkedin_post(
    topic: str, style_tone: Optional[str] = "executive"
) -> dict[str, Any]:
    """Generate a review-required LinkedIn draft without publishing it."""
    db, domain = await _domain(SCOPE_CONTENT_DRAFT)
    async with db:
        return await domain.generate_linkedin_post(topic=topic, style_tone=style_tone)


@mcp_server.tool(annotations=DRAFT_ONLY)
async def generate_case_study(project_name: str) -> dict[str, Any]:
    """Generate a review-required case-study draft without publishing it."""
    db, domain = await _domain(SCOPE_CONTENT_DRAFT)
    async with db:
        return await domain.generate_case_study(project_name=project_name)


@mcp_server.tool(annotations=DRAFT_ONLY)
async def generate_weekly_review() -> dict[str, Any]:
    """Generate a private weekly review for the authenticated user."""
    db, domain = await _domain(SCOPE_CONTENT_DRAFT)
    async with db:
        return await domain.generate_weekly_review()


mcp_asgi_app = mcp_server.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=settings.MCP_ALLOWED_HOSTS,
        allowed_origins=settings.CORS_ORIGINS,
    ),
)

__all__ = ["mcp_asgi_app", "mcp_server"]
