# Master Development Roadmap & Multi-Agent Orchestration Plan - Taj's Second Brain

Version: 2.0 (Comprehensive Phased Orchestration Schedule)  
Author: Agent 1 — Architecture and Contracts Agent  
Approved by: Agent 0 — Lead Orchestrator  
Target Architecture: Next.js App Router, Python FastAPI, Supabase PostgreSQL / RLS / pgvector, Gemini API, Python MCP Server

---

## 1. Executive Orchestration Roadmap Overview

To transform the approved PRD/TRD into a functional, highly secure Founder Operating System without schema drift or integration friction, development is divided into **Eight Explicit Execution Phases (Phase 0 through Phase 7)**. This roadmap serves as the absolute operational contract for **Agent 0 — Lead Orchestrator** to delegate autonomous tasks, enforce directory ownership boundaries, manage parallel development groups, and validate mandatory quality and security gates before authorizing phase transitions.

---

## 2. Comprehensive Phase-by-Phase Implementation Plan

### Phase 0: Architecture & Shared Contracts (CURRENT PHASE - COMPLETED)
- **Objective:** Establish implementation-ready blueprints, database schemas, REST/MCP API contracts, cybersecurity threat models, architecture decision records (ADRs), and strict multi-agent file ownership boundaries prior to executing application feature code.
- **Deliverables:**
  - `Tajs_Second_Brain_PRD_TRD.md` (Validated baseline requirements)
  - `implementation_plan.md` (Master architecture & component interaction design)
  - `database_schema.md` (Authoritative SQL specifications for 31+ tables and pgvector similarity engines)
  - `api_contracts.md` (RESTful JSON endpoints, SSE Vercel streaming syntax, and MCP tool signatures)
  - `security_and_privacy_plan.md` (15 threat models, RLS invariants, key isolation, and prompt injection defenses)
  - `development_roadmap.md` (Phased multi-agent orchestration schedule)
  - Supporting Docs (`docs/architecture/*.md` including ADRs 001 to 012, system workflows, auth sequences, and RAG pipelines)
- **Assigned Agents:** Agent 0 — Lead Orchestrator, Agent 1 — Architecture and Contracts Agent.
- **Owned Paths:** `/*.md`, `docs/**`.
- **Dependencies:** None. | **Parallel Tasks:** None (Foundation serialization).
- **Acceptance Criteria:** Every PRD module is architected; all 31 tables define explicit user ownership paths; every frontend feature possesses a versioned REST endpoint; AI responses incorporate citation support; MCP tools define read-only default constraints.
- **Required Tests:** Static Markdown review and verification of schema relationship consistency.
- **Security Gate:** Verification that no client-controlled user IDs appear in API contracts and all tables require RLS.
- **Exit Criteria:** Agent 0 reviews and explicitly approves architecture documents; zero unresolved critical contract conflicts remain. Transitioning authorized to Parallel Group A (Phase 1).

---

### Phase 1: Core Foundation & Dashboard (Weeks 1-2)
- **Objective:** Provision the multi-language monorepo workspace, deploy Supabase PostgreSQL migrations and Auth middleware, establish FastAPI application skeletons, configure Next.js App Router terminal design systems, and build the live Founder Dashboard command center with ventures, projects, and task execution workflows.
- **Deliverables:**
  - Complete monorepo build tools (`pnpm-workspace.yaml`, Python UV environments, ESLint/Ruff linter setups).
  - Supabase PostgreSQL SQL migration scripts (`supabase/migrations/001_initial_schema.sql`, RLS policies, vector extension setup).
  - FastAPI web server runtime (`apps/api/main.py`, Supabase Auth Bearer JWT dependency `get_current_user`, Pydantic validation schemas).
  - Next.js Retro-Futuristic Terminal application shell (`apps/web/app/(auth)/*`, `apps/web/app/(dashboard)/*`, Shadcn UI styling).
  - UI Workspaces & API Endpoints for Dashboard summary, Venture Management, Project Pipelines, and interactive Task boards (`/dashboard`, `/ventures`, `/projects`, `/tasks`).
- **Assigned Agents:** 
  - **Group A:** Database Agent, Backend Foundation Agent, Frontend Foundation Agent.
  - **Group B:** Dashboard and Execution Agent.
- **Owned Paths:**
  - Database Agent: `supabase/migrations/**`, `supabase/seed/**`, `packages/database/**`
  - Backend Foundation Agent: `apps/api/**` (excluding specific advanced domain routers), `backend/requirements.txt`, `pyproject.toml`
  - Frontend Foundation Agent: `apps/web/package.json`, `apps/web/app/layout.tsx`, `apps/web/app/(auth)/**`, `packages/ui/**`
  - Dashboard and Execution Agent: `apps/web/app/(dashboard)/dashboard/**`, `apps/web/app/(dashboard)/ventures/**`, `apps/web/app/(dashboard)/projects/**`, `apps/web/app/(dashboard)/tasks/**`, `apps/api/app/routers/dashboard.py`, `ventures.py`, `projects.py`, `tasks.py`
- **Dependencies:** Phase 0 Completion.
- **Parallel Execution Plan:** 
  - *Group A (Parallel):* Database Agent writes SQL migrations simultaneously with Backend Foundation configuring FastAPI auth frameworks and Frontend Foundation configuring Next.js terminal themes and login pages.
  - *Group B (Sequential after Group A):* Dashboard and Execution Agent constructs interactive command screens and corresponding CRUD endpoints once database tables and Auth JWT verification middleware are live.
- **Acceptance Criteria:** Users can sign in via Email or Magic Link; dashboard renders real-time mission focus; ventures, projects, and tasks can be created, updated, and soft-deleted; all queries execute strictly scoped by authenticated `user_id`.
- **Required Tests:** Pytest unit tests for FastAPI Auth middleware; pgTAP SQL test asserting RLS prevents cross-user visibility on `ventures`, `projects`, and `tasks`; Next.js production build check (`pnpm build`).
- **Security Gate:** Audit confirming JWT cryptographic verification operates locally without relying on client request parameters; confirm `SUPABASE_SERVICE_ROLE_KEY` is excluded from frontend bundles.
- **Exit Criteria:** Core foundation builds successfully; RLS isolation verified; all Phase 1 unit and API tests execute cleanly with zero errors.

---

### Phase 2: Memory Layer & Founder CRM (Weeks 3-4)
- **Objective:** Construct the Network Intelligence Founder CRM, relationship graphing tables, meetings transcription loggers, reflective personal memories, universal Markdown export engines, and Google Drive cloud backup sync automation.
- **Deliverables:**
  - Network Intelligence CRM UI & API (`/people`, `/organizations`, `/people/[personId]`, relationship multi-directional junction graph).
  - Interactions and meetings journal (`/interactions`, `/meetings`, participant linking, audio Blob URLs, takeaway extraction).
  - Freeform reflective memories stream (`/memories`).
  - Asynchronous Markdown Export Worker (`apps/api/workers/exporter.py` writing structured YAML-frontmatter files to `knowledge/Founder_OS/`).
  - Google Drive automated backup worker (`POST /api/v1/integrations/google-drive/sync` utilizing AES-256-GCM token encryption) and Google Calendar two-way task due date synchronization.
- **Assigned Agents:**
  - **Group B:** CRM and Memory Agent.
  - **Group C:** Integrations and Export Agent.
- **Owned Paths:**
  - CRM and Memory Agent: `apps/web/app/(dashboard)/people/**`, `organizations/**`, `memories/**`, `meetings/**`, `apps/api/routers/crm.py`, `interactions.py`, `meetings.py`, `memories.py`
  - Integrations and Export Agent: `apps/web/app/(dashboard)/settings/integrations/**`, `export/**`, `apps/api/routers/integrations.py`, `exports.py`, `apps/api/workers/gdrive.py`, `exporter.py`, `gcal.py`, `knowledge/Founder_OS/**`
- **Dependencies:** Phase 1 Completion (Foundation, Auth, and Projects/Tasks operational).
- **Parallel Execution Plan:**
  - *Parallel Group:* CRM and Memory Agent implements CRM contact cards and interaction interfaces concurrently while Integrations and Export Agent constructs the Google OAuth authentication callback flow and offline Markdown YAML frontmatter generation engine.
- **Acceptance Criteria:** Founder can record mentors/investors and link them to startup projects; meetings log action items; manual trigger of Markdown Export generates structured `.md` files in local `knowledge/Founder_OS/` directory; Google Drive backup job cleanly zips and pushes archives to restricted app cloud storage.
- **Required Tests:** Pytest verifying markdown file path sanitation prevents Path Traversal attacks (`../../`); unit test asserting AES-256-GCM token encryption encrypts and decrypts OAuth credentials properly; component tests for CRM contact timeline rendering.
- **Security Gate:** Verify Google OAuth scopes are limited strictly to `calendar.events` and `drive.file` / appdata (zero full-drive global scopes permitted); assert that refresh tokens are never written unencrypted to database columns or application logs.
- **Exit Criteria:** CRM and Memory layer fully operational; offline markdown exports match PostgreSQL canonical schemas 1:1; automated tests pass.

---

### Phase 3: AI Layer & Vector Search (Weeks 5-6)
- **Objective:** Deploy the polymorphic AI Provider Abstraction layer (`BaseLLMProvider`), implement the 15-step Retrieval-Augmented Generation (RAG) pipeline utilizing pgvector neural memory embeddings, build hybrid similarity search endpoints, construct document attachment ingestion workers, and launch the real-time SSE streaming AI Founder Coach chat interface.
- **Deliverables:**
  - AI Provider Driver wrapper (`apps/api/app/ai/provider.py` supporting `GeminiLLMProvider` primary and `OpenAILLMProvider` fallback).
  - Document parsing & chunking worker (`apps/api/workers/rag_ingestor.py` utilizing 500-token sliding windows with 100-token overlap).
  - pgvector embedding integration (`public.memory_embeddings`, IVFFlat index, Gemini `text-embedding-004` generation).
  - Hybrid memory search engine (`POST /api/v1/search/hybrid` executing Reciprocal Rank Fusion of vector distance + FTS trigram keyword ranking).
  - Live streaming AI Founder Coach interface (`apps/web/app/(dashboard)/assistant/**`, SSE endpoint `POST /api/v1/ai/chat/stream`, interactive citation grounding overlay).
- **Assigned Agents:** **Group C:** AI Retrieval Agent.
- **Owned Paths:** `apps/api/app/ai/**`, `apps/api/routers/search.py`, `assistant.py`, `documents.py`, `apps/web/app/(dashboard)/assistant/**`, `packages/prompts/**`.
- **Dependencies:** Phase 2 Completion (CRM memories, meeting notes, and document attachments must exist to provide vectorization input).
- **Parallel Tasks:** None (Core ML pipeline focused execution).
- **Acceptance Criteria:** Uploaded document PDFs extract text and populate 768-dim vectors in `public.memory_embeddings`; semantic queries return relevant historical advice above 0.55 similarity threshold; AI Coach streams text via Vercel SSE data protocol and displays clickable source citations linking directly to canonical database records; zero hallucinated facts without citation grounding.
- **Required Tests:** RAG accuracy integration test validating hybrid retrieval precision; streaming endpoint test asserting clean termination and partial transcript saving upon client disconnection; unit test validating automatic failover from Gemini to OpenAI upon simulated HTTP 429 rate limit exceptions.
- **Security Gate:** Verify prompt injection defenses: confirm retrieved fact blocks are encapsulated within `<RETRIEVED_CONTEXT>` XML tags; assert that destructive tool functions (`delete_venture`) are omitted from AI function schemas; confirm LLM vendor network clients mandate enterprise zero-data-retention headers (`store=false`).
- **Exit Criteria:** Hybrid search sub-second latency confirmed; AI Coach conversations stream reactively with 100% citation grounding; security prompt injection tests pass.

---

### Phase 4: Intelligence Products & Content Engine (Weeks 7-8)
- **Objective:** Build advanced executive synthesis products: the Idea Vault with AI market opportunity validation, the Life KPI tracking growth matrix, the Career Proof Achievement Portfolio builder with automated case study generation, and the authentic AI Content Engine for drafting LinkedIn social updates and founder stories.
- **Deliverables:**
  - Idea Vault interactive validator (`/ideas`, AI opportunity analyzer endpoint `POST /api/v1/ideas/{id}/analyze`, idea-to-project converter).
  - Life KPI time-series growth tracking matrix (`/kpis`, check-in audit logs, Recharts interactive analytical progress charts).
  - Career Proof Portfolio & Case Study generator (`/achievements`, `/portfolio/case-studies`, AI PM case study synthesis engine).
  - AI Content Engine studio (`/content`, LinkedIn post generator grounded in founder memories, revision version control rollback tool).
  - Automated Weekly Strategic Review generator (`/weekly-reviews`, task/KPI reflection analyzer).
- **Assigned Agents:** **Group C:** KPI and Portfolio Agent.
- **Owned Paths:** `apps/web/app/(dashboard)/ideas/**`, `kpis/**`, `achievements/**`, `content/**`, `weekly-reviews/**`, `apps/api/routers/ideas.py`, `kpis.py`, `portfolio.py`, `content.py`, `weekly_reviews.py`, `packages/ui/components/charts/**`.
- **Dependencies:** Phase 3 Completion (Requires operational RAG semantic search and BaseLLMProvider abstraction to synthesize grounded content).
- **Parallel Tasks:** None.
- **Acceptance Criteria:** Ideas can be scored and mathematically converted into active projects; KPI targets record weekly check-in values and visualize historical trajectory; Content Engine drafts LinkedIn posts incorporating actual startup milestones and citations; Weekly Review identifies operational execution bottlenecks.
- **Required Tests:** Component tests for KPI Recharts visualization hydration; backend API unit test verifying version history creation and rollback mechanics on content edits; integration test asserting portfolio generator extracts actual skills and impact metrics from linked achievements.
- **Security Gate:** Confirm writing tools triggered during content or portfolio generation do not automatically publish to internet APIs; verify outputs remain inside internal drafting status requiring explicit human review.
- **Exit Criteria:** All five advanced intelligence modules fully functional; UI design matches Retro-Futuristic Terminal aesthetic; tests pass.

---

### Phase 5: Model Context Protocol (MCP) Server (Weeks 9-10)
- **Objective:** Build and launch the standalone Python MCP Server (`apps/mcp-server/`), implement cryptographic client token authentication (`X-MCP-API-KEY`), register all 9 required operational MCP tools, and deploy configuration docs enabling external AI assistants (Claude Desktop, ChatGPT, Claude Code, Gemini CLI) to securely access Second Brain context.
- **Deliverables:**
  - Standalone MCP application runtime (`apps/mcp-server/main.py` communicating via JSON-RPC Stdio / SSE).
  - Cryptographic token authentication & rate-limiting middleware (60 req/min limit, verification against `profiles.settings`).
  - All 9 Required MCP Tools (`search_people`, `search_memory`, `get_projects`, `get_tasks`, `get_calendar`, `get_relationship_history`, `generate_linkedin_post`, `generate_case_study`, `generate_weekly_review`).
  - Internal Domain Service bridge (ensuring MCP calls shared repositories in `packages/database` rather than executing raw SQL queries).
  - Client connection installation guidelines (`claude_desktop_config.json` blueprints).
- **Assigned Agents:** **MCP Agent**.
- **Owned Paths:** `apps/mcp-server/**`, `docs/api/mcp_tools.json`.
- **Dependencies:** Phase 4 Completion (All database schemas, RAG retrieval engines, and intelligence content generators must be operational).
- **Parallel Tasks:** None.
- **Acceptance Criteria:** Claude Desktop and ChatGPT can attach to local/remote MCP server; invoking `search_memory` returns accurate hybrid RAG chunks with cosine similarity scores; invoking `generate_linkedin_post` outputs staged draft text without modifying live databases; unauthenticated connections are immediately rejected with JSON-RPC `-32001 (Unauthorized)`.
- **Required Tests:** Automated Python MCP client harness simulating JSON-RPC tool invocations across all 9 tools; unit test asserting MCP tool execution under `User_A` API key cannot read CRM contacts belonging to `User_B`; rate limit saturation test.
- **Security Gate:** Verify read-only default policy: assert that MCP server has zero SQL database write permissions for primary table structural deletion; confirm every MCP action logs to `public.audit_logs` tagged with `source='mcp_server'`.
- **Exit Criteria:** All 9 MCP tools verified against external LLM client interfaces; zero unauthorized security bypasses observed; automated tool test suite passes 100%.

---

### Phase 6: System Hardening, Testing & Security Review (Week 11)
- **Objective:** Conduct rigorous end-to-end integration testing, browser automated UI traversal, cross-user RLS database penetration audits, AI grounding verification, prompt-injection red-teaming, dependency scanning, and accessibility/performance benchmarking across the entire full-stack ecosystem.
- **Deliverables:**
  - Complete Playwright / Cypress E2E automated workflow suites (`tests/e2e/**`).
  - Database RLS penetration test reports (pgTAP tests asserting absolute multi-tenant boundary integrity).
  - AI Grounding and Hallucination evaluation benchmark reports (verifying RRF hybrid search precision > 0.55).
  - OWASP ZAP and Python Bandit security vulnerability inspection reports.
  - Final audit of application loggers to confirm zero plaintext secret or prompt leakage occurs under maximum verbosity settings.
- **Assigned Agents:** 
  - **Security Review Agent** (Owning security penetration, RLS audit, prompt injection testing, secret inspection).
  - **QA & E2E Testing Agent** (Owning Playwright browser workflows, performance profiling, responsive theme checking).
- **Owned Paths:** `tests/e2e/**`, `tests/integration/**`, `tests/security/**`, `security_and_privacy_plan.md`, `integration_status.md`.
- **Dependencies:** Phase 5 Completion (All application features and MCP integration layers code-complete).
- **Parallel Execution Plan:** Security Review Agent executes automated red-teaming and RLS fuzzing concurrently while QA & E2E Testing Agent runs cross-browser automation scripts and terminal responsiveness evaluations.
- **Acceptance Criteria:** Zero critical or high-severity security vulnerabilities detected; E2E tests execute complete founder workflows (auth -> create venture -> ingest meeting -> AI chat retrieval -> markdown export) with zero console network errors; WCAG 2.1 AA accessibility contrast compliance verified on terminal theme.
- **Required Tests:** Execution of full workspace CI testing pipeline: `pnpm test`, `pytest`, `pg_prove`, and `playwright test`.
- **Security Gate:** **Master Security Gate:** Formal sign-off from Security Review Agent certifying that all 15 threat models defined in `security_and_privacy_plan.md` are actively mitigated and operationalized in code.
- **Exit Criteria:** 100% test pass rate achieved; zero open critical architectural or security defects; system declared staging-ready.

---

### Phase 7: Production Readiness & Release Deployment (Week 12)
- **Objective:** Provision production hosting container environments (Vercel Edge for Next.js frontend, Render/Railway Linux container clusters for FastAPI and MCP services, Supabase production DB poolers), verify backup rehydration recovery routines, finalize production documentation, and execute official release deployment.
- **Deliverables:**
  - Production Dockerfiles and CI/CD automated release workflows (`docs/deployment/Dockerfile`, GitHub Actions deployment yaml).
  - Verified production environment variable injection (`SUPABASE_DB_URL`, `TOKEN_ENCRYPTION_KEY`, `GEMINI_API_KEY`).
  - Automated disaster recovery backup rehydration test verification report (confirming `.zip` markdown backups can recreate production database from scratch).
  - Production Uptime & Observability Monitor configuration (`GET /api/v1/health` sub-second alerting).
  - Formal **Production Readiness & Release Decision Report** submitted to Taj and Agent 0.
- **Assigned Agents:** Agent 0 — Lead Orchestrator, Agent 1 — Architecture and Contracts Agent, Backend & Frontend Foundation Agents.
- **Owned Paths:** `docs/deployment/**`, `docker-compose.yml`, root deployment configuration files.
- **Dependencies:** Phase 6 Completion and Master Security Gate Sign-off.
- **Parallel Tasks:** None (Atomic deployment pipeline execution).
- **Acceptance Criteria:** Live production web application accessible at custom domains; backend API responds cleanly to JWT bearer calls; Google Drive backup workers synchronize production markdown archives; MCP server successfully communicates with external Claude Desktop clients over HTTPS SSE.
- **Required Tests:** Production smoke testing suite; disaster recovery restoration drill from Google Drive compressed markdown backup archive.
- **Security Gate:** Verification of TLS 1.3 encryption across all network conduits; confirmation that database connections route strictly through SSL connection poolers (`sslmode=require`); final production secret environment variable audit.
- **Exit Criteria:** Lead Orchestrator and Founder review Production Readiness Report; formal authorization granted; Taj’s Second Brain is officially deployed to general availability.

---

## 3. Master Multi-Agent Task & Ownership Dependency Board

```mermaid
gantt
    title Taj's Second Brain - Master Phased Implementation Schedule
    dateFormat  YYYY-MM-DD
    axisFormat  Week %W
    section Phase 0: Arch
    Architecture & Technical Contracts (Agent 0 & 1)     :done,    p0, 2026-08-01, 7d
    section Phase 1: Foundation
    Group A: Database Migrations & RLS (DB Agent)          :active,  p1_db, 2026-08-08, 14d
    Group A: FastAPI Backend Foundation (Backend Agent)    :active,  p1_be, 2026-08-08, 14d
    Group A: Next.js Terminal UI Setup (Frontend Agent)    :active,  p1_fe, 2026-08-08, 14d
    Group B: Founder Dashboard & Tasks (Dashboard Agent)   :         p1_dash, after p1_db p1_be p1_fe, 7d
    section Phase 2: Memory & CRM
    Group B: Network CRM & Meetings (CRM Agent)            :         p2_crm, after p1_dash, 14d
    Group C: Markdown Export & GDrive Sync (Export Agent)  :         p2_sync, after p1_dash, 14d
    section Phase 3: AI & RAG
    Group C: RAG Pipeline & AI Assistant (AI Agent)        :         p3_ai, after p2_crm p2_sync, 14d
    section Phase 4: Intelligence
    Group C: KPI, Idea Vault & Content Engine (KPI Agent)  :         p4_intel, after p3_ai, 14d
    section Phase 5: MCP
    Standalone Python MCP SDK Server (MCP Agent)           :         p5_mcp, after p4_intel, 14d
    section Phase 6: Hardening
    E2E Browser & Automated QA Testing (QA Agent)         :         p6_qa, after p5_mcp, 7d
    Security & RLS Penetration Red-Teaming (Security Agent):         p6_sec, after p5_mcp, 7d
    section Phase 7: Release
    Production Container Deployment & Release (All Agents) :         p7_rel, after p6_qa p6_sec, 7d
```
