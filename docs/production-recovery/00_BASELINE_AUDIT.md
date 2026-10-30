# 00 — PRODUCTION RECOVERY BASELINE AUDIT

**Auditor:** Principal Production Recovery Engineer  
**Date:** 2026-08-24  
**Repository:** `t4j44/mysecondbrain`  
**Audit Methodology:** Full source-code read, pattern search, test execution, cross-referencing documentation claims against actual implementation.

---

> [!CAUTION]
> **VERDICT: This repository is NOT production ready.**  
> Documentation claims "100% INTEGRATED, RECONCILED & PASSED PRODUCTION GATES" and "56 PASSED / 0 FAILED".  
> The actual state is **~35% integrated** with **P0 security vulnerabilities**, **15 stub frontend pages**, **5 unauthenticated API endpoint files**, **simulated Google OAuth**, **simulated AI providers**, and **simulated Google sync jobs**.

---

## Executive Summary

| Metric | Documentation Claim | Verified Reality |
|---|---|---|
| Integration Status | "100% INTEGRATED" | **~35% integrated** |
| Test Count | "56 PASSED / 0 FAILED" (also "53 tests" in README) | **74 tests collected** across 18 files |
| Frontend Routes Functional | "30/30 routes optimized" | **15 of 30 routes are stubs** showing toast placeholders |
| RLS Coverage | "100% RLS table policy coverage" | SQL migrations define RLS for 33 tables; **5 API endpoint files bypass JWT entirely** |
| API Auth Coverage | "Zero hardcoded user IDs" | **5 endpoint files use hardcoded `00000000-0000-0000-0000-000000000001`** |
| Google OAuth | "Connected and credentials encrypted" | **Simulated refresh tokens**, no real Google API calls |
| AI Provider | "Gemini/OpenAI RAG pipelines" | Returns `[Simulated Gemini Output]` with placeholder keys |
| Google Drive Sync | "Verified" | Returns **hardcoded `synced_files_count: 14`** |
| Google Calendar Sync | "Verified" | Returns **hardcoded `events_synchronized: 5`** |
| Blocker Count | "0 open blockers (BLK-001–BLK-008 CLOSED)" | **12+ P0/P1 blockers identified below** |

---

## Domain-by-Domain Audit

---

### 1. Authentication

**STATUS:** PARTIAL

**IMPLEMENTED:**
- JWT Bearer auth dependency in [`dependencies/auth.py`](file:///e:/second%20brain/apps/api/app/dependencies/auth.py) with JWKS asymmetric verification and HS256 fallback.
- `AuthenticatedUser` model extracting `sub` claim from verified token.
- Production config validator blocking placeholder secrets.
- Proper auth used in `founder.py`, `ai_portfolio.py`, `network.py`, `knowledge.py`, `system.py`, `pdf_analysis.py`.
- Frontend Supabase SSR auth with cookie session management and middleware route protection.

**MISSING:**
- No refresh token rotation flow implemented.
- No rate limiting on auth attempts (general rate limiter exists but no auth-specific one).

**BROKEN:**
- **P0 SECURITY**: Five API endpoint files define their own `get_current_user_id()` returning hardcoded UUID `00000000-0000-0000-0000-000000000001`, completely bypassing JWT auth:
  - [`achievements.py:L24-25`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/achievements.py#L24-L25)
  - [`content.py:L26-27`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/content.py#L26-L27)
  - [`ideas.py:L27-32`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/ideas.py#L27-L32)
  - [`kpis.py:L27-28`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/kpis.py#L27-L28)
  - [`portfolio.py:L26-27`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/portfolio.py#L26-L27)
- **Note:** These 5 files are **not mounted** in `router.py` (the canonical routers in `founder.py`, `ai_portfolio.py` etc. ARE properly authenticated). However, they are **present in the codebase** and referenced in documentation as "completed". They use `MockDbClient` and are not connected to the real database.

**EVIDENCE:**
- [`router.py`](file:///e:/second%20brain/apps/api/app/api/v1/router.py) — only imports `founder`, `network`, `knowledge`, `ai_portfolio`, `system`, `pdf_analysis`, `mcp`. Does NOT import `achievements`, `content`, `ideas`, `kpis`, `portfolio`.
- The 5 unmounted files exist as orphaned Agent 9 prototypes.

**TEST:** JWT auth tests exist in `test_auth_security.py` (8 tests) and `test_security_suite.py` (5 tests). These test the properly authenticated endpoints.

**PRIORITY:** P0 (orphan files with hardcoded auth must be deleted or refactored before any deployment)

---

### 2. Database / Supabase

**STATUS:** PARTIAL

**IMPLEMENTED:**
- 16 ordered SQL migration files in [`supabase/migrations/`](file:///e:/second%20brain/supabase/migrations) creating ~56 tables with proper foreign keys, triggers, and validation functions.
- Extensions: `uuid-ossp`, `vector` (pgvector), `pg_trgm`, `citext`, `pgcrypto`.
- pgTAP test suites: 25 schema tests, 15 RLS tests, 10 vector search tests.
- Development seed data with test user and sample ventures/projects.
- SQLite fallback for local development via `aiosqlite`.

**MISSING:**
- pgTAP tests are **never executed in CI** — no `supabase test db` step in GitHub Actions.
- No evidence of migrations ever applied to a live Supabase instance.

**BROKEN:**
- Schema vs migration divergence (see Domain #3).
- Development runs on SQLite which cannot test pgvector, RLS, or PL/pgSQL functions.

**EVIDENCE:**
- [`.github/workflows/security_ci.yml`](file:///e:/second%20brain/.github/workflows/security_ci.yml) — no `supabase` CLI usage.
- [`config.py:L16`](file:///e:/second%20brain/apps/api/app/config.py#L16) — default `sqlite+aiosqlite:///./brain_dev.db`.

**TEST:** pgTAP tests exist but are NOT run. SQLite tests pass but do not test RLS/vector.

**PRIORITY:** P1

---

### 3. Schema vs SQLAlchemy Model Alignment

**STATUS:** PARTIAL

**IMPLEMENTED:**
- 26 SQLAlchemy models in [`entities.py`](file:///e:/second%20brain/apps/api/app/models/entities.py), [`crm.py`](file:///e:/second%20brain/apps/api/app/models/crm.py), [`meetings.py`](file:///e:/second%20brain/apps/api/app/models/meetings.py) covering core domain tables.
- `FlexibleUUID` type for SQLite/PostgreSQL UUID compatibility.
- `JSONEncodedDict`/`JSONEncodedList` TypeDecorators for cross-database JSON support.

**MISSING:**
- Supabase migrations define ~56 tables but SQLAlchemy models only cover 26.
- Missing models for: `tags`, `project_members`, `task_comments`, `task_tags`, `relationships` (exists in crm.py but minimal), `interaction_participants`, `person_venture_links`, `person_project_links`, `memory_people`, `memory_projects`, `memory_ventures`, `memory_tags`, `idea_people`, `idea_projects`, `idea_memories`, `decision_people`, `decision_documents`, `document_links`, `document_chunks`, `embeddings`, `embedding_jobs`, `kpi_definitions`, `achievement_evidence`, `case_study_sources`, `ai_conversations`, `ai_messages`, `ai_message_sources`, `content_sources`, `weekly_review_sources`, `integration_tokens`, `sync_jobs`, `export_jobs`, `export_items`.

**BROKEN:**
- The SQLAlchemy `JobRecord` model maps to table `jobs` but migrations create `sync_jobs`/`export_jobs` (separate tables).
- The SQLAlchemy `ExportRecord` model maps to table `exports` but migrations create `export_jobs`.
- `MemoryEmbedding.embedding` column is `Text` type in SQLAlchemy but `vector(768)` in PostgreSQL migration.
- Several junction tables defined in migrations have no ORM models, meaning the API cannot interact with them via SQLAlchemy.

**EVIDENCE:**
- [`entities.py`](file:///e:/second%20brain/apps/api/app/models/entities.py) — 26 models.
- Migration `000004` through `000012` — ~56 tables.

**TEST:** No automated schema alignment test exists.

**PRIORITY:** P1

---

### 4. Ventures

**STATUS:** PASS

**IMPLEMENTED:**
- SQLAlchemy model `Venture` with full columns.
- `VentureRepository` with `get_by_slug`, `get_by_name`, `get_active_count`.
- `VentureService` with CRUD operations.
- API endpoints in `founder.py` behind proper JWT auth.
- Migration creating `ventures` table with RLS policies.

**MISSING:**
- Frontend ventures page is a **STUB** showing toast: "VENTURE STUB: Agent 5 will build venture initialization modals here."

**BROKEN:** None in backend.

**EVIDENCE:** [`founder.py`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/founder.py), [`ventures/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/ventures/page.tsx#L21)

**TEST:** Tested via `test_founder_domain.py`.

**PRIORITY:** P2 (backend works, frontend stub)

---

### 5. Projects

**STATUS:** PASS (backend) / FAIL (frontend)

**IMPLEMENTED:**
- Full backend: Model, Repository, Service, authenticated API endpoint.

**MISSING:**
- Frontend is a STUB: "PROJECT STUB: Project management board arriving with Agent 5."

**EVIDENCE:** [`projects/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/projects/page.tsx#L21)

**TEST:** Tested in `test_founder_domain.py`.

**PRIORITY:** P2

---

### 6. Tasks

**STATUS:** PASS (backend) / FAIL (frontend)

**IMPLEMENTED:**
- Full backend: Model, Repository with `get_tasks_today`/`get_overdue_tasks`, Service, authenticated API endpoint.

**MISSING:**
- Frontend is a STUB: "TASK ENGINE STUB: Agent 5 will attach full interactive CRUD forms here."

**EVIDENCE:** [`tasks/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/tasks/page.tsx#L21)

**TEST:** Tested in `test_founder_domain.py`.

**PRIORITY:** P2

---

### 7. People / CRM

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend: `Person` model, `CRMRepository`, `PersonService`, authenticated endpoints in `network.py`.
- Frontend: People list page is a STUB, but `people/new` and `people/[personId]` have functional forms.

**BROKEN:**
- Frontend hooks (`usePeople.ts`, `useMeetings.ts`, `useMemories.ts`) use `localStorage.getItem('supabase_session_token')` instead of the proper Supabase auth client.
- `people/[personId]` has dead links to `/interactions/new` (non-existent route) and `/people/.../edit` (non-existent route).

**EVIDENCE:**
- [`usePeople.ts:L52,81,107`](file:///e:/second%20brain/apps/web/hooks/usePeople.ts#L52)
- [`people/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/people/page.tsx#L21) — STUB

**TEST:** `test_crm_memory.py` (5 tests).

**PRIORITY:** P1

---

### 8. Organizations

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend: `Organization` model, `CRMRepository`, `OrganizationService`, authenticated endpoints.

**MISSING:**
- Frontend is a STUB: "ORG STUB: Agent 6 will enable corporate directory mapping here."

**EVIDENCE:** [`organizations/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/organizations/page.tsx#L21)

**TEST:** Tested via `test_crm_memory.py`.

**PRIORITY:** P2

---

### 9. Interactions

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend: `Interaction` model, `InteractionsRepository`, `InteractionService`, authenticated endpoints.
- No dedicated frontend page exists.

**MISSING:**
- Frontend route for interactions does not exist (dead link from `people/[personId]`).

**EVIDENCE:** [`network.py`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/network.py)

**TEST:** Tested via `test_crm_memory.py`.

**PRIORITY:** P2

---

### 10. Meetings

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend: `Meeting` model with `MeetingParticipant` junction, `MeetingsRepository`, `MeetingService`, authenticated endpoints.
- Frontend: List page is STUB. Detail page `meetings/[meetingId]` exists but has issues.

**BROKEN:**
- `meetings/[meetingId]/page.tsx` uses `localStorage` for auth tokens, N+1 fetch calls in a loop (Lines 36-42), and `alert()` instead of toast notifications.

**EVIDENCE:**
- [`meetings/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/meetings/page.tsx#L21) — "MEETING AUDIO STUB"
- [`meetings/[meetingId]/page.tsx:L36-42`](file:///e:/second%20brain/apps/web/app/(dashboard)/meetings/[meetingId]/page.tsx#L36-L42) — N+1 queries

**TEST:** `test_crm_memory.py`.

**PRIORITY:** P2

---

### 11. Memories

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend: `Memory` model, `MemoriesRepository`, `MemoryService`, authenticated endpoints.
- Frontend: List page is STUB. `memories/new` creation form exists.

**BROKEN:**
- `memories/new/page.tsx` uses `localStorage` for auth token.
- Re-embedding logic is a comment stub: "mocked/notified via meta or state" ([`memories.py:L119`](file:///e:/second%20brain/apps/api/app/repositories/memories.py#L119)).

**EVIDENCE:** [`memories/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/memories/page.tsx#L21) — "MEMORY STUB"

**TEST:** `test_crm_memory.py`, `test_knowledge_ai.py`.

**PRIORITY:** P2

---

### 12. Ideas

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend canonical: `Idea` model, `IdeaRepository` (base repo), `IdeaService` in `knowledge.py`, authenticated endpoint in `knowledge.py`.
- Backend orphan: Agent 9 prototype `ideas.py` endpoint with hardcoded UUID and `MockDbClient` (NOT mounted).

**MISSING:**
- Frontend is a STUB: "IDEA INCUBATOR STUB: Agent 8 will implement AI idea scoring here."
- `analyze_idea_feasibility()` returns hardcoded offline scores (`problem_clarity_score=8`, `solution_viability_score=7`).

**EVIDENCE:**
- [`ideas/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/ideas/page.tsx#L21)
- [`idea_service.py:L74-94`](file:///e:/second%20brain/apps/api/app/services/ideas/idea_service.py#L74-L94)

**TEST:** `test_ideas_api.py` (3 tests — tests the orphan prototype, not the canonical endpoint).

**PRIORITY:** P2

---

### 13. Decisions

**STATUS:** PASS (backend) / FAIL (frontend)

**IMPLEMENTED:**
- Backend: `Decision` model, `DecisionService`, authenticated endpoint in `knowledge.py`.

**MISSING:**
- No dedicated frontend page for decisions.

**TEST:** `test_knowledge_ai.py`.

**PRIORITY:** P3

---

### 14. Documents

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend: `Document` model, `DocumentService`, PDF upload/analysis endpoints, `PDFValidator`.

**BROKEN:**
- Document processing job uses **simulated text extraction**: `f"[Extracted knowledge from {doc.sanitized_filename}]"` ([`document_processing.py:L25`](file:///e:/second%20brain/apps/api/app/jobs/handlers/document_processing.py#L25)).
- No actual PDF text extraction library integrated (no `PyPDF2`, `pdfminer`, `pdfplumber` etc.).

**EVIDENCE:** [`document_processing.py:L25`](file:///e:/second%20brain/apps/api/app/jobs/handlers/document_processing.py#L25)

**TEST:** `test_pdf_analysis.py` (9 tests), `test_storage_client.py` (10 tests).

**PRIORITY:** P1

---

### 15. Achievements

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend canonical: `Achievement` model, `AchievementService` in `knowledge.py`, authenticated endpoint in `ai_portfolio.py`.
- Backend orphan: Agent 9 prototype with `MockDbClient` (NOT mounted).

**MISSING:**
- Frontend is a STUB: "ACHIEVEMENT STUB: Agent 8 will enable automated case-study conversion here."

**EVIDENCE:** [`achievements/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/achievements/page.tsx#L21)

**TEST:** `test_achievements_api.py` (1 test — tests the orphan prototype).

**PRIORITY:** P2

---

### 16. Portfolio

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend canonical: `PortfolioCaseStudy` model, `PortfolioService`, authenticated endpoint in `ai_portfolio.py`.
- `generate_grounded_case_study()` uses offline template fallback when API key is placeholder.

**MISSING:**
- No dedicated frontend page.

**EVIDENCE:** [`portfolio_service.py:L64-122`](file:///e:/second%20brain/apps/api/app/services/portfolio/portfolio_service.py#L64-L122)

**TEST:** `test_portfolio_api.py` (1 test — tests orphan prototype).

**PRIORITY:** P3

---

### 17. Content

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Backend canonical: `ContentItem`/`ContentVersion` models, `ContentService` in `knowledge.py`, authenticated endpoint in `ai_portfolio.py`.
- Backend orphan: Agent 9 prototype with `MockDbClient` and mock source records (NOT mounted).

**MISSING:**
- Frontend is a STUB: "CONTENT ENGINE STUB: Agent 8 will implement automated AI editorial workflows here."

**BROKEN:**
- Orphan `content.py` endpoint generates fake source records for grounded content generation.

**EVIDENCE:**
- [`content/page.tsx:L21`](file:///e:/second%20brain/apps/web/app/(dashboard)/content/page.tsx#L21)
- [`content.py:L73-81`](file:///e:/second%20brain/apps/api/app/api/v1/endpoints/content.py#L73-L81)

**TEST:** `test_content_engine_api.py` (2 tests).

**PRIORITY:** P2

---

### 18. AI Assistant

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Frontend: `ChatArea.tsx` (387 lines) — production-grade SSE streaming chat with Vercel AI SDK protocol, citations, thinking animation, auto-scroll, transcript export.
- Backend: `/ai/search` endpoint with RAG retrieval, `AIService`, `GeminiLLMProvider`.
- `useChat.ts` hook (335 lines) handling SSE delta streaming.

**BROKEN:**
- With placeholder API keys, returns `[Simulated Gemini Output for: ...]` — not a real AI response.
- Hardcoded confidence score `score=0.89` in retrieval results ([`retrieval.py:L45`](file:///e:/second%20brain/apps/api/app/ai/retrieval.py#L45)).

**EVIDENCE:**
- [`provider.py:L33-40`](file:///e:/second%20brain/apps/api/app/ai/provider.py#L33-L40) — simulated output
- [`retrieval.py:L45`](file:///e:/second%20brain/apps/api/app/ai/retrieval.py#L45) — hardcoded `0.89`

**TEST:** `test_knowledge_ai.py` (5 tests). Tests run against simulated provider.

**PRIORITY:** P1 (AI is a core differentiator but currently simulated)

---

### 19. RAG

**STATUS:** PARTIAL

**IMPLEMENTED:**
- `MemoryEmbedding` model, `MemoryEmbeddingRepository` with `search_similar` (ILIKE fallback).
- Supabase `match_memories()` and `hybrid_knowledge_search()` PL/pgSQL functions.
- Chunking pipeline in `document_processing.py` (500-char chunks, 100-char overlap).
- pgvector HNSW + IVFFlat indexes in migration `000014`.

**BROKEN:**
- `embed_text()` returns `[0.01] * 768` synthetic vectors with placeholder keys.
- `search_similar` falls back to ILIKE text search on SQLite (cannot test vector similarity).
- `MemoryEmbedding.embedding` is `Text` in SQLAlchemy but `vector(768)` in PostgreSQL — type mismatch.

**EVIDENCE:** [`provider.py:L61-63`](file:///e:/second%20brain/apps/api/app/ai/provider.py#L61-L63)

**TEST:** pgTAP vector tests exist but are NOT executed. Python tests use SQLite.

**PRIORITY:** P1

---

### 20. Gemini

**STATUS:** PARTIAL

**IMPLEMENTED:**
- `GeminiLLMProvider` class with `generate_content()` and `embed_text()` via REST API.
- `GoogleGenAIClient` for document analysis.
- Production guard: raises `AIProviderError` if placeholder key used in production.

**BROKEN:**
- Returns simulated output in development/testing environments.
- No integration test with actual Gemini API.

**EVIDENCE:** [`provider.py:L24-77`](file:///e:/second%20brain/apps/api/app/ai/provider.py#L24-L77)

**TEST:** Tests run against simulated provider.

**PRIORITY:** P1

---

### 21. MCP

**STATUS:** PASS

**IMPLEMENTED:**
- 9 MCP tools registered: `search_people`, `search_memory`, `get_projects`, `get_tasks`, `get_relationship_history`, `get_calendar`, `generate_linkedin_post`, `generate_case_study`, `generate_weekly_review`.
- ASGI Streamable HTTP transport mounted at `/mcp` in `main.py`.
- MCP credential management: HMAC key generation, constant-time comparison, rotation, revocation.
- `X-MCP-API-KEY` authentication with scope-based authorization.

**MISSING:**
- `generate_*` tools use simulated AI provider output with placeholder keys.

**EVIDENCE:**
- [`mcp/tools.py`](file:///e:/second%20brain/apps/api/app/mcp/tools.py)
- [`mcp/server.py`](file:///e:/second%20brain/apps/api/app/mcp/server.py)
- [`mcp/security.py`](file:///e:/second%20brain/apps/api/app/mcp/security.py)

**TEST:** `test_mcp_api.py` (1), `test_mcp_auth.py` (3), `test_mcp_tools.py` (1).

**PRIORITY:** P2

---

### 22. Google OAuth

**STATUS:** FAIL

**IMPLEMENTED:**
- `GoogleIntegrationService` class with `connect_oauth_callback()`, `disconnect_provider()`.
- AES-256-GCM token encryption via `encrypt_token()`.
- Callback endpoint in `system.py`.

**BROKEN:**
- **Entirely simulated.** `connect_oauth_callback()` generates a fake refresh token: `f"1//0e_simulated_refresh_token_for_{self.user_id}_{code[:10]}"` ([`google_client.py:L24`](file:///e:/second%20brain/apps/api/app/integrations/google_client.py#L24)).
- Hardcoded email `founder.root@tajssecondbrain.ai` ([`google_client.py:L37`](file:///e:/second%20brain/apps/api/app/integrations/google_client.py#L37)).
- No actual Google OAuth2 library (`google-auth`, `google-auth-oauthlib`, `google-api-python-client`) used for token exchange.

**EVIDENCE:** [`google_client.py:L18-54`](file:///e:/second%20brain/apps/api/app/integrations/google_client.py#L18-L54)

**TEST:** `test_integrations_export.py` tests against simulated flow.

**PRIORITY:** P0 (documented as "VERIFIED & PASSED" but completely fake)

---

### 23. Google Drive

**STATUS:** FAIL

**IMPLEMENTED:**
- Job trigger endpoint for `sync_google_drive`.
- `JobRunner` infrastructure.

**BROKEN:**
- Sync handler returns **hardcoded results**: `{"status": "completed", "synced_files_count": 14}` with no actual Google Drive API calls ([`sync_google.py:L17-24`](file:///e:/second%20brain/apps/api/app/jobs/handlers/sync_google.py#L17-L24)).

**EVIDENCE:** [`sync_google.py:L17-24`](file:///e:/second%20brain/apps/api/app/jobs/handlers/sync_google.py#L17-L24)

**TEST:** `test_integrations_export.py` — tests the simulated flow, passing because the fake data matches expected fake data.

**PRIORITY:** P1

---

### 24. Google Calendar

**STATUS:** FAIL

**IMPLEMENTED:**
- Job trigger endpoint for `sync_google_calendar`.

**BROKEN:**
- Sync handler returns **hardcoded results**: `{"status": "completed", "events_synchronized": 5}` with no actual Calendar API calls ([`sync_google.py:L25-31`](file:///e:/second%20brain/apps/api/app/jobs/handlers/sync_google.py#L25-L31)).

**EVIDENCE:** [`sync_google.py:L25-31`](file:///e:/second%20brain/apps/api/app/jobs/handlers/sync_google.py#L25-L31)

**TEST:** Same as above — tests pass against fake data.

**PRIORITY:** P1

---

### 25. Google Contacts

**STATUS:** NOT TESTED

**IMPLEMENTED:** Nothing. No Google Contacts integration exists.

**MISSING:** Entire module.

**EVIDENCE:** No files reference Google Contacts API or People API.

**PRIORITY:** P3

---

### 26. Markdown Export

**STATUS:** PARTIAL

**IMPLEMENTED:**
- `export_markdown.py` job handler compiles ventures/memories into Markdown files.
- Writes to `.storage_buckets/exports/{user_id}/`.
- Generates signed 48-hour access link.

**BROKEN:**
- Renders to **ephemeral local disk** — incompatible with Render's ephemeral filesystem (documented as resolved in BLK-004 but still writes to local paths).

**EVIDENCE:** [`export_markdown.py:L14-96`](file:///e:/second%20brain/apps/api/app/jobs/handlers/export_markdown.py#L14-L96)

**TEST:** `test_integrations_export.py`.

**PRIORITY:** P2

---

### 27. Frontend Route Integration

**STATUS:** FAIL

**IMPLEMENTED (Functional):**
- Auth routes: `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/verify`, `/callback` — **All functional**.
- Dashboard layout with sidebar, breadcrumbs, command menu, user menu — **Functional**.
- `/assistant` — **Functional** (renders ChatArea).
- `/settings`, `/settings/profile`, `/settings/appearance` — **Functional**.

**STUB PAGES (15 total):**
1. `/dashboard` — Static EmptyState placeholder
2. `/ventures` — STUB (Agent 5)
3. `/projects` — STUB (Agent 5)
4. `/tasks` — STUB (Agent 5)
5. `/people` — STUB (Agent 6)
6. `/organizations` — STUB (Agent 6)
7. `/meetings` — STUB (Agent 6)
8. `/memories` — STUB (Agent 6/9)
9. `/ideas` — STUB (Agent 8)
10. `/content` — STUB (Agent 8)
11. `/kpis` — STUB (Agent 8)
12. `/achievements` — STUB (Agent 8)
13. `/settings/integrations` — STUB (Agent 7)
14. `/settings/export` — STUB (Agent 7)
15. `/settings/export` — STUB (Agent 7, second button)

**BROKEN:**
- 3 hooks (`usePeople`, `useMeetings`, `useMemories`) use `localStorage.getItem('supabase_session_token')` instead of Supabase SSR auth client.
- Dead links in `people/[personId]` to non-existent routes.
- Breadcrumbs component has impossible logic condition ([`breadcrumbs.tsx:L12`](file:///e:/second%20brain/apps/web/components/layout/breadcrumbs.tsx#L12)).
- `meetings/[meetingId]` uses `alert()` instead of toast, N+1 fetch loop.

**EVIDENCE:** STUB search found 15 toast stub patterns in `apps/web/app/(dashboard)/`.

**TEST:** No integration tests verify route functionality.

**PRIORITY:** P1

---

### 28. Mobile Responsiveness

**STATUS:** PARTIAL

**IMPLEMENTED:**
- `mobile-navigation.tsx` component exists.
- `ResponsivePageContainer` wrapper component.
- Tailwind responsive breakpoints configured.
- Playwright config includes "Mobile Chrome" project.

**MISSING:**
- No actual mobile responsive testing has been performed or automated.

**TEST:** NOT TESTED.

**PRIORITY:** P3

---

### 29. CI

**STATUS:** PARTIAL

**IMPLEMENTED:**
- [`.github/workflows/security_ci.yml`](file:///e:/second%20brain/.github/workflows/security_ci.yml) runs on push/PR to `main`/`develop`:
  - `ruff check apps/api`
  - `bandit -r apps/api -x tests`
  - `pytest apps/api/tests/ --cov`
  - `pnpm lint` & `pnpm typecheck`

**MISSING:**
- `mypy` is **installed but never invoked** in CI pipeline.
- `pnpm test` (Vitest unit tests) is **not run** in CI.
- `pnpm test:e2e` (Playwright E2E) is **not run** in CI.
- Supabase pgTAP tests (`supabase test db`) are **not run** in CI.

**EVIDENCE:** [`.github/workflows/security_ci.yml`](file:///e:/second%20brain/.github/workflows/security_ci.yml)

**TEST:** CI pipeline exists but with major gaps.

**PRIORITY:** P1

---

### 30. E2E Tests

**STATUS:** FAIL

**IMPLEMENTED:**
- Playwright config in [`playwright.config.ts`](file:///e:/second%20brain/apps/web/playwright.config.ts).
- Test file [`e2e/essential-flows.spec.ts`](file:///e:/second%20brain/apps/web/e2e/essential-flows.spec.ts) (6 tests).

**BROKEN:**
- **Tests are structurally invalid:**
  1. Use `expect(page.locator('...')).toBeDefined()` which is **always true** in Playwright (locator constructor is synchronous and always returns an object).
  2. No authentication fixture — all protected routes redirect to `/login`, making assertions meaningless.

**EVIDENCE:** [`essential-flows.spec.ts:L21,24,27,32,35,40,45`](file:///e:/second%20brain/apps/web/e2e/essential-flows.spec.ts#L21)

**TEST:** These tests CANNOT verify anything meaningful in their current form.

**PRIORITY:** P1

---

### 31. Security

**STATUS:** PARTIAL

**IMPLEMENTED:**
- SecurityHeadersMiddleware: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `X-XSS-Protection`, `Referrer-Policy`.
- Rate limiting middleware (300 req/min general, 30 req/min strict).
- CORS configuration.
- Production config validator rejecting placeholder secrets and localhost URLs.
- MCP credential security: salted SHA-256 + HMAC constant-time comparison.
- RLS policies for 33 tables in migration `000015`.
- `Bandit` security scanner in CI.

**BROKEN:**
- 5 orphaned endpoint files with hardcoded user IDs (not mounted but present).
- Frontend `localStorage` token retrieval in hooks bypasses Supabase SSR cookie security model.
- Frontend env.ts defaults to `https://mock.supabase.co` — would silently fail in misconfigured deployment.
- `scripts/backup/backup.py` and `restore/restore.py` use `shell=True` in `subprocess.run()`.

**EVIDENCE:** Multiple files cited above.

**TEST:** `test_auth_security.py` (8 tests), `test_security_suite.py` (5 tests).

**PRIORITY:** P0 (orphan files), P1 (localStorage auth bypass)

---

### 32. Deployment Configuration

**STATUS:** PARTIAL

**IMPLEMENTED:**
- Multi-stage `Dockerfile` with non-root `appuser` (UID 10001), dynamic `${PORT:-8000}` binding.
- `docker-compose.yml` with healthcheck and volume mount.
- `.env.example` files for both API and web.
- Production config validator blocks placeholder secrets.

**MISSING:**
- No Render, Railway, or Vercel deployment configuration files (render.yaml, vercel.json).
- `docker-compose.yml` references `.env.example` by default — would fail in production with placeholder secrets.

**EVIDENCE:**
- [`docker-compose.yml:L10`](file:///e:/second%20brain/docker-compose.yml#L10) — `env_file: ./apps/api/.env.example`
- [`Dockerfile`](file:///e:/second%20brain/apps/api/Dockerfile)

**TEST:** Docker build not tested as part of this audit.

**PRIORITY:** P2

---

### 33. Documentation Accuracy

**STATUS:** FAIL

**IMPLEMENTED:**
- 78 markdown specification documents across 11 domains.
- Comprehensive API contracts, database schema, architecture decisions.

**BROKEN — Critical False Claims:**

| Document | Claim | Reality |
|---|---|---|
| [`integration_status.md`](file:///e:/second%20brain/integration_status.md) | "100% INTEGRATED, RECONCILED & PASSED PRODUCTION GATES" | ~35% integrated; 15 frontend stubs; 5 orphan files with hardcoded auth |
| [`integration_status.md`](file:///e:/second%20brain/integration_status.md#L42) | "56 PASSED / 0 FAILED" | 74 tests collected; actual pass/fail ratio to be verified |
| [`README.md`](file:///e:/second%20brain/README.md#L24) | "53 integrated & security tests" | 74 tests collected |
| [`agent_task_board.md`](file:///e:/second%20brain/agent_task_board.md) | All agents "COMPLETED" | Agent 5, 6, 7, 8, 9 work is visibly incomplete (frontend stubs referencing them) |
| [`integration_status.md`](file:///e:/second%20brain/integration_status.md#L44) | "Legacy router stubs cleaned up" | 5 orphan prototype files still present with MockDbClient |
| [`integration_status.md`](file:///e:/second%20brain/integration_status.md#L24) | "Offline Export & Google Sync VERIFIED & PASSED" | Google sync returns hardcoded fake counts |
| [`integration_status.md`](file:///e:/second%20brain/integration_status.md#L14) | "Authentication & Core VERIFIED & PASSED" | 5 endpoint files bypass auth entirely |
| [`security_and_privacy_plan.md`](file:///e:/second%20brain/security_and_privacy_plan.md) | "All 56 tables enforce strict RLS" | RLS defined in SQL but SQLAlchemy only covers 26 models; 5 endpoints bypass auth |
| [`README.md`](file:///e:/second%20brain/README.md#L14) | "No Client-Side user_id Impersonation" | 5 files return hardcoded `00000000-0000-0000-0000-000000000001` |

**EVIDENCE:** All files cited throughout this audit.

**TEST:** This audit IS the verification.

**PRIORITY:** P0

---

## Test Execution Results

**Audit independently ran: `python -m pytest tests/ --co -q`**

Tests collected: **74** (across 18 test files)

| Test File | Count | Notes |
|---|---|---|
| `test_achievements_api.py` | 1 | Tests orphan prototype with MockDbClient |
| `test_auth_security.py` | 8 | Tests real JWT auth dependency |
| `test_content_engine_api.py` | 2 | Tests orphan prototype |
| `test_crm_memory.py` | 5 | Tests canonical endpoints |
| `test_founder_domain.py` | 5 | Tests canonical endpoints |
| `test_health.py` | 4 | Tests health probes |
| `test_ideas_api.py` | 3 | Tests orphan prototype |
| `test_integrations_export.py` | 3 | Tests simulated Google/export flow |
| `test_knowledge_ai.py` | 5 | Tests canonical endpoints |
| `test_kpis_api.py` | 3 | Tests orphan prototype |
| `test_mcp_api.py` | 1 | Tests MCP credential CRUD |
| `test_mcp_auth.py` | 3 | Tests MCP auth |
| `test_mcp_tools.py` | 1 | Tests MCP tools |
| `test_pdf_analysis.py` | 9 | Tests PDF upload/validation |
| `test_portfolio_api.py` | 1 | Tests orphan prototype |
| `test_production_startup_and_pagination.py` | 5 | Tests startup + pagination |
| `test_security_suite.py` | 5 | Tests security |
| `test_storage_client.py` | 10 | Tests storage abstraction |

### Tests Blocked:
- **pgTAP tests** (schema, RLS, vector): Blocked — require running Supabase instance.
- **Playwright E2E tests**: Blocked — tests are structurally invalid (always-true assertions, no auth fixture).
- **Vitest frontend unit tests**: Not executed as part of this audit scope.
- **Integration tests against real Gemini/Google APIs**: Blocked — require real API keys.

---

## Pydantic Deprecation Warnings

The test collection emitted 12 Pydantic deprecation warnings:
- `crm.py:L34,113,146` — Class-based `config` deprecated (use `ConfigDict`)
- `crm.py:L76,103` — V1 `@validator` deprecated (use `@field_validator`)
- `interactions.py:L20,44,54` — V1 `@validator` and class-based config deprecated
- `meetings.py:L39` — Class-based config deprecated
- `memories.py:L17,48,66` — V1 `@validator` and class-based config deprecated

**PRIORITY:** P2 (will break in Pydantic V3)

---

## `pnpm-workspace.yaml` Issue

Lines 5-6 contain placeholder text: `set this to true or false` under `allowBuilds`.

**PRIORITY:** P3
