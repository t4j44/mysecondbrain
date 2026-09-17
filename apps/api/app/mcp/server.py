"""Official MCP SDK server mounted into the unified FastAPI process."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional, cast

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl

from app.core.config import settings
from app.dependencies.database import admin_db_session, rls_db_session
from app.mcp.extraction import extract_session_intelligence
from app.mcp.security import (
    FINALIZE_REQUIRED_SCOPES,
    READ_SCOPES,
    SCOPE_CALENDAR_READ,
    SCOPE_CONTENT_DRAFT,
    SCOPE_DECISIONS_WRITE,
    SCOPE_MEMORY_READ,
    SCOPE_MEMORY_WRITE,
    SCOPE_PEOPLE_READ,
    SCOPE_PEOPLE_WRITE,
    SCOPE_PROJECTS_READ,
    SCOPE_PROJECTS_WRITE,
    SCOPE_RELATIONSHIPS_READ,
    SCOPE_SESSIONS_WRITE,
    SCOPE_TASKS_READ,
    SCOPE_TASKS_WRITE,
    verify_scope,
)
from app.mcp.tools import MCPDomainTools
from app.repositories.mcp import MCPCredentialRepository


class DatabaseTokenVerifier(TokenVerifier):
    """Validate opaque MCP credentials against the shared application database."""

    def __init__(self) -> None:
        self.repo = MCPCredentialRepository()

    async def verify_token(self, token: str) -> AccessToken | None:
        # System operation: matching a key requires scanning credentials across profiles.
        async with admin_db_session(reason="mcp_token_verification") as db:
            verified = await self.repo.verify_api_key(db, token)
            await db.commit()
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
CREATES = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, open_world_hint=False
)
UPDATES = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, open_world_hint=False
)


def _authenticated_user_id(*required_scopes: str) -> str:
    access_token = get_access_token()
    if not access_token or not access_token.subject:
        raise PermissionError("A valid MCP bearer credential is required.")
    for scope in required_scopes:
        verify_scope(access_token.scopes, scope)
    return access_token.subject


@asynccontextmanager
async def _domain(required_scope: str) -> AsyncGenerator[MCPDomainTools, None]:
    """Scope-check the MCP credential, then read under the owner's RLS claims."""
    user_id = _authenticated_user_id(required_scope)
    async with rls_db_session(user_id) as db:
        yield MCPDomainTools(db=db, user_id=user_id)


@asynccontextmanager
async def _write_domain(*required_scopes: str) -> AsyncGenerator[MCPDomainTools, None]:
    """
    Scope-check the MCP credential, then run the whole write batch as ONE owner-scoped
    transaction: BEGIN on first statement, COMMIT on clean exit, ROLLBACK on any failure.

    A credential without the granular write scope never reaches the database at all, and
    RLS remains the second boundary for whatever the transaction does touch. Model
    inference must happen before this context is entered — see app/mcp/extraction.py.
    """
    user_id = _authenticated_user_id(*required_scopes)
    async with rls_db_session(user_id) as db:
        domain = MCPDomainTools(db=db, user_id=user_id)
        try:
            yield domain
        except Exception:
            await db.rollback()
            raise
        await db.commit()


@mcp_server.tool(annotations=READ_ONLY)
async def search_people(query: Optional[str] = None, limit: int = 20) -> list[dict[str, Any]]:
    """Search the authenticated user's CRM contacts."""
    async with _domain(SCOPE_PEOPLE_READ) as domain:
        return await domain.search_people(query=query, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def search_memory(
    query: Optional[str] = None, category: Optional[str] = None, limit: int = 20
) -> list[dict[str, Any]]:
    """Search the authenticated user's memories and notes."""
    async with _domain(SCOPE_MEMORY_READ) as domain:
        return await domain.search_memory(query=query, category=category, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_projects(
    status: Optional[str] = None, limit: int = 20
) -> list[dict[str, Any]]:
    """List the authenticated user's projects."""
    async with _domain(SCOPE_PROJECTS_READ) as domain:
        return await domain.get_projects(status=status, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_tasks(status: Optional[str] = None, limit: int = 20) -> list[dict[str, Any]]:
    """List the authenticated user's tasks."""
    async with _domain(SCOPE_TASKS_READ) as domain:
        return await domain.get_tasks(status=status, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_relationship_history(
    person_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    """Return the authenticated user's interaction history for a contact."""
    async with _domain(SCOPE_RELATIONSHIPS_READ) as domain:
        return await domain.get_relationship_history(person_id=person_id, limit=limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_calendar(limit: int = 20) -> list[dict[str, Any]]:
    """List the authenticated user's upcoming meetings."""
    async with _domain(SCOPE_CALENDAR_READ) as domain:
        return await domain.get_calendar(limit=limit)


@mcp_server.tool(annotations=DRAFT_ONLY)
async def generate_linkedin_post(
    topic: str, style_tone: Optional[str] = "executive"
) -> dict[str, Any]:
    """Generate a review-required LinkedIn draft without publishing it."""
    async with _domain(SCOPE_CONTENT_DRAFT) as domain:
        return await domain.generate_linkedin_post(topic=topic, style_tone=style_tone)


@mcp_server.tool(annotations=DRAFT_ONLY)
async def generate_case_study(project_name: str) -> dict[str, Any]:
    """Generate a review-required case-study draft without publishing it."""
    async with _domain(SCOPE_CONTENT_DRAFT) as domain:
        return await domain.generate_case_study(project_name=project_name)


@mcp_server.tool(annotations=DRAFT_ONLY)
async def generate_weekly_review() -> dict[str, Any]:
    """Generate a private weekly review for the authenticated user."""
    async with _domain(SCOPE_CONTENT_DRAFT) as domain:
        return await domain.generate_weekly_review()


# ---------------------------------------------------------------------------
# WRITE TOOLS (G5). Every one of them runs through _write_domain, so it is guarded by a
# granular write scope, executes under the owner's RLS claims, commits exactly once and
# rolls back as a unit. A read-only credential fails scope verification before any SQL.
# ---------------------------------------------------------------------------


@mcp_server.tool(annotations=CREATES)
async def create_task(
    title: str,
    description: Optional[str] = None,
    status: Optional[str] = "todo",
    priority: Optional[str] = "medium",
    due_date: Optional[str] = None,
    project_id: Optional[str] = None,
    venture_id: Optional[str] = None,
    person_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Create a task for the authenticated user. Requires mcp:tasks:write."""
    async with _write_domain(SCOPE_TASKS_WRITE) as domain:
        return await domain.create_task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            project_id=project_id,
            venture_id=venture_id,
            person_id=person_id,
            tags=tags,
        )


@mcp_server.tool(annotations=UPDATES)
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    completion_date: Optional[str] = None,
    project_id: Optional[str] = None,
    venture_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Update a task owned by the authenticated user. Requires mcp:tasks:write."""
    async with _write_domain(SCOPE_TASKS_WRITE) as domain:
        return await domain.update_task(
            task_id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            completion_date=completion_date,
            project_id=project_id,
            venture_id=venture_id,
            tags=tags,
        )


@mcp_server.tool(annotations=UPDATES)
async def complete_task(task_id: str, completion_notes: Optional[str] = None) -> dict[str, Any]:
    """Mark a task complete for the authenticated user. Requires mcp:tasks:write."""
    async with _write_domain(SCOPE_TASKS_WRITE) as domain:
        return await domain.complete_task(task_id=task_id, completion_notes=completion_notes)


@mcp_server.tool(annotations=CREATES)
async def create_person(
    name: str,
    role: Optional[str] = None,
    company: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    relationship_type: Optional[str] = "contact",
    notes: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Create a CRM contact, returning the existing record when the email or name already
    matches one. Requires mcp:people:write.
    """
    async with _write_domain(SCOPE_PEOPLE_WRITE) as domain:
        return await domain.create_person(
            name=name,
            role=role,
            company=company,
            industry=industry,
            location=location,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
            relationship_type=relationship_type,
            notes=notes,
            tags=tags,
        )


@mcp_server.tool(annotations=UPDATES)
async def update_person(
    person_id: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
    company: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    relationship_type: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Update a CRM contact owned by the authenticated user. Requires mcp:people:write."""
    async with _write_domain(SCOPE_PEOPLE_WRITE) as domain:
        return await domain.update_person(
            person_id=person_id,
            name=name,
            role=role,
            company=company,
            industry=industry,
            location=location,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
            relationship_type=relationship_type,
            notes=notes,
            tags=tags,
        )


@mcp_server.tool(annotations=CREATES)
async def create_project(
    name: str,
    description: Optional[str] = None,
    venture_id: Optional[str] = None,
    status: Optional[str] = "in_progress",
    priority: Optional[str] = "medium",
    progress: Optional[int] = 0,
    target_date: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a project, returning the existing record when the name already matches one.
    Requires mcp:projects:write.
    """
    async with _write_domain(SCOPE_PROJECTS_WRITE) as domain:
        return await domain.create_project(
            name=name,
            description=description,
            venture_id=venture_id,
            status=status,
            priority=priority,
            progress=progress,
            target_date=target_date,
        )


@mcp_server.tool(annotations=UPDATES)
async def update_project(
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    venture_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    progress: Optional[int] = None,
    target_date: Optional[str] = None,
    completion_date: Optional[str] = None,
) -> dict[str, Any]:
    """Update a project owned by the authenticated user. Requires mcp:projects:write."""
    async with _write_domain(SCOPE_PROJECTS_WRITE) as domain:
        return await domain.update_project(
            project_id=project_id,
            name=name,
            description=description,
            venture_id=venture_id,
            status=status,
            priority=priority,
            progress=progress,
            target_date=target_date,
            completion_date=completion_date,
        )


@mcp_server.tool(annotations=CREATES)
async def save_memory(
    title: str,
    content: str,
    category: Optional[str] = "note",
    tags: Optional[list[str]] = None,
    linked_venture_id: Optional[str] = None,
    linked_person_id: Optional[str] = None,
    importance: int = 5,
) -> dict[str, Any]:
    """Save a memory or note for the authenticated user. Requires mcp:memory:write."""
    async with _write_domain(SCOPE_MEMORY_WRITE) as domain:
        return await domain.save_memory(
            title=title,
            content=content,
            category=category,
            tags=tags,
            linked_venture_id=linked_venture_id,
            linked_person_id=linked_person_id,
            importance=importance,
        )


@mcp_server.tool(annotations=CREATES)
async def save_decision(
    decision: str,
    context: Optional[str] = None,
    rationale: Optional[str] = None,
    alternatives: Optional[list[str]] = None,
    expected_impact: Optional[str] = None,
    project_id: Optional[str] = None,
    venture_id: Optional[str] = None,
) -> dict[str, Any]:
    """Record a decision with its rationale and rejected alternatives. Requires mcp:decisions:write."""
    async with _write_domain(SCOPE_DECISIONS_WRITE) as domain:
        return await domain.save_decision(
            decision=decision,
            context=context,
            rationale=rationale,
            alternatives=alternatives,
            expected_impact=expected_impact,
            project_id=project_id,
            venture_id=venture_id,
        )


@mcp_server.tool(annotations=CREATES)
async def save_work_session(
    title: str,
    summary: Optional[str] = None,
    detailed_notes: Optional[str] = None,
    project_id: Optional[str] = None,
    venture_id: Optional[str] = None,
    person_id: Optional[str] = None,
    key_takeaways: Optional[list[str]] = None,
    next_actions: Optional[list[str]] = None,
    client_request_id: Optional[str] = None,
    provider: Optional[str] = None,
) -> dict[str, Any]:
    """
    Record a work session verbatim, without extraction or downstream record creation.
    Use finalize_work_session for the full workflow. Requires mcp:sessions:write.
    """
    async with _write_domain(SCOPE_SESSIONS_WRITE) as domain:
        return await domain.save_work_session(
            title=title,
            summary=summary,
            detailed_notes=detailed_notes,
            project_id=project_id,
            venture_id=venture_id,
            person_id=person_id,
            key_takeaways=key_takeaways,
            next_actions=next_actions,
            client_request_id=client_request_id,
            provider=provider,
        )


@mcp_server.tool(annotations=CREATES)
async def finalize_work_session(
    provider: Optional[str] = "mcp_client",
    session_reference: Optional[str] = None,
    client_request_id: Optional[str] = None,
    summary: Optional[str] = None,
    session_payload: Optional[dict[str, Any]] = None,
    venture: Optional[str] = None,
    project: Optional[str] = None,
    title: Optional[str] = None,
) -> dict[str, Any]:
    """
    Finalize an AI work session: extract objective, research, findings, decisions and their
    rationale and rejected alternatives, tasks, people, organizations, commitments, evidence,
    artifacts, skills and open questions, then persist them with provenance in a single
    transaction. Replaying the same session_reference or client_request_id creates nothing new.

    Requires the full write set: mcp:sessions:write, mcp:tasks:write, mcp:decisions:write,
    mcp:memory:write, mcp:people:write (a single mcp:write grant covers all of them).
    """
    # Extraction runs first and completely outside the transaction: inference latency must
    # never hold a database connection or locks open.
    extracted = await extract_session_intelligence(
        summary=summary, session_payload=session_payload, provider=provider,
        user_id=_authenticated_user_id(*FINALIZE_REQUIRED_SCOPES),
    )
    fields = extracted["fields"]

    async with _write_domain(*FINALIZE_REQUIRED_SCOPES) as domain:
        return await domain.finalize_work_session(
            provider=provider,
            session_reference=session_reference,
            client_request_id=client_request_id,
            summary=summary,
            session_payload=session_payload,
            venture_hint=venture,
            project_hint=project,
            title=title,
            extraction=extracted["extraction"],
            **fields,
        )


# ---------------------------------------------------------------------------
# MCP exposure truth: every MCPDomainTools capability is now registered. Reads and drafts
# are scope-checked and RLS-scoped; writes additionally require a granular write scope and
# a single committed transaction (G5_MCP_FINALIZE_GATE.md).
# ---------------------------------------------------------------------------


@mcp_server.tool(annotations=READ_ONLY)
async def search_context(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve approved context with real semantic search or a labelled keyword fallback."""
    owner = _authenticated_user_id(*sorted(READ_SCOPES))
    async with rls_db_session(owner) as db:
        return await MCPDomainTools(db=db, user_id=owner).search_context(query, limit)

@mcp_server.tool(annotations=READ_ONLY)
async def find_relevant_contacts(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Suggest contacts from recorded links, with evidence and no claimed availability."""
    owner = _authenticated_user_id(*sorted(READ_SCOPES))
    async with rls_db_session(owner) as db:
        return await MCPDomainTools(db=db, user_id=owner).find_relevant_contacts(query, limit)


@mcp_server.tool(annotations=READ_ONLY)
async def search_documents(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search only the authenticated owner's extracted documents."""
    owner = _authenticated_user_id(*sorted(READ_SCOPES))
    async with rls_db_session(owner) as db:
        return await MCPDomainTools(db=db, user_id=owner).search_documents(query, limit)


@mcp_server.tool(annotations=READ_ONLY)
async def get_person_context(person_id: str) -> dict[str, Any]:
    """Read the person's recorded relationship history, affiliations and commitments."""
    owner = _authenticated_user_id(*sorted(READ_SCOPES))
    async with rls_db_session(owner) as db:
        return await MCPDomainTools(db=db, user_id=owner).get_person_context(person_id)

@mcp_server.tool(annotations=READ_ONLY)
async def prepare_meeting(person_id: str) -> dict[str, Any]:
    """Prepare a factual brief from the selected person's saved history."""
    return await get_person_context(person_id)

@mcp_server.tool(annotations=READ_ONLY)
async def get_commitments(person_id: Optional[str] = None, overdue_only: bool = False, limit: int = 20) -> list[dict[str, Any]]:
    """Read open commitments, optionally overdue or related to one person."""
    owner = _authenticated_user_id(*sorted(READ_SCOPES))
    async with rls_db_session(owner) as db:
        return await MCPDomainTools(db=db, user_id=owner).get_commitments(person_id, overdue_only, limit)

@mcp_server.tool(annotations=CREATES)
async def create_commitment(description: str, person_id: Optional[str] = None, direction: str = 'unspecified', due_at: Optional[str] = None) -> dict[str, Any]:
    """Save a commitment the user explicitly requested."""
    async with _write_domain(SCOPE_TASKS_WRITE) as domain:
        return await domain.create_commitment(description, person_id, direction, due_at)

@mcp_server.tool(annotations=UPDATES)
async def complete_commitment(commitment_id: str) -> dict[str, Any]:
    """Complete an explicitly identified commitment."""
    async with _write_domain(SCOPE_TASKS_WRITE) as domain:
        return await domain.complete_commitment(commitment_id)

@mcp_server.tool(annotations=CREATES)
async def capture_context(text: str = '', draft_id: Optional[str] = None, reviewed_proposal: Optional[dict] = None, confirmed: bool = False) -> dict[str, Any]:
    """Propose first. Show the proposal to the user; obtain confirmation before submitting draft_id, reviewed_proposal and confirmed=true."""
    async with _write_domain(*FINALIZE_REQUIRED_SCOPES) as domain:
        return await domain.capture_context(text, draft_id, reviewed_proposal, confirmed)


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
