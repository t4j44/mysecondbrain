# Model Context Protocol (MCP) Server Architecture - Taj's Second Brain

Version: 1.0  
Status: Approved & Implementation-Ready  
Author: Agent 1 — Architecture and Contracts Agent  
Approved by: Agent 0 — Lead Orchestrator  

---

## 1. MCP Architecture Overview

The Model Context Protocol (MCP) layer turns Taj's Second Brain from a closed web application into an open, secure personal memory infrastructure. By deploying a standalone Python MCP Server (`apps/mcp-server/`), external desktop AI clients—including **Claude Desktop, ChatGPT, Claude Code, and Gemini CLI**—can connect to Taj’s historical founder knowledge base to receive rich context during external coding, drafting, or business research sessions.

---

## 2. Server Topology & Access Strategy

```
+-------------------------------------------------------------------------------------------------+
|                                    EXTERNAL AI CLIENT APIS                                      |
|              Claude Desktop Client, ChatGPT MCP Plugin, Claude Code CLI, Gemini CLI             |
+-------------------------------------------------------------------------------------------------+
                                                │
                 JSON-RPC over STDIO / SSE (Header: `X-MCP-API-KEY: <secret_token>`)
                                                │
                                                ▼
+-------------------------------------------------------------------------------------------------+
|                                     MCP SERVER APPLICATION                                      |
|                          Python MCP SDK Server (`apps/mcp-server/`)                            |
|                                                                                                 |
|  +--------------------+  +-----------------------+  +----------------------------------------+  |
|  | AUTH & TOKEN GATE  |  |    TOOL REGISTRATION  |  |           SECURITY ENFORCING           |  |
|  | Verify X-MCP-KEY   |  | 9 Eager & Lazy Tools  |  | Default Read-Only / Staged Mutation UI |  |
|  +--------------------+  +-----------------------+  +----------------------------------------+  |
+-------------------------------------------------------------------------------------------------+
                                                │
        Calls explicit internal Domain Service Repositories (`packages/database` & Service APIs)
                                                │
                                                ▼
+-------------------------------------------------------------------------------------------------+
|                       SHARED BACKEND SERVICES & SQL DATABASE LAYER                              |
|       PostgreSQL RLS Verification -> Canonical Tables -> Vector Search (pgvector)               |
+-------------------------------------------------------------------------------------------------+
```

### Why MCP Accesses Shared Services (Not Direct Raw DB Queries)
To ensure system stability, **the MCP Server is strictly prohibited from executing raw untyped SQL query strings directly against PostgreSQL tables.** Instead, the MCP server imports and invokes the exact same shared Domain Service and Repository layer classes (`backend.app.services.*` / `packages.database`) used by the FastAPI web service.
- **Benefits:** Ensures complete consistency in data validation, guaranteed execution of Row Level Security (RLS) scoping filters (`user_id == authenticated_mcp_user`), unified audit logging, and consistent error handling across both Web UI users and external AI assistants.

---

## 3. Security, Authentication, & Authorization Engineering

1. **Authentication Protocol:**
   - External clients connecting via Stdio or SSE must provide an explicit authentication API key (`X-MCP-API-KEY` or Bearer token) configured within the client terminal configuration (`claude_desktop_config.json` / OpenAI MCP tool config).
   - The MCP Server verifies this key against the encrypted user access token repository in `public.profiles.settings`. Unauthenticated or invalid token attempts are immediately dropped with JSON-RPC error `-32001 (Unauthorized)`.
2. **Default Read-Only Authorization Policy:**
   - By default, all MCP tools execute under **Strict Read-Only Access**. Tools designed for memory retrieval (`search_memory`, `get_projects`, `search_people`) are permitted to read databases under verified user RLS scoping.
   - **Write & Mutation Controls:** Tools designed to draft content or manipulate records (`generate_linkedin_post`, `create_task`) do not immediately mutate live canonical production tables or publish posts to the internet. Instead, they output structured markdown draft schemas to the external AI chat window or stage an unapproved draft record in PostgreSQL requiring explicit human confirmation inside the Next.js Founder Dashboard before execution.
3. **Rate Limiting & Abuse Defense:**
   - MCP tool invocations are rate-limited via an in-memory sliding window or Supabase Redis layer to **60 requests per minute per authenticated access token**. Excessive polling from misbehaving AI agents is halted with HTTP 429 / JSON-RPC rate limit alerts.
4. **Audit Logging & Revocation:**
   - Every MCP tool call is permanently recorded in `public.audit_logs` with explicit operational origin tagging (`source: "mcp_server"`, `tool_name`, `execution_duration_ms`, `tokens_consumed`).
   - If an external desktop laptop or client key is compromised, the founder can instantly revoke MCP access with a single click in the UI (`/settings/integrations`), immediately invalidating the key across all active MCP servers without affecting web session cookies.

---

## 4. Comprehensive MCP Tool Specifications (All 9 Required Tools)

The MCP Server exposes the following 9 formalized tool contracts to connected LLM assistants:

| Tool Identifier | Purpose & Domain Utility | Required & Optional Arguments | Output Response Format | Safety Level |
|---|---|---|---|---|
| `search_people` | Queries the Founder CRM for professional contacts, mentors, and investors matching name, company, or expertise tags. | `query` (string, required)<br>`relationship_type` (string, optional: mentor/investor/peer)<br>`limit` (int, default: 5) | Array of CRM contact profile JSON objects including company, location, and key interaction notes. | Read-Only |
| `search_memory` | Performs RAG hybrid vector + keyword search across all stored notes, decisions, meeting transcripts, and ideas. | `query` (string, required)<br>`top_k` (int, default: 5)<br>`similarity_threshold` (float, default: 0.55) | Array of matched conversational memory snippets with cosine similarity scores and clickable entity citation URLs. | Read-Only |
| `get_projects` | Retrieves active startup projects, target execution milestones, and progress summaries across ventures. | `venture_slug` (string, optional: justor-ai / zqtion / iexf / cmoos)<br>`status` (string, default: in_progress) | Array of Project objects with completion percentage, target dates, and task count summaries. | Read-Only |
| `get_tasks` | Fetches open tasks, prioritized action items, and deadlines scheduled for today or upcoming sprints. | `status` (string, default: todo)<br>`priority` (string, optional: low/medium/high/urgent)<br>`venture_id` (string UUID, optional) | Array of Task items sorted by urgent priority and chronological due date. | Read-Only |
| `get_calendar` | Reads scheduled founder meetings, events, and task deadlines from the synchronized schedule view. | `days_ahead` (int, default: 7, max: 30) | Array of CalendarEvent items with start/end timestamps, meeting locations, and associated project tags. | Read-Only |
| `get_relationship_history` | Reconstructs the complete historical interaction timeline and advice archive for a specific CRM contact. | `person_id` (string UUID, required) | Comprehensive JSON document containing person profile attributes, chronological interaction summaries, and action items. | Read-Only |
| `generate_linkedin_post` | Synthesizes an authentic LinkedIn social media post utilizing Taj's documented startup learnings and editorial tone. | `topic` (string, required)<br>`target_audience` (string, default: "Founders & AI PMs")<br>`include_achievements` (bool, default: true) | Markdown string containing formatted social post draft, suggested hashtags, and citation proof references. | Draft Only (No Internet Post) |
| `generate_case_study` | Compiles a professional career proof portfolio case study based on stored achievements and project execution history. | `achievement_id` (string UUID, required)<br>`target_role` (string, optional: "AI Product Manager" / "Founder") | Structured Markdown document detailing Problem, Responsibilities, AI Workflow Design, Impact, and Demonstrated Skills. | Read / Draft |
| `generate_weekly_review` | Evaluates past week performance metrics, completed tasks, meaningful CRM connections, and learning KPIs. | `week_offset_zero` (bool, default: true) | Structured reflection review identifying execution triumphs, strategic bottlenecks, and guidance for next week. | Read / Draft |

---

## 5. Client Setup Documentation Blueprint (For Founder Reference)

To connect Claude Desktop to Taj's Second Brain, add the following configuration block into your system `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "taj-second-brain": {
      "command": "python",
      "args": [
        "-m",
        "apps.mcp_server.main",
        "--transport",
        "stdio"
      ],
      "env": {
        "MCP_API_KEY": "sb_mcp_secret_key_xxxxxxxxx",
        "API_BASE_URL": "https://api.tajssecondbrain.ai/api/v1"
      }
    }
  }
}
```

When connecting over remote HTTP Server-Sent Events (SSE) from external cloud clients (e.g., ChatGPT plugins or distributed agents):
- **Endpoint URL:** `https://mcp.tajssecondbrain.ai/sse`
- **Required HTTP Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <sb_access_jwt>` or `X-MCP-API-KEY: <mcp_token>`
