# MASTER PRODUCTION READINESS PLAN — Taj's Second Brain

**Author:** Principal Recovery Engineer  
**Date:** 2026-08-25  
**Repository:** [t4j44/mysecondbrain](https://github.com/t4j44/mysecondbrain)  
**Canonical branch:** `recovery/core-daily-driver`  
**Execution model:** Sequential Prompts 1→7 + Final Gate (see [`00_MULTI_AGENT_ROLE_PLAN.md`](./00_MULTI_AGENT_ROLE_PLAN.md))  
**Push policy:** **No push** until user explicitly approves.

---

## 1. Executive Summary

### Current state (~30–35% personal production readiness)

| Layer | Status | Evidence |
|-------|--------|----------|
| **Architecture** | Strong | ADR-013 single ASGI service; Supabase JWT + RLS; domain repos/services; MCP mounted at `/mcp` |
| **Backend API** | ~80% | 64 pytest tests pass; Ventures/Projects/Tasks/People CRUD authenticated and tested |
| **Frontend shell** | ~90% | App shell, auth, design system, mobile nav — compiles and builds |
| **Frontend ↔ API wiring** | ~10–15% | Most dashboard routes still EmptyState/toast stubs; People partially wired |
| **RAG / AI (real)** | Fail-closed offline | Hardcoded score `0.89`; simulated Gemini when keys missing |
| **Google Workspace** | 0% real | Simulated OAuth tokens and hardcoded sync metrics |
| **finalize_work_session** | Not productized | MCP tools expanded in tree; killer feature not end-to-end |
| **E2E QA** | Blocked | No Playwright auth fixture; Prompt 3 owns gate |

**Honest verdict today:** **NO-GO** for daily personal use and **NO-GO** for public production. **GO** to begin **Prompt 2** (Core Daily Driver frontend) on a trusted recovery branch after Prompt 1 verification.

### Target: “Fully production ready”

Three distinct targets — do not conflate:

| Target | Definition | Gate |
|--------|------------|------|
| **Core Daily Driver v0.1** | Login → Venture/Project/Task + People CRUD → persist → logout/login → archive/delete. No stubs on those four domains. Centralized `browser-client.ts`. | Prompt 2 + Prompt 3 E2E GO |
| **Personal daily driver (v0.1 release)** | v0.1 + honest RAG path + finalize_work_session MCP write + daily memory/evidence path. Google may be **OAUTH BLOCKED** if documented. | Final Gate **GO** (personal scope only) |
| **Full vision** | Live Google Drive/Calendar/Contacts, portfolio/network intelligence, knowledge graph UX, zero simulated behavior anywhere | Post–v0.1 roadmap |

---

## 2. Vision Synthesis (User Context)

### Product intent

Taj's Second Brain is a **personal AI operating system** for an ADHD founder:

- **Capture once, structure automatically, zero friction** — sacred UX constraint.
- **Venture → Project → Task + People** is the **Core Daily Driver v0.1** — the only product surface that must work before anything else.
- **Killer feature:** `finalize_work_session` — one-click session compilation → structured records → tasks/decisions → evidence linking → idempotent MCP write (Prompt 5).
- **Real RAG** with Gemini + pgvector + citations — not ILIKE-as-vector or hardcoded confidence (Prompt 4).
- **Daily Memory / Evidence** path for personal recall (Prompt 6).
- **Google OAuth / Drive / Calendar / Contacts** — real or honestly blocked; never fake success (Prompt 7).

### Architecture (verified)

- **Frontend:** Next.js 14, Supabase SSR auth, centralized API via `apps/web/lib/api/browser-client.ts`.
- **Backend:** FastAPI in `apps/api/`, SQLAlchemy models aligned to Supabase migrations, JWT on all canonical routes.
- **MCP:** Streamable HTTP at `/mcp` inside same ASGI process (not a separate `apps/mcp-server/` sidecar).
- **AI:** Gemini primary; pgvector hybrid search in PostgreSQL.
- **Persistence:** Supabase PostgreSQL only in production — no ephemeral disk as source of truth.

### ADHD / scope-creep guardrails (non-negotiable)

1. **One coding agent at a time** — no parallel product work.
2. **Document adjacent work; do not implement** in the wrong phase.
3. **No “while we’re here”** refactors, portfolio UI, Google polish, or RAG UX during Prompt 2.
4. **Remove fake/simulated behavior** from anything labeled production — simulated paths may exist only behind explicit dev/offline flags with fail-closed production config.
5. **Independent QA** for E2E (Prompt 3) and Final Gate — fresh sessions, zero builder bias.

### Sequencing rationale

Recovery proved that parallel agents + bulk scripts caused contract breaks, auth regressions, and untrusted trees. Sequential prompts enforce:

**Trust foundation (Prompt 1) → Daily CRUD UI (Prompt 2) → Adversarial E2E (Prompt 3) → Real intelligence layers (4–7) → Zero-trust release (Final).**

Each phase has explicit **GO/NO-GO**; a NO-GO **halts** the pipeline.

---

## 3. Phase Map — Prompts 1–7 + Final Gate

| Phase | Prompt | Owner role | Primary deliverable | GO criteria | NO-GO triggers |
|-------|--------|------------|-------------------|-------------|----------------|
| **0/1** | **1** | Principal Recovery Engineer | `recovery/core-daily-driver`, `11_LOCAL_DIFF_REVIEW.md` | All compile/test gates PASS; Playwright **BLOCKED** documented; status **READY FOR CORE FRONTEND** | pytest/ruff/mypy/typecheck/lint/build FAIL; secrets in tree |
| **2** | **2** | Senior Next.js Product Integration | `12_CORE_DAILY_DRIVER_FRONTEND.md` | Ventures, Projects, Tasks, People — full CRUD via `browser-client.ts`; login/logout/persist verified manually | Any of four domains stub/toast-only |
| **3** | **3** | Independent Senior QA (fresh session) | `13_CORE_E2E_GATE.md` | Playwright auth fixture + non-vacuous assertions; **E2E GO** | Fake/missing auth fixture; `toBeDefined`-style asserts |
| **4** | **4** | Senior AI / Retrieval | `14_REAL_RAG_AI_CHAT.md` | Real cosine scores; fail-closed without keys; no `0.89` constant in prod path | Hardcoded scores; simulation labeled as real |
| **5** | **5** | Senior MCP / Work Intelligence | `15_FINALIZE_WORK_SESSION_MCP.md` | `finalize_work_session` end-to-end + safe MCP write tools | Missing/broken finalize; unsafe writes |
| **6** | **6** | Personal Intelligence / Evidence | `16_DAILY_MEMORY_EVIDENCE.md` | Daily memory capture → evidence linking usable daily | Path broken or stub-only |
| **7** | **7** | Google Workspace Integration | `17_GOOGLE_WORKSPACE.md` | Real OAuth + API calls **or** documented **OAUTH BLOCKED** | Fake success metrics; security regression |
| **8** | **Final** | Independent Release Gatekeeper (fresh) | `V01_RELEASE_GATE.md` | Zero-trust re-verification; **GO** for personal v0.1 only | Any open P0; dishonest status docs |

### Phase dependency diagram

```
Prompt 1 (READY) ──► Prompt 2 ──► Prompt 3 (E2E GO) ──► Prompt 4 (RAG)
                                                      ──► Prompt 5 (Finalize)
                                                      ──► Prompt 6 (Daily Memory)
                                                      ──► Prompt 7 (Google)
                                                              ──► Final Gate
```

---

## 4. P0 / P1 / P2 Defect Backlog (with owners)

Owners per [`docs/orchestration/agent-ownership.md`](../orchestration/agent-ownership.md).

### P0 — Security / blocks daily use

| ID | Defect | Owner | Phase | Status on recovery branch |
|----|--------|-------|-------|---------------------------|
| BLK-001 | Orphan endpoints with hardcoded UUID auth | Agent 11 / Agent 3 | 1 | **FIXED** — deleted/quarantined |
| BLK-003 | Frontend `localStorage` session tokens | Agent 4 | 1 | **FIXED** — Supabase SSR session |
| BLK-003b | `useChat.ts` missing Bearer | Agent 4 | 1 | **FIXED** |
| BLK-002 | 15+ frontend routes toast stubs (Ventures/Tasks/etc.) | Agent 5 / Agent 6 | 2 | **OPEN** |
| BLK-004 | Hardcoded RAG score `0.89` | Agent 8 | 4 | **OPEN** |
| BLK-005 | Simulated AI/embeddings in prod-labeled paths | Agent 8 | 4 | **OPEN** (fail-closed offline OK) |
| BLK-006 | Fake Google OAuth + sync metrics | Agent 7 | 7 | **OPEN** |
| BLK-010 | Vacuous E2E / no auth fixture | Agent 12 | 3 | **BLOCKED** (assertions tightened; fixture missing) |

### P1 — Important broken capability

| ID | Defect | Owner | Phase | Status |
|----|--------|-------|-------|--------|
| BLK-007 | `finalize_work_session` not productized | Agent 10 / Agent 5 | 5 | **OPEN** |
| BLK-008 | MCP write tools missing / unsafe | Agent 10 | 5 | **OPEN** |
| BLK-009 | ORM/schema drift (Meeting setter, Memory body/content) | Agent 3 | 1 | **PARTIAL FIX** — Meeting setter fixed |
| DOC-001 | Docs claim `apps/mcp-server/` sidecar | Agent 13 | 1 | **OPEN** |
| DOC-002 | False “100% integrated” claims | Agent 0 / Agent 13 | 1 | **FIXED** in `integration_status.md` |
| CI-001 | CI missing vitest / mypy until recovery | Agent 11 | 1 | **PARTIAL** — mypy in CI; vitest local PASS |
| API-001 | Dashboard insights hardcoded strings | Agent 5 | 4+ | **OPEN** |
| API-002 | `payload: dict` on KPI routes | Agent 3 | 1 | **FIXED** |

### P2 — Improvement / polish

| ID | Defect | Owner | Phase | Status |
|----|--------|-------|-------|--------|
| FE-001 | Hooks not fully centralized on `browser-client.ts` | Agent 4 | 2 | **OPEN** |
| FE-002 | 15 stub routes beyond Core Daily Driver | Agents 5–9 | Post–v0.1 | **OPEN** |
| BE-001 | Pydantic v1 `@validator` deprecations | Agent 3 | Post–1 | **OPEN** (warnings only) |
| BE-002 | `_quarantine/` folder cleanup | Agent 11 | Post–1 | **OPEN** |
| BE-003 | Document text extraction placeholder | Agent 3 | 4+ | **OPEN** |
| DB-001 | pgTAP not in CI | Agent 2 / Agent 11 | Post–1 | **OPEN** |

---

## 5. Verification Matrix

Run from repo root unless noted. **PASS** = exit code 0 with criteria met.

| Gate | Command | PASS criteria | Prompt 1 result (2026-08-25) |
|------|---------|---------------|------------------------------|
| Backend pytest | `cd apps/api && python -m pytest tests/ -v` | 64 collected, 0 failed | **PASS** (64/64) |
| Ruff | `python -m ruff check apps/api` | 0 errors | **PASS** |
| Mypy | `python -m mypy apps/api/app` | 0 errors (113 files) | **PASS** |
| Frontend unit | `pnpm --filter @second-brain/web test` | 0 failed suites | **PASS** (14/14, 6 files) |
| Frontend typecheck | `pnpm --filter @second-brain/web typecheck` | `tsc --noEmit` clean | **PASS** |
| Frontend lint | `pnpm --filter @second-brain/web lint` | 0 ESLint errors | **PASS** |
| Frontend build | Env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_BASE_URL` → `pnpm --filter @second-brain/web build` | Next.js production build succeeds | **PASS** |
| Playwright E2E | `pnpm --filter @second-brain/web test:e2e` | Real auth fixture + visible DOM asserts | **BLOCKED** — do not fake PASS |
| Bandit | `bandit -r apps/api -x tests` | No high-severity issues | CI step (not re-run locally this session) |
| Manual Core CRUD | Browser against local stack | Create/edit/archive Venture, Project, Task, Person | **DEFERRED** → Prompt 2 |

### Prompt 2+ additional gates (future)

| Gate | Command / check | Owner |
|------|-----------------|-------|
| Core E2E | Playwright with Supabase test user fixture | Agent 12 |
| RAG real path | Integration test with mocked Gemini + real pgvector SQL | Agent 8 |
| Finalize MCP | MCP tool invocation with authz scopes | Agent 10 |
| Google honest | No `simulated_refresh_token` in grep; or env gate documents BLOCKED | Agent 7 |

---

## 6. Definition of “Fully Production Ready”

### Core Daily Driver v0.1 (minimum shippable)

- [ ] Authenticated session via Supabase SSR (login/logout)
- [ ] **Ventures:** list, create, edit, archive/delete, reload
- [ ] **Projects:** list, create, edit under venture, archive/delete
- [ ] **Tasks:** list, create, complete, edit, calendar metadata, reload
- [ ] **People:** list, create, edit, search, archive/delete
- [ ] All mutations via `apps/web/lib/api/browser-client.ts` — no ad-hoc `fetch` + token logic in hooks
- [ ] Data persists across logout/login (Supabase RLS scoped)
- [ ] Playwright E2E **GO** on above flows (Prompt 3)

### Personal daily driver release (Final Gate GO scope)

Everything in v0.1 plus:

- [ ] Real RAG retrieval scores (Prompt 4)
- [ ] `finalize_work_session` MCP write path (Prompt 5)
- [ ] Daily memory / evidence capture path (Prompt 6)
- [ ] Google: real integration **or** explicit **OAUTH BLOCKED** UI — never fake sync counts (Prompt 7)
- [ ] No P0 defects open; `integration_status.md` matches code
- [ ] Independent Final Gate signoff

### Full vision (post–v0.1)

- Portfolio / network intelligence UI
- Content engine, KPIs, achievements surfaces wired
- Live Google Contacts sync
- Knowledge graph UX
- PWA polish, deployment automation on Render/Vercel
- pgTAP + pgvector validated in CI against PostgreSQL

---

## 7. Fake / Broken Items to Eliminate

From [`docs/final-audit/`](../final-audit/) and [`integration_status.md`](../../integration_status.md). **Do not mark PASS until removed or honestly gated.**

| Item | Location | Fake behavior | Eliminate in |
|------|----------|---------------|--------------|
| Google OAuth | `apps/api/app/integrations/google_client.py` | `simulated_refresh_token`, fake email | Prompt 7 |
| Drive/Calendar sync | `apps/api/app/jobs/handlers/sync_google.py` | `synced_files_count: 14`, `events_synchronized: 5` | Prompt 7 |
| RAG confidence | `apps/api/app/ai/retrieval.py` | `score = 0.89` | Prompt 4 |
| Vector search fallback | `apps/api/app/repositories/knowledge.py` | ILIKE substring as “vector” search | Prompt 4 |
| AI provider simulation | `apps/api/app/ai/provider.py` | `[Simulated Gemini Output]` when keys missing | Prompt 4 (fail-closed OK in dev) |
| Dashboard insights | `apps/api/app/services/founder.py` | Hardcoded project names, velocity `1.24` | Prompt 4+ |
| Frontend toast stubs | `apps/web/app/(dashboard)/{ventures,projects,tasks,...}` | “Agent N will implement” | Prompt 2 (core four) / later |
| Document extraction | `document_processing.py` / extractor | Placeholder extracted text | Prompt 4+ |
| Vacuous E2E | `apps/web/e2e/essential-flows.spec.ts` | Was `toBeDefined()` | Prompt 3 (auth fixture) |
| False docs | README, old agent reports | “100% integrated”, wrong test counts | Ongoing (Agent 13) |
| Quarantine legacy | `apps/api/app/_quarantine/` | Orphan dashboard stub | Post–1 cleanup |

---

## 8. Merge / PR Strategy (8 local slices — no push)

Eight `pr/*` branches exist **locally and on origin** (pushed before user no-push rule). **Do not push further.**

| Slice branch | Approximate content | Merge order into `recovery/core-daily-driver` |
|--------------|---------------------|-----------------------------------------------|
| `pr/01-docs-audit-recovery` | `docs/final-audit/`, recovery docs | 1 — docs foundation |
| `pr/02-quarantine-stubs` | Delete/quarantine Agent 9 stubs | 2 — security |
| `pr/03-backend-domain` | Models, schemas, founder/knowledge/network services | 3 |
| `pr/04-mcp-ai` | MCP tools, AI provider, security | 4 |
| `pr/05-frontend-auth` | Supabase session, env fail-closed, hooks | 5 |
| `pr/06-frontend-shell` | Dashboard, capture, layout | 6 |
| `pr/07-ci-workspace` | CI workflow, pnpm/npmrc | 7 |
| `pr/08-test-harness` | pytest/conftest, vitest env, E2E assertion tighten | 8 |

**Current state:** These slices are **already consolidated** on `recovery/core-daily-driver` (~86 files vs `main`, +9835/−1811 lines). The slice branches are reference artifacts for review — **do not merge to `main` or push** until user approves.

**Recommended path when user allows push:**

1. Open **one** PR: `recovery/core-daily-driver` → `main` with link to this plan + `11_LOCAL_DIFF_REVIEW.md`.
2. Optional: keep slice branches for bisect only; no sequential PR merge needed if monolithic branch verified.
3. Final Gate runs on exact SHA tagged in PR.

---

## 9. Risk Register & ADHD Scope-Creep Guardrails

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep into RAG/Google during Prompt 2 | High | Delays daily driver | Phase map hard stops; document only |
| Believing Google sync works | High | Data loss trust | Prompt 7 honest BLOCKED UI; grep audits |
| Parallel agents reintroduce script damage | Medium | Broken contracts | Sequential rule; Prompt 1-style recovery only |
| MCP `tools.py` expansion without authz | Medium | Security | Prompt 5 gate; Agent 10 ownership |
| Frontend partial wiring (People only) | Medium | False “done” | Prompt 2 checklist all four domains |
| Builder-biased E2E | Medium | Fake GO | Fresh QA session Prompt 3 |
| Push to main before Final Gate | Low | Production incident | User no-push rule; branch protection |
| ADHD friction from over-building | High | Abandonment | v0.1 = 4 domains only; capture UX sacred |
| Schema drift SQLAlchemy ↔ migrations | Medium | Runtime errors | RT-004 before new migrations |
| Python 3.14 local vs CI 3.12 | Low | CI surprise | CI uses 3.12; local PASS on 3.14 noted |

### Scope-creep red flags (stop and document)

- New dashboard widgets not in Venture/Project/Task/People
- Wiring Ideas/KPIs/Achievements before Core Daily Driver PASS
- “Quick fix” to RAG or Google to demo something
- Adding migrations without Agent 2 review
- Replacing fail-closed env with mock defaults

---

## 10. Critical Path (ordered tasks — no time estimates)

1. ~~**Prompt 1:** Classify dirty tree, fix recovery defects, verify gates, `11_LOCAL_DIFF_REVIEW.md`~~ → **DONE** (READY FOR CORE FRONTEND)
2. **Prompt 2:** Wire Ventures, Projects, Tasks, People to `browser-client.ts`; remove stubs on those routes; manual CRUD smoke; `12_CORE_DAILY_DRIVER_FRONTEND.md`
3. **Prompt 3 (fresh QA):** Playwright Supabase auth fixture; real E2E for core four; `13_CORE_E2E_GATE.md` GO/NO-GO
4. **Prompt 4:** Remove `0.89`; real pgvector cosine scoring; fail-closed prod AI; `14_REAL_RAG_AI_CHAT.md`
5. **Prompt 5:** Productize `finalize_work_session`; MCP write tools with scopes; `15_FINALIZE_WORK_SESSION_MCP.md`
6. **Prompt 6:** Daily memory → evidence path; `16_DAILY_MEMORY_EVIDENCE.md`
7. **Prompt 7:** Real Google OAuth/API or documented OAUTH BLOCKED; `17_GOOGLE_WORKSPACE.md`
8. **Final Gate (fresh):** Re-run full verification matrix + manual matrix; `V01_RELEASE_GATE.md`
9. **User-approved push:** Single PR to `main`; deploy Render/Vercel with production secrets
10. **Post–v0.1:** Remaining stub routes, portfolio UI, pgTAP CI, quarantine deletion, Pydantic v2 migration

---

## Related documents

| Document | Purpose |
|----------|---------|
| [`00_MULTI_AGENT_ROLE_PLAN.md`](./00_MULTI_AGENT_ROLE_PLAN.md) | Agent roles and handoffs |
| [`11_LOCAL_DIFF_REVIEW.md`](./11_LOCAL_DIFF_REVIEW.md) | Prompt 1 exit report |
| [`RECOVERY_TASKS.md`](./RECOVERY_TASKS.md) | RT-001–RT-022 dependency graph |
| [`../final-audit/A_TO_Z_SYSTEM_AUDIT.md`](../final-audit/A_TO_Z_SYSTEM_AUDIT.md) | Independent A–Z audit |
| [`../../integration_status.md`](../../integration_status.md) | Live integration matrix |
| [`../orchestration/agent-ownership.md`](../orchestration/agent-ownership.md) | File ownership |

---

*Last verified: 2026-08-25 on `recovery/core-daily-driver` @ `6d47fdf`.*
