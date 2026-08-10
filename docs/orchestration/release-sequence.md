# Master Release Sequence & Phase Transformation Plan - Taj's Second Brain

Version: 1.0  
Author: Agent 0 — Lead Orchestrator  
Status: Authoritative Release Roadmap  

---

## 1. Release Progression Overview

To ensure zero-regression integration, Taj's Second Brain follows a rigid 8-phase transformation plan. Each phase must be explicitly reviewed against its **Integration Gate** in `docs/orchestration/integration-gates.md` and signed off by Agent 0 before transitioning to subsequent phases.

```text
+-------------------------------------------------------------------------+
| Phase 0: System Architecture & Orchestration Alignment (Agent 0, 1)     | <-- [CURRENT PHASE]
+-------------------------------------------------------------------------+
                                    | (Requires Gate 0 Signoff & ADR-013 Audit)
                                    v
+-------------------------------------------------------------------------+
| Phase 1: Database & Foundation Layer Transformation (Agent 2, 3, 4)     |
+-------------------------------------------------------------------------+
                                    | (Requires Gate 1 & 2 Signoff; Resolve BLK-002)
                                    v
+-------------------------------------------------------------------------+
| Phase 2: Core Execution & Founder Dashboard Integration (Agent 5)       |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Phase 3: Relationship CRM & Memory Network Integration (Agent 6)        |
+-------------------------------------------------------------------------+
                                    | (Requires Gate 2 Reconciliation; Resolve BLK-003)
                                    v
+-------------------------------------------------------------------------+
| Phase 4: Knowledge Export & Cloud Backup Automation (Agent 7)         |
+-------------------------------------------------------------------------+
                                    | (Requires Ephemeral Filesystem Verification)
                                    v
+-------------------------------------------------------------------------+
| Phase 5: RAG Pipeline & Semantic Intelligence Integration (Agent 8)      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Phase 6: Idea Vault, KPIs, Portfolio & AI Content Engine (Agent 9)      |
+-------------------------------------------------------------------------+
                                    | (Requires Shared Repository Readiness)
                                    v
+-------------------------------------------------------------------------+
| Phase 7: Single Render Web Service & MCP Integration (Agent 10, 11)     | <-- [RESOLVES BLK-001]
+-------------------------------------------------------------------------+
                                    | (Requires Gate 4 Signoff: /mcp Mount over ASGI)
                                    v
+-------------------------------------------------------------------------+
| Phase 8: E2E QA Certification & System Production Handoff (Agent 12, 13) |
+-------------------------------------------------------------------------+
```

---

## 2. Phase Execution Specifications

### Phase 0: System Architecture & Orchestration Alignment (Current Status)
- **Active Agents:** Agent 0 (Lead Orchestrator), Agent 1 (Architecture & Contracts)
- **Key Objectives:** Establish multi-agent governance, define single-service Render deployment rules (ADR-013), document ownership boundaries, and identify codebase implementation gaps.
- **Exit Verification:** Approval of all files in `docs/orchestration/` and readiness handoff for Agent 1.

### Phase 1: Database & Foundation Layer Transformation
- **Active Agents:** Agent 2 (Database/RLS), Agent 3 (FastAPI Backend Foundation), Agent 4 (Frontend Foundation)
- **Key Objectives:** Apply all Supabase PostgreSQL schemas, certify 100% RLS coverage, unify duplicate frontend directory roots (`src/` vs `apps/web/`), and verify OAuth/JWT cryptographic Bearer middleware.
- **Exit Verification:** Clean test runs for database schemas, backend core auth tests, and Next.js foundation builds.

### Phase 2 & 3: Founder Dashboard, CRM & Memory Integration
- **Active Agents:** Agent 5 (Dashboard & Execution), Agent 6 (CRM & Memory System)
- **Key Objectives:** Deliver ventures, projects, tasks, contact graph interfaces, interaction logs, and meeting transcription analysis. Integrate legacy router logic into canonical OpenAPI endpoints.
- **Exit Verification:** Full functional behavior verified via frontend UI components and backend repository unit tests.

### Phase 4 & 5: Export Synchronization & Semantic RAG Pipeline
- **Active Agents:** Agent 7 (Export/GDrive/GCal Sync), Agent 8 (RAG & Semantic Search)
- **Key Objectives:** Implement background async jobs for converting PostgreSQL records to YAML-frontmatter Markdown archives, execute Google Drive encrypted OAuth token sync, and operationalize hybrid search (`pgvector` cosine similarity + trigram FTS).
- **Exit Verification:** Confirm zero dependency on local disk persistence across container restarts; verify RRF retrieval relevancy scores.

### Phase 6 & 7: AI Content Engine & Single Render Service MCP Consolidation
- **Active Agents:** Agent 9 (Content/KPIs/Portfolio), Agent 10 (Secure MCP Server), Agent 11 (Security/DevOps)
- **Key Objectives:** Implement content generation grounded in RAG retrieval. **Execute ADR-013 runtime consolidation:** Refactor standalone `apps/mcp-server` to mount as a Streamable HTTP ASGI app inside `apps/api/app/main.py` at `/mcp`, sharing domain repositories without violating security or rate-limiting boundaries.
- **Exit Verification:** Verify single container start command boots both REST and `/mcp` endpoints; perform penetration test on MCP token scope controls and rate limiters.

### Phase 8: E2E Quality Certification & Production Handoff
- **Active Agents:** Agent 12 (E2E QA), Agent 13 (Documentation)
- **Key Objectives:** Execute comprehensive Playwright tests across web UI flows and automated API test suites against deployed staging endpoints. Produce final walkthrough and disaster recovery runbooks.
- **Exit Verification:** Zero defect severity blockers remaining in defect log; complete user handover report delivered.
