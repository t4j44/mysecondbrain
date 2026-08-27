"""
FastAPI Router for Streamable HTTP Model Context Protocol (MCP) Server Endpoint mounted at /mcp.
Module Owner: Agent 10 & Agent 3 — ADR-013 Single Render Service Architecture
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.dependencies.database import admin_db_session, rls_db_session
from app.mcp.security import (
    SCOPE_CALENDAR_READ,
    SCOPE_CONTENT_DRAFT,
    SCOPE_MEMORY_READ,
    SCOPE_PEOPLE_READ,
    SCOPE_PROJECTS_READ,
    SCOPE_RELATIONSHIPS_READ,
    SCOPE_TASKS_READ,
    authorize_mcp_request,
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


# Write / mutate tools exist on MCPDomainTools but are intentionally NOT registered
# on the MCP server or REST invoke manifest (G0). Prompt 5 owns safe exposure.
MCP_WRITE_TOOLS_IMPLEMENTED_NOT_EXPOSED: List[str] = [
    "save_memory",
    "create_task",
    "update_task",
    "complete_task",
    "create_person",
    "update_person",
    "create_project",
    "update_project",
    "save_decision",
    "save_work_session",
    "finalize_work_session",
]


@router.get("", summary="MCP Server Capabilities & Protocol Info")
async def mcp_server_info():
    return {
        "status": "online",
        "mcp_version": "1.0",
        "server_name": "Taj's Second Brain MCP Streamable HTTP Server",
        "transport": "Streamable HTTP (ASGI mounted at /mcp)",
        "available_tools_count": len(MCP_TOOLS_MANIFEST),
        "registered_tools": [t["name"] for t in MCP_TOOLS_MANIFEST],
        "write_tools_status": "IMPLEMENTED_IN_CODE_NOT_EXPOSED",
        "write_tools_not_exposed": list(MCP_WRITE_TOOLS_IMPLEMENTED_NOT_EXPOSED),
        "docs": "/api/docs#tag/MCP-Streamable-HTTP-Server",
    }


@router.get("/tools", summary="List Available MCP Tools & Schemas")
async def list_mcp_tools():
    return {"tools": MCP_TOOLS_MANIFEST}


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
    tool_spec = next((t for t in MCP_TOOLS_MANIFEST if t["name"] == payload.tool), None)
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

    args = payload.arguments or {}
    result: Any = None

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
