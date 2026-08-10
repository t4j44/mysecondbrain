# External AI Client Integration & Setup Guide

This guide walks through configuring external AI assistants to safely query Taj's Second Brain using the standalone MCP server (`apps/mcp-server`).

## 1. Generate an MCP API Key
Using the FastAPI backend endpoint or founder administration terminal, create a secure salted SHA-256 API key:
```bash
curl -X POST "http://localhost:8000/api/v1/mcp/credentials" \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Desktop",
    "client_type": "stdio",
    "scopes": ["mcp:read", "mcp:content:draft", "mcp:case_study:draft"]
  }'
```
*Note your plaintext key starting with `sb_mcp_...`—it is displayed only once upon generation.*

---

## 2. Claude Desktop Integration (Stdio Transport)
To integrate with Anthropic's Claude Desktop application on Windows, modify your `claude_desktop_config.json` file located at `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "taj-second-brain": {
      "command": "python",
      "args": [
        "-m",
        "app.main",
        "--transport",
        "stdio"
      ],
      "cwd": "E:/second brain/apps/mcp-server",
      "env": {
        "X_MCP_API_KEY": "sb_mcp_your_generated_secret_here",
        "DATABASE_URL": "sqlite+aiosqlite:///../../local_second_brain.db",
        "APP_ENV": "development"
      }
    }
  }
}
```

---

## 3. Claude Code CLI Integration
When operating via Claude Code in your terminal workspace, configure the local project server binding:

```bash
# Register via local project configuration or environment variable export
export X_MCP_API_KEY="sb_mcp_your_generated_secret_here"
claude mcp add taj-second-brain -- python -m app.main --transport stdio
```

---

## 4. Gemini CLI & Custom Assistants (SSE Transport)
For web-based or SSE (Server-Sent Events) compatible desktop clients including custom Google Gemini integrations or OpenAI custom actions, launch the HTTP SSE transport daemon:

```bash
cd "E:/second brain/apps/mcp-server"
python -m app.main --transport sse --host 127.0.0.1 --port 8001
```

Configure your SSE connecting client with the target endpoint and API header:
* **Server URL**: `http://127.0.0.1:8001/sse`
* **Authentication Header**: `X-MCP-API-KEY: sb_mcp_your_generated_secret_here`
