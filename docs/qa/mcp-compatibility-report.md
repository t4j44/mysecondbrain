# Model Context Protocol (MCP) Compatibility Report

**Server Implementation:** FastMCP SDK (`apps/api/mcp_server.py`)  
**Transport Protocol:** Server-Sent Events (SSE) & Stdio  
**Target Clients:** Claude Desktop, ChatGPT Custom GPTs, Gemini CLI  

---

## 1. Tool & Resource Compatibility Audit

| MCP Tool Name | Description | Required Scope | Auth Enforcement | Test Result |
|---|---|---|---|---|
| `search_people` | Search CRM contacts by name, organization, or tag | `read:crm` | Bearer Token / API Key | PASSED (`test_mcp_tools.py`) |
| `search_memory` | Vector RAG query over long-term memories | `read:memories` | Bearer Token / API Key | PASSED (`test_mcp_tools.py`) |
| `get_projects` | List active founder projects and milestones | `read:ventures` | Bearer Token / API Key | PASSED (`test_mcp_tools.py`) |
| `get_tasks` | Fetch pending tasks filtered by status/priority | `read:tasks` | Bearer Token / API Key | PASSED (`test_mcp_tools.py`) |
| `generate_linkedin_post` | AI content generator using founder experiences | `write:content` | Bearer Token / API Key | PASSED (`test_mcp_tools.py`) |

---

## 2. Security & Scope Enforcement

- **Token Revocation & Expiry**: Tested `POST /api/v1/mcp/tokens/revoke`. Revoked tokens return `HTTP 401 Unauthorized` immediately across all MCP transports (`test_mcp_auth.py`).
- **Scope Scoping**: Calling `generate_linkedin_post` using a token restricted to `read:crm` scope returns `HTTP 403 Forbidden` (`test_mcp_auth.py`).
- **Prompt Injection Defense**: Untrusted arguments passed to MCP tools are sanitized prior to database or LLM invocation.
