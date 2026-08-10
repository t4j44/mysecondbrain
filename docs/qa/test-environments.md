# Test Environments & Infrastructure Verification

**Target Release:** v1.0.0-RC1  
**Environment Tier:** Local Integration & Automated CI Pipeline  

---

## 1. Environment Configuration Matrix

| Component | Technology / Runtime | Local Port / Host | Test Config / Mock Status |
|---|---|---|---|
| **Frontend Web App** | Next.js 14 App Router, React 18, Tailwind | `localhost:3000` | Isolated JS DOM test environment, Vitest runner |
| **Backend API Microservice** | FastAPI, Uvicorn, Python 3.11 | `localhost:8000` | SQLite in-memory / Local Postgres test runner |
| **Database & Vector Store** | PostgreSQL 15 + `pgvector`, Supabase CLI | `localhost:54322` | Migration suite 00001-00016 applied |
| **AI LLM Provider** | Gemini 1.5 Pro / Flash | External REST API | `MockGeminiClient` fixture in automated tests |
| **Google Drive / Calendar** | Google OAuth2 & REST APIs | External REST API | `MockGoogleClient` fixture in automated tests |
| **MCP Server** | FastMCP SDK (Python) | `localhost:8000/mcp` / SSE | SSE transport test harness |

---

## 2. Environment Verification & Clean Installation Standard Operating Procedure

1. **Clean Installation Verification**:
   ```bash
   git clean -fdx
   npm install --frozen-lockfile
   cd apps/api && python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt
   ```
2. **Database Migration & Seeding**:
   ```bash
   supabase db reset --linked=false
   pytest tests/test_auth_security.py
   ```
3. **Environment Security Scans**:
   - Zero hardcoded production secrets in `.env.example` or repository root.
   - All JWT signing keys and OAuth client secrets populated via environment variable injection.
