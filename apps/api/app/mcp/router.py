"""
FastAPI Router for Streamable HTTP Model Context Protocol (MCP) Server Endpoint mounted at /mcp.
Module Owner: Agent 10 & Agent 3 — ADR-013 Single Render Service Architecture
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.dependencies.database import admin_db_session, rls_db_session
from app.mcp.extraction import extract_session_intelligence
from app.mcp.security import (
    FINALIZE_REQUIRED_SCOPES,
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
    MCPScopeError,
    authorize_mcp_request,
    verify_scope,
)
from app.mcp.tools import MCPDomainTools

router = APIRouter(tags=["MCP Streamable HTTP Server"])


class MCPToolInvocation(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


# Tool Manifest definitions
MCP_TOOLS_MANIFEST: List[Dict[str, Any]] = [
    {
        "name": "search_people",
        "description": "Search founder network CRM contacts by name, company, or role.",
        "required_scope": SCOPE_PEOPLE_READ,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "search_memory",
        "description": (
            "Keyword/substring search across founder memories and notes. "
            "Not semantic vector RAG; confidence scores are unavailable."
        ),
        "required_scope": SCOPE_MEMORY_READ,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "get_projects",
        "description": "Retrieve active projects across ventures (Justor AI, Zqtion, IEXF, CMOOS).",
        "required_scope": SCOPE_PROJECTS_READ,
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "get_tasks",
        "description": "Retrieve active tasks from Linear/Notion task management system.",
        "required_scope": SCOPE_TASKS_READ,
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "get_relationship_history",
        "description": "Retrieve interaction timeline for a specific person profile in CRM.",
        "required_scope": SCOPE_RELATIONSHIPS_READ,
        "input_schema": {
            "type": "object",
            "properties": {
                "person_id": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["person_id"],
        },
    },
    {
        "name": "get_calendar",
        "description": "Retrieve upcoming scheduled meetings and calendar events.",
        "required_scope": SCOPE_CALENDAR_READ,
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 20}},
        },
    },
    {
        "name": "generate_linkedin_post",
        "description": "Synthesize authentic founder LinkedIn post draft.",
        "required_scope": SCOPE_CONTENT_DRAFT,
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}, "style_tone": {"type": "string"}},
            "required": ["topic"],
        },
    },
    {
        "name": "generate_case_study",
        "description": "Generate professional portfolio case study draft from venture data.",
        "required_scope": SCOPE_CONTENT_DRAFT,
        "input_schema": {
            "type": "object",
            "properties": {"project_name": {"type": "string"}},
            "required": ["project_name"],
        },
    },
    {
        "name": "generate_weekly_review",
        "description": "Generate AI weekly executive review and completed task summary.",
        "required_scope": SCOPE_CONTENT_DRAFT,
        "input_schema": {"type": "object", "properties": {}},
    },
]


# Write tools (G5). Each entry declares the granular scope a credential must hold; a
# read-only credential is rejected with 403 before any database work happens.
MCP_WRITE_TOOLS_MANIFEST: List[Dict[str, Any]] = [
    {
        "name": "create_task",
        "description": "Create a task for the authenticated user.",
        "required_scope": SCOPE_TASKS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "default": "todo"},
                "priority": {"type": "string", "default": "medium"},
                "due_date": {"type": "string", "format": "date-time"},
                "project_id": {"type": "string"},
                "venture_id": {"type": "string"},
                "person_id": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],
        },
    },
    {
        "name": "update_task",
        "description": "Update a task owned by the authenticated user.",
        "required_scope": SCOPE_TASKS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string"},
                "priority": {"type": "string"},
                "due_date": {"type": "string", "format": "date-time"},
                "completion_date": {"type": "string", "format": "date-time"},
                "project_id": {"type": "string"},
                "venture_id": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "complete_task",
        "description": "Mark a task complete with optional completion notes.",
        "required_scope": SCOPE_TASKS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "completion_notes": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "create_person",
        "description": (
            "Create a CRM contact. Returns the existing record when the email or name "
            "already matches one."
        ),
        "required_scope": SCOPE_PEOPLE_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "role": {"type": "string"},
                "company": {"type": "string"},
                "industry": {"type": "string"},
                "location": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "linkedin_url": {"type": "string"},
                "relationship_type": {"type": "string", "default": "contact"},
                "notes": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_person",
        "description": "Update a CRM contact owned by the authenticated user.",
        "required_scope": SCOPE_PEOPLE_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "person_id": {"type": "string"},
                "name": {"type": "string"},
                "role": {"type": "string"},
                "company": {"type": "string"},
                "industry": {"type": "string"},
                "location": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "linkedin_url": {"type": "string"},
                "relationship_type": {"type": "string"},
                "notes": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["person_id"],
        },
    },
    {
        "name": "create_project",
        "description": (
            "Create a project. Returns the existing record when the name already matches one."
        ),
        "required_scope": SCOPE_PROJECTS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "venture_id": {"type": "string"},
                "status": {"type": "string", "default": "in_progress"},
                "priority": {"type": "string", "default": "medium"},
                "progress": {"type": "integer", "default": 0},
                "target_date": {"type": "string", "format": "date-time"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_project",
        "description": "Update a project owned by the authenticated user.",
        "required_scope": SCOPE_PROJECTS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "venture_id": {"type": "string"},
                "status": {"type": "string"},
                "priority": {"type": "string"},
                "progress": {"type": "integer"},
                "target_date": {"type": "string", "format": "date-time"},
                "completion_date": {"type": "string", "format": "date-time"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "save_memory",
        "description": "Save a memory or note for the authenticated user.",
        "required_scope": SCOPE_MEMORY_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string", "default": "note"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "linked_venture_id": {"type": "string"},
                "linked_person_id": {"type": "string"},
                "importance": {"type": "integer", "default": 5},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "save_decision",
        "description": "Record a decision with its rationale and rejected alternatives.",
        "required_scope": SCOPE_DECISIONS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "context": {"type": "string"},
                "rationale": {"type": "string"},
                "alternatives": {"type": "array", "items": {"type": "string"}},
                "expected_impact": {"type": "string"},
                "project_id": {"type": "string"},
                "venture_id": {"type": "string"},
            },
            "required": ["decision"],
        },
    },
    {
        "name": "save_work_session",
        "description": (
            "Record a work session verbatim, without extraction or downstream record "
            "creation. Use finalize_work_session for the full workflow."
        ),
        "required_scope": SCOPE_SESSIONS_WRITE,
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "detailed_notes": {"type": "string"},
                "project_id": {"type": "string"},
                "venture_id": {"type": "string"},
                "person_id": {"type": "string"},
                "key_takeaways": {"type": "array", "items": {"type": "string"}},
                "next_actions": {"type": "array", "items": {"type": "string"}},
                "client_request_id": {"type": "string"},
                "provider": {"type": "string"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "finalize_work_session",
        "description": (
            "Finalize an AI work session: extract objective, research, findings, decisions "
            "with rationale and rejected alternatives, tasks, people, organizations, "
            "commitments, evidence, artifacts, skills and open questions, then persist them "
            "with provenance in one transaction. Replays are idempotent."
        ),
        "required_scope": SCOPE_SESSIONS_WRITE,
        "additional_scopes": list(FINALIZE_REQUIRED_SCOPES),
        "write": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "default": "mcp_client"},
                "session_reference": {"type": "string"},
                "client_request_id": {"type": "string"},
                "summary": {"type": "string"},
                "session_payload": {"type": "object"},
                "venture": {"type": "string"},
                "project": {"type": "string"},
                "title": {"type": "string"},
            },
        },
    },
]

MCP_ALL_TOOLS: List[Dict[str, Any]] = MCP_TOOLS_MANIFEST + MCP_WRITE_TOOLS_MANIFEST


@router.get("", summary="MCP Server Capabilities & Protocol Info")
async def mcp_server_info():
    return {
        "status": "online",
        "mcp_version": "1.0",
        "server_name": "Taj's Second Brain MCP Streamable HTTP Server",
        "transport": "Streamable HTTP (ASGI mounted at /mcp)",
        "available_tools_count": len(MCP_ALL_TOOLS),
        "registered_tools": [t["name"] for t in MCP_ALL_TOOLS],
        "write_tools_status": "EXPOSED_SCOPE_ENFORCED",
        "write_tools": [t["name"] for t in MCP_WRITE_TOOLS_MANIFEST],
        "write_scopes_required": sorted(
            {str(t["required_scope"]) for t in MCP_WRITE_TOOLS_MANIFEST}
        ),
        "docs": "/api/docs#tag/MCP-Streamable-HTTP-Server",
    }


@router.get("/tools", summary="List Available MCP Tools & Schemas")
async def list_mcp_tools():
    return {"tools": MCP_ALL_TOOLS}


def _required_arg(args: Dict[str, Any], name: str) -> Any:
    value = args.get(name)
    if value in (None, ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required argument '{name}'.",
        )
    return value


def _allowed_arguments(tool_spec: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    """Only declared schema properties reach the domain layer; unknown keys are dropped."""
    properties = tool_spec.get("input_schema", {}).get("properties", {})
    return {k: v for k, v in args.items() if k in properties}


async def _invoke_write_tool(
    tool: str,
    args: Dict[str, Any],
    sec_ctx: Any,
    tool_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a mutating tool as one owner-scoped transaction: BEGIN on the first statement,
    COMMIT once on success, ROLLBACK on any failure.

    For finalize_work_session the extraction step runs before the session is opened, so
    model inference never holds a database connection or locks.
    """
    call_args = _allowed_arguments(tool_spec, args)

    if tool == "finalize_work_session":
        extracted = await extract_session_intelligence(
            summary=call_args.get("summary"),
            session_payload=call_args.get("session_payload"),
            provider=call_args.get("provider"),
        )
        venture_hint = call_args.pop("venture", None)
        project_hint = call_args.pop("project", None)
        call_args = {
            **extracted["fields"],
            **call_args,
            "venture_hint": venture_hint,
            "project_hint": project_hint,
            "extraction": extracted["extraction"],
        }
    elif tool in {"create_task", "create_project", "save_work_session"}:
        _required_arg(args, "title" if tool != "create_project" else "name")
    elif tool in {"update_task", "complete_task"}:
        _required_arg(args, "task_id")
    elif tool == "update_person":
        _required_arg(args, "person_id")
    elif tool == "update_project":
        _required_arg(args, "project_id")
    elif tool == "create_person":
        _required_arg(args, "name")
    elif tool == "save_memory":
        _required_arg(args, "title")
        _required_arg(args, "content")
    elif tool == "save_decision":
        _required_arg(args, "decision")

    async with rls_db_session(sec_ctx.user_id) as db:
        domain = MCPDomainTools(db=db, user_id=sec_ctx.user_id)
        handler = getattr(domain, tool, None)
        if handler is None:
            raise HTTPException(status_code=404, detail="Tool logic not bound.")
        try:
            result = await handler(**call_args)
        except HTTPException:
            await db.rollback()
            raise
        except Exception as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MCP write tool '{tool}' failed: {exc}",
            ) from exc
        await db.commit()

    return {
        "status": "success",
        "tool": tool,
        "result": result,
        "security_context": {
            "client_name": sec_ctx.client_name,
            "scope_enforced": tool_spec["required_scope"],
            "write": True,
        },
    }


@router.post("/tools/invoke", summary="Execute Authenticated MCP Tool Call")
async def invoke_mcp_tool(
    payload: MCPToolInvocation,
    x_mcp_api_key: Optional[str] = Header(None, alias="X-MCP-API-KEY"),
    authorization: Optional[str] = Header(None),
):
    api_key = x_mcp_api_key or authorization
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-MCP-API-KEY header.",
        )

    # Find tool spec
    tool_spec = next((t for t in MCP_ALL_TOOLS if t["name"] == payload.tool), None)
    if not tool_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Tool '{payload.tool}' is not registered on this server.",
        )

    # Credential verification scans every profile for a matching key prefix, so it is a
    # system operation and must run in the privileged admin context, not under RLS claims.
    async with admin_db_session(reason="mcp_api_key_verification") as admin_db:
        sec_ctx = await authorize_mcp_request(
            db=admin_db,
            api_key=api_key,
            required_scope=str(tool_spec["required_scope"]),
            tool_name=payload.tool,
            arguments=payload.arguments,
        )
        await admin_db.commit()

    # finalize_work_session spans five domains, so every one of their write scopes must be
    # granted before it can run.
    for extra_scope in tool_spec.get("additional_scopes", []):
        try:
            verify_scope(sec_ctx.granted_scopes, str(extra_scope))
        except MCPScopeError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"MCP credential lacks required capability scope '{extra_scope}'. "
                    f"Granted: {sec_ctx.granted_scopes}"
                ),
            ) from exc

    args = payload.arguments or {}
    result: Any = None

    if tool_spec.get("write"):
        return await _invoke_write_tool(payload.tool, args, sec_ctx, tool_spec)

    # Tool execution runs under the resolved owner's transaction-local claims, so the same
    # RLS tenant boundary applies to MCP reads as to REST requests.
    async with rls_db_session(sec_ctx.user_id) as db:
        domain = MCPDomainTools(db=db, user_id=sec_ctx.user_id)

        if payload.tool == "search_people":
            result = await domain.search_people(query=args.get("query"), limit=args.get("limit", 20))
        elif payload.tool == "search_memory":
            result = await domain.search_memory(
                query=args.get("query"), category=args.get("category"), limit=args.get("limit", 20)
            )
        elif payload.tool == "get_projects":
            result = await domain.get_projects(
                status=args.get("status"), limit=args.get("limit", 20)
            )
        elif payload.tool == "get_tasks":
            result = await domain.get_tasks(status=args.get("status"), limit=args.get("limit", 20))
        elif payload.tool == "get_relationship_history":
            person_id = args.get("person_id")
            if not person_id:
                raise HTTPException(status_code=400, detail="Missing required argument 'person_id'")
            result = await domain.get_relationship_history(
                person_id=person_id, limit=args.get("limit", 20)
            )
        elif payload.tool == "get_calendar":
            result = await domain.get_calendar(limit=args.get("limit", 20))
        elif payload.tool == "generate_linkedin_post":
            topic = args.get("topic")
            if not topic:
                raise HTTPException(status_code=400, detail="Missing required argument 'topic'")
            result = await domain.generate_linkedin_post(
                topic=topic, style_tone=args.get("style_tone", "executive")
            )
        elif payload.tool == "generate_case_study":
            project_name = args.get("project_name")
            if not project_name:
                raise HTTPException(
                    status_code=400, detail="Missing required argument 'project_name'"
                )
            result = await domain.generate_case_study(project_name=project_name)
        elif payload.tool == "generate_weekly_review":
            result = await domain.generate_weekly_review()
        else:
            raise HTTPException(status_code=404, detail="Tool logic not bound.")

    return {
        "status": "success",
        "tool": payload.tool,
        "result": result,
        "security_context": {
            "client_name": sec_ctx.client_name,
            "scope_enforced": tool_spec["required_scope"],
        },
    }
