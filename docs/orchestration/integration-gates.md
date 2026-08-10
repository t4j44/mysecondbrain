# Master Integration Gates - Taj's Second Brain

Version: 1.0  
Author: Agent 0 — Lead Orchestrator  
Status: Authoritative Verification Gates  

Before any phase transformation or specialist agent handoff is marked approved, the system must pass all relevant Quality Integration Gates defined below. No specialist agent may bypass a gate or alter tests to artificially achieve compliance.

---

## 1. Gate Definitions & Criteria

### Gate 0: Architecture & Orchestration Readiness Gate
- **Target:** Agent 0 & Agent 1
- **Criteria:**
  - [x] PRD, TRD, and 14-Agent Sequence fully analyzed and reconciled against implementation codebase.
  - [x] ADR-013 (Single Render Web Service for FastAPI and MCP) drafted and approved in `docs/architecture/architecture_decisions.md`.
  - [x] All orchestration tracking documents live in `docs/orchestration/` (`agent-ownership.md`, `dependency-map.md`, `decision-log.md`, `blocker-log.md`, `integration-gates.md`, `release-sequence.md`).
  - [x] Repository audit completed; discrepancies between planned scripts and genuine functional files documented.
- **Status:** **PASSED / COMPLETED BY AGENT 0**

---

### Gate 1: Database & Persistence Gate
- **Target:** Agent 2
- **Criteria:**
  - [ ] All tables created in `supabase/migrations/` match the canonical data schema (`database_schema.md`).
  - [ ] Row Level Security (RLS) is explicitly enabled on 100% of tables with zero public access bypasses.
  - [ ] `pgvector` extension is active with an index (IVFFlat/HNSW) on `public.memory_embeddings`.
  - [ ] Database automated tests (`pg_prove` or pytest DB seeding suites) pass cleanly without schema syntax errors.
- **Status:** **PENDING / REQUIRES AGENT 2 FORMAL VERIFICATION**

---

### Gate 2: REST Backend Services Gate
- **Target:** Agent 3 & Agent 6
- **Criteria:**
  - [ ] All OpenAPI endpoint routes match `api_contracts.md` specifications.
  - [ ] JWT Bearer authentication dependency natively checks signature validities without trusting client-side `user_id` payload claims.
  - [ ] Exception handlers return RFC 7807 problem details or standardized error schemas without exposing Python stack traces.
  - [ ] Dead/unused routing structures in `app/routers/` resolved or fully covered by automated unit tests in pytest.
- **Status:** **PENDING / IN PROGRESS (58 existing backend tests pass; CRM routers need reconciliation)**

---

### Gate 3: UI Frontend Shell & Component Gate
- **Target:** Agent 4 & Group B/C Dashboard Agents (5, 6, 7, 9)
- **Criteria:**
  - [ ] Duplicate root frontend prototype (`src/`) resolved; `apps/web/` designated as the sole canonical frontend application space.
  - [ ] `@supabase/ssr` correctly handles cookie sessions with HTTP-only SameSite flags.
  - [ ] UI layouts match design aesthetic standards (modern dark mode, smooth transitions, no broken layout shifts).
  - [ ] TypeScript build (`pnpm --filter web build`) completes with zero type errors or unresolved module dependencies.
- **Status:** **PENDING / BLOCKED ON FRONTEND CODEBASE CONSOLIDATION (BLK-002)**

---

### Gate 4: Single Render Service & MCP Integration Gate (ADR-013)
- **Target:** Agent 3 & Agent 10
- **Criteria:**
  - [ ] Standalone `apps/mcp-server/` web deployment removed or integrated into `apps/api/`.
  - [ ] Agent 10 mounts the Streamable HTTP MCP server inside `apps/api/app/main.py` via `app.mount("/mcp", mcp_app)`.
  - [ ] Both FastAPI endpoints and MCP tool executions invoke identical shared domain service repositories without duplicating business logic or running raw untyped SQL.
  - [ ] REST API and MCP server preserve strictly separate authentication, authorization scopes, rate limits, and audit logs.
- **Status:** **BLOCKED / CRITICAL REWORK REQUIRED IN AGENT 10 (BLK-001)**

---

### Gate 5: Security, Production Readiness & QA Signoff Gate
- **Target:** Agent 11, Agent 12 & Agent 13
- **Criteria:**
  - [ ] Bandit, Ruff, and OWASP dependency security audits complete with zero high-severity vulnerabilities reported.
  - [ ] Ephemeral filesystem rules verified: all persistent state writes direct to Supabase PostgreSQL, Supabase Storage, or Google Drive cloud backups.
  - [ ] Automated E2E test scripts run across key user flows (capturing thoughts, searching memories, drafting LinkedIn content, generating weekly reviews).
  - [ ] Handover walkthrough documentation complete and verified against live deployed endpoints.
- **Status:** **SCHEDULED FOR PHASE 7 & 8**
