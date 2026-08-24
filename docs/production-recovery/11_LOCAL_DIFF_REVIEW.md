# 11 — Local Diff Review (Prompt 1)

**Author:** Principal Recovery Engineer / Git Release Manager  
**Date:** 2026-08-25  
**Branch:** `recovery/core-daily-driver`  
**Base:** local `main` @ `eec2e20` (1 commit ahead of `origin/main`, unpushed)  
**Remote:** `https://github.com/t4j44/mysecondbrain`  
**Plan:** [`00_MULTI_AGENT_ROLE_PLAN.md`](./00_MULTI_AGENT_ROLE_PLAN.md)

---

## Executive Verdict

Local tree contained substantial recovery/audit work not on GitHub `main` (~Aug 15 lineage). Prompt 1 classified every dirty path, fixed recovery defects only (Pydantic `dict` payloads, Meeting setter, fail-closed env refine, `useChat` Bearer auth, CI Python 3.12 + env for fail-closed build, E2E gated as BLOCKED), excluded scratch scripts, and structured commits.

**Prompt 2 was NOT started.**

---

## Classification Legend

| Class | Meaning |
|-------|---------|
| **KEEP** | Retain on recovery branch as intentional recovery foundation |
| **FIX BEFORE COMMIT** | Defect corrected during Prompt 1 |
| **REVERT** | Do not keep / delete from tree (scratch, accidental) |
| **DOCUMENTATION ONLY** | Docs/audit artifacts; no runtime effect |
| **TEST ONLY** | Test/CI harness changes |

---

## File-by-File Classification

### Documentation

| Path | Class | Notes |
|------|-------|-------|
| `docs/final-audit/**` | DOCUMENTATION ONLY | Independent A–Z audit, architecture, defect register |
| `docs/production-recovery/00_BASELINE_AUDIT.md` | DOCUMENTATION ONLY | Baseline NO-GO audit |
| `docs/production-recovery/00_MULTI_AGENT_ROLE_PLAN.md` | DOCUMENTATION ONLY | Sequential agent plan (this Prompt) |
| `docs/production-recovery/01_CI_REPORT.md` | DOCUMENTATION ONLY | Prior CI findings |
| `docs/production-recovery/02_BACKEND_DATABASE_AUTH_REPORT.md` | DOCUMENTATION ONLY | Auth/DB report |
| `docs/production-recovery/10_RELEASE_GATE.md` | DOCUMENTATION ONLY | Prior NO-GO gate |
| `docs/production-recovery/RECOVERY_TASKS.md` | DOCUMENTATION ONLY | Ordered recovery waves |
| `docs/production-recovery/11_LOCAL_DIFF_REVIEW.md` | DOCUMENTATION ONLY | This file |
| `integration_status.md` | KEEP | Honest status correction vs false “100% integrated” |

### Security quarantine (orphan Agent 9 stubs)

| Path | Class | Notes |
|------|-------|-------|
| `apps/api/app/api/v1/endpoints/achievements.py` (deleted) | KEEP | Unmounted hardcoded-UUID stubs removed from live tree |
| `apps/api/app/api/v1/endpoints/content.py` (deleted) | KEEP | Same |
| `apps/api/app/api/v1/endpoints/dashboard.py` (deleted) | KEEP | Quarantined copy retained under `_quarantine` |
| `apps/api/app/api/v1/endpoints/ideas.py` (deleted) | KEEP | Same |
| `apps/api/app/api/v1/endpoints/kpis.py` (deleted) | KEEP | Same |
| `apps/api/app/api/v1/endpoints/portfolio.py` (deleted) | KEEP | Same |
| `apps/api/app/repositories/{achievements,content,ideas,kpis,portfolio}.py` (deleted) | KEEP | Orphan Mock/Supabase-builder repos removed |
| `apps/api/app/_quarantine/**` | KEEP | Explicit quarantine; not mounted |
| `apps/api/tests/test_{achievements,content_engine,ideas,kpis,portfolio}_api.py` (deleted) | TEST ONLY | Tests only covered orphan stubs; deletion is consistent |

### Backend recovery / contracts

| Path | Class | Notes |
|------|-------|-------|
| `apps/api/app/models/entities.py` | KEEP + FIX | `VectorType`; WorkSession/Evidence/PortfolioEvidence/EntityEdge models; **added `participant_person_ids` setter** |
| `apps/api/app/api/v1/endpoints/founder.py` | FIX BEFORE COMMIT | Replaced `payload: dict` with `KPIUpdate` / `KPIEntryUpdate` |
| `apps/api/app/schemas/founder.py` | FIX BEFORE COMMIT | Added `KPIEntryUpdate` |
| `apps/api/app/schemas/__init__.py` | KEEP + FIX | Export `KPIEntryUpdate` |
| `apps/api/app/services/founder.py` | KEEP | KPI update/delete service methods |
| `apps/api/app/services/knowledge.py` | KEEP | Memory/Idea/Decision/Document CRUD completeness; flush-before-job |
| `apps/api/app/services/network.py` | KEEP | Network service completeness |
| `apps/api/app/api/v1/endpoints/knowledge.py` | KEEP | Memory update + related routes with Pydantic |
| `apps/api/app/api/v1/endpoints/network.py` | KEEP | Network route completeness |
| `apps/api/app/api/v1/endpoints/ai_portfolio.py` | KEEP | Present; **productization deferred** (not Prompt 2) |
| `apps/api/app/schemas/portfolio.py` | KEEP | Schema expansion; product UI deferred |
| `apps/api/app/ai/provider.py` | KEEP | Fail-closed production; deterministic offline embeddings |
| `apps/api/app/integrations/storage_client.py` | KEEP | Storage client hygiene |
| `apps/api/app/mcp/security.py` | KEEP | MCP security hardening |
| `apps/api/app/mcp/tools.py` | KEEP (scope caution) | Large expansion; **finalize_work_session productization is Prompt 5** — do not expand further in Prompt 2 |
| `apps/api/app/services/document_extractor.py` | KEEP | Supporting extract utility |
| `apps/api/pyproject.toml` / `requirements.txt` / `uv.lock` | KEEP | Dep/lock alignment |
| `supabase/migrations/20260811000017_create_evidence_and_portfolio_graph_tables.sql` | KEEP | Schema for later evidence/portfolio phases |

### Frontend auth / env / CI

| Path | Class | Notes |
|------|-------|-------|
| `apps/web/hooks/usePeople.ts` | KEEP | Replaced `localStorage` token with Supabase SSR session |
| `apps/web/hooks/useMeetings.ts` | KEEP | Same |
| `apps/web/hooks/useMemories.ts` | KEEP | Same |
| `apps/web/hooks/useChat.ts` | FIX BEFORE COMMIT | Added Bearer from Supabase session (was missing) |
| `apps/web/app/(dashboard)/people/**` | KEEP | Auth fix + people UI work mixed in; Prompt 2 owns full Core Daily Driver polish |
| `apps/web/app/(dashboard)/memories/new/page.tsx` | KEEP | Auth fix |
| `apps/web/app/(dashboard)/meetings/[meetingId]/page.tsx` | KEEP | Auth fix |
| `apps/web/lib/env.ts` | KEEP + FIX | Fail-closed URLs; refine requires publishable/anon key |
| `apps/web/lib/supabase/{client,server,middleware}.ts` | KEEP | Non-null anon key after fail-closed transform |
| `apps/web/e2e/essential-flows.spec.ts` | TEST ONLY | Replaced vacuous `toBeDefined()` with `toBeVisible()`; **auth fixture still missing → Playwright BLOCKED** |
| `.github/workflows/security_ci.yml` | TEST ONLY / FIX | Python 3.12; PYTHONPATH; frontend env for fail-closed; filter `@second-brain/web`; E2E step documents BLOCKED |
| `package.json` | KEEP | Moved build-deps policy to `.npmrc` / workspace |
| `pnpm-workspace.yaml` | KEEP | `allowBuilds` list form |
| `.npmrc` | KEEP | `only-built-dependencies=esbuild,unrs-resolver` |

### Frontend shell / premature product surfaces (present, do not expand in Prompt 1)

| Path | Class | Notes |
|------|-------|-------|
| `apps/web/app/(dashboard)/dashboard/page.tsx` | KEEP (caution) | Large dashboard rewrite — not Core Daily Driver CRUD; Prompt 2 must not treat as done |
| `apps/web/components/layout/**` | KEEP (caution) | Shell/sidebar/mobile bar changes |
| `apps/web/components/capture/**` | KEEP (caution) | ADHD capture UI — verify in later prompts; out of Prompt 1 scope |
| `apps/web/components/session/**` | KEEP (caution) | Work session UI → Prompt 5 |
| `apps/web/hooks/useQuickCapture.ts` | KEEP (caution) | Same |

### Scratch / accidental — DO NOT COMMIT

| Path | Class | Notes |
|------|-------|-------|
| `fix_auth.py` | REVERT | Automated bulk auth rewriter — **deleted from tree** |
| `fix_imports.py` | REVERT | Automated import injector — **deleted from tree** |

---

## High-Risk Automated Edit Findings

| Finding | Severity | Disposition |
|---------|----------|-------------|
| `founder.py` KPI routes used `payload: dict` | P1 contract | **FIXED** → Pydantic `KPIUpdate` / `KPIEntryUpdate` |
| `Meeting.participant_person_ids` property without setter | P1 ORM | **FIXED** |
| Hooks + pages used `localStorage.getItem('supabase_session_token')` | P0 auth | **FIXED** (script-driven; manually reviewed) |
| `useChat.ts` had no Bearer auth | P0 auth | **FIXED** |
| `env.ts` mock defaults → fail-closed | P0 hygiene | **KEEP**; refine added so missing keys fail closed |
| CI would run Playwright without auth fixture / wrong filter risk | P1 CI | **FIXED** — E2E gated as BLOCKED status step |
| Orphan hardcoded-UUID endpoints | P0 security | **KEEP** deletion + quarantine |
| Deleted stub API tests without replacements | Expected | **KEEP** — stubs gone |
| `mcp/tools.py` +1150 LOC | Scope risk | KEEP tree; **no Prompt 5 product claim** |
| Dashboard/people large UI diffs | Scope risk | KEEP for compile continuity; Prompt 2 owns Ventures/Projects/Tasks/People gate |
| Duplicate OpenAI provider removed from `provider.py` | Intentional | KEEP — factory returns Gemini only; docs mention OpenAI historically |

---

## Prompt 1 Fixes Applied (Allowed Scope Only)

1. Pydantic KPI update/entry contracts in `founder.py` + `KPIEntryUpdate` schema  
2. `Meeting.participant_person_ids` setter  
3. `useChat` Supabase session Bearer header  
4. `env.ts` refine requiring publishable or anon key  
5. CI: Python 3.12, frontend mock env for fail-closed build, correct package filter, Playwright marked BLOCKED  
6. Deleted scratch `fix_auth.py` / `fix_imports.py`

**Not done (explicitly deferred):** Prompt 2 Core Daily Driver frontend implementation; real RAG productization; finalize_work_session productization; live Google; portfolio UI.

---

| Backend pytest | `python -m pytest apps/api/tests/ -v` | **64 passed / 0 failed** |
| Ruff | `ruff check apps/api` | **PASS** |
| Mypy | `mypy apps/api/app` | **PASS** (113 files) |
| Frontend unit | `pnpm --filter @second-brain/web test` | **14 passed / 0 failed** (6 files) |
| Frontend typecheck | `pnpm --filter @second-brain/web typecheck` | **PASS** |
| Frontend lint | `pnpm --filter @second-brain/web lint` | **PASS** |
| Frontend build | `pnpm --filter @second-brain/web build` | **PASS** |
| Playwright | auth fixture | **BLOCKED** (no verified auth fixture; CI documents deferral to Prompt 3) |

---

## Prompt 1 Exit Report

```
BRANCH: recovery/core-daily-driver
COMMIT SHA: 368e507f2994b11b9505de6101046e4bd072245e
FILES CHANGED: ~80+ (57 tracked modifications + 30 untracked additions − scratch scripts)
TESTS PASSED: Backend 64/64; Frontend unit 14/14; Ruff PASS; Mypy PASS; Typecheck PASS; Lint PASS; Build PASS
TESTS FAILED: 0
TESTS BLOCKED: Playwright E2E (no auth fixture)

RECOVERY BRANCH STATUS: READY FOR CORE FRONTEND
```

**Prompt 2 may proceed** on this branch. Playwright gate remains **Prompt 3** with a fresh QA session.

**Known deferred (not Prompt 1 blockers):**
- Ventures/Projects/Tasks UI may still be stub/minimal — Prompt 2 owns wiring
- RAG hardcoded scores / simulated Google — Prompts 4–7
- `finalize_work_session` productization — Prompt 5
