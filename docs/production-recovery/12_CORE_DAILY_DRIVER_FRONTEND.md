# 12 — Core Daily Driver Frontend (Prompt 2)

**Author:** Senior Next.js Product Integration Engineer  
**Date:** 2026-08-25  
**Branch:** `recovery/core-daily-driver`  
**Starting SHA:** `9480d631f6c677a4f518c3ef5b3c35acf1868d0e` (docs commit atop Prompt 1 @ `6d47fdfe268cd85685e5fc178b8d4e3c1139033d`)  
**Ending SHA:** `f6583b53f6dfae4a2c84913dc39b3a88c71a3ea1`  
**Plan:** [`MASTER_PRODUCTION_PLAN.md`](./MASTER_PRODUCTION_PLAN.md)

---

## Executive Summary

Prompt 2 productized the **Core Daily Driver v0.1** frontend for four domains: **Ventures**, **Projects**, **Tasks**, and **People**. All authenticated mutations and reads use the centralized `apps/web/lib/api/browser-client.ts` singleton (`api.get/post/patch/delete`) with Supabase session JWT injection. Stub toasts and demo/local-only data were removed from these routes.

**Verdict:** Implementation complete for Prompt 2 scope. Automated compile/test gates **PASS**. Manual browser CRUD **BLOCKED** (no verified local API + Supabase session in this session). **READY FOR INDEPENDENT E2E** (Prompt 3).

---

## Auth Architecture

| Layer | Implementation |
|-------|----------------|
| Session | Supabase SSR client (`createClient()` in browser) |
| Token | `session.access_token` attached as `Authorization: Bearer` |
| Client | `export const api = new FastApiClient(getToken, NEXT_PUBLIC_API_BASE_URL)` |
| Base URL | `NEXT_PUBLIC_API_BASE_URL` includes `/api/v1` — endpoints are **relative paths** (`/ventures`, `/people`, not `/api/v1/ventures`) |
| Errors | `ApiError` from `lib/api/errors.ts`; `formatApiError()` maps 401/404/422/500 to user-visible messages |
| Hooks | `useVentures`, `useProjects`, `useTasks`, `usePeople` — all call `api.*`; no ad-hoc `fetch` + `getSession` in core-four hooks |

---

## API Routes Consumed

### Ventures (`founder.py`)
| Method | Path | Used by |
|--------|------|---------|
| GET | `/ventures` | `useVentures` list |
| POST | `/ventures` | Create form |
| PATCH | `/ventures/{id}` | Inline edit |
| DELETE | `/ventures/{id}` | Archive confirm |

### Projects (`founder.py`)
| Method | Path | Used by |
|--------|------|---------|
| GET | `/projects?venture_id=` | `useProjects` list + filter |
| POST | `/projects` | Create form (optional `venture_id`) |
| PATCH | `/projects/{id}` | Inline edit |
| DELETE | `/projects/{id}` | Archive confirm |

### Tasks (`founder.py`)
| Method | Path | Used by |
|--------|------|---------|
| GET | `/tasks?status=` | `useTasks` + status filters |
| POST | `/tasks` | Quick input + Enter |
| PATCH | `/tasks/{id}` | Status cycle (todo → in_progress → done) |
| DELETE | `/tasks/{id}` | Delete confirm |

### People (`network.py`)
| Method | Path | Used by |
|--------|------|---------|
| GET | `/people` | `usePeople` list |
| POST | `/people` | Quick add + `/people/new` form |
| GET | `/people/{id}` | Detail page |
| PATCH | `/people/{id}` | Edit page |
| DELETE | `/people/{id}` | Archive confirm |

---

## Files Changed

| Path | Change |
|------|--------|
| `apps/web/lib/api/domains.ts` | **NEW** — shared domain types + `ListResponse<T>` |
| `apps/web/lib/api/format-error.ts` | **NEW** — user-visible API error formatting |
| `apps/web/hooks/useVentures.ts` | **NEW** |
| `apps/web/hooks/useProjects.ts` | **NEW** |
| `apps/web/hooks/useTasks.ts` | **NEW** |
| `apps/web/hooks/usePeople.ts` | Refactored to `browser-client.ts` |
| `apps/web/app/(dashboard)/ventures/page.tsx` | Full CRUD UI |
| `apps/web/app/(dashboard)/projects/page.tsx` | Full CRUD UI + venture filter |
| `apps/web/app/(dashboard)/tasks/page.tsx` | Quick capture, filters, status transitions |
| `apps/web/app/(dashboard)/people/page.tsx` | Real API list; removed demo contacts |
| `apps/web/app/(dashboard)/people/new/page.tsx` | Real create; no fake success on error |
| `apps/web/app/(dashboard)/people/[personId]/page.tsx` | `api` client; archive |
| `apps/web/app/(dashboard)/people/[personId]/edit/page.tsx` | **NEW** edit form |
| `apps/api/app/mcp/server.py` | Import order fix (ruff I001, pre-existing) |

---

## Per-Domain Status

| Domain | Status | Notes |
|--------|--------|-------|
| **Ventures** | **PASS** (code) / Manual **BLOCKED** | Inline create/edit, archive confirm, loading/empty/error/retry |
| **Projects** | **PASS** (code) / Manual **BLOCKED** | Venture dropdown from live ventures; filter by venture |
| **Tasks** | **PASS** (code) / Manual **BLOCKED** | Quick input + Enter; optional venture/project/priority/due; All/Todo/In Progress/Done filters |
| **People** | **PASS** (code) / Manual **BLOCKED** | Search (client-side), create, view, edit, archive; no raw UUID inputs |

---

## data-testid Attributes (Prompt 3)

| testid | Location |
|--------|----------|
| `venture-create` | Ventures page header button |
| `venture-list` | Ventures grid container |
| `venture-card` | Each venture card |
| `venture-edit` | Inline edit panel on card |
| `project-create` | Projects page header button |
| `project-list` | Projects grid container |
| `project-card` | Each project card |
| `task-quick-input` | Tasks quick capture input |
| `task-list` | Tasks list container |
| `task-row` | Each task row |
| `task-status` | Status toggle button |
| `person-create` | People page "New Contact" link |
| `people-search` | People search input |
| `person-card` | Each person card |
| `person-edit` | Detail edit link + edit page root |

---

## Manual Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Venture CRUD lifecycle | **BLOCKED** | No live FastAPI + Supabase auth session verified in this session |
| Project CRUD lifecycle | **BLOCKED** | Same |
| Task CRUD lifecycle | **BLOCKED** | Same |
| People CRUD lifecycle | **BLOCKED** | Same |
| Logout/login persistence | **BLOCKED** | Requires running stack + browser session |

`.env.local` exists but API/backend was not started and browser CRUD was not executed — no fake PASS recorded.

---

## Mobile Responsiveness (code review)

Layouts use `ResponsivePageContainer`, `min-h-[44px]` touch targets, stacked grids at `grid-cols-1`, filter pills with horizontal scroll, and `sm:`/`md:`/`lg:` breakpoints. Intended breakpoints: **375px** (single column), **768px** (2-col grids), **1440px** (3-col grids). Not visually verified in browser this session.

---

## Automated Verification (2026-08-25)

| Gate | Command | Result |
|------|---------|--------|
| Backend pytest | `cd apps/api && python -m pytest tests/ -v` | **64 passed**, 0 failed |
| Ruff | `python -m ruff check apps/api` | **PASS** (1 pre-existing I001 fixed in `mcp/server.py`) |
| Mypy | `python -m mypy apps/api/app` | **PASS** (113 files) |
| Frontend unit | `pnpm --filter @second-brain/web test` | **14 passed** (6 files) |
| Typecheck | `pnpm --filter @second-brain/web typecheck` | **PASS** |
| Lint | `pnpm --filter @second-brain/web lint` | **PASS** |
| Build | `pnpm --filter @second-brain/web build` (CI env vars) | **PASS** |

---

## Blockers

| ID | Blocker | Owner |
|----|---------|-------|
| MAN-001 | Manual CRUD not executed — local API stack not run in Prompt 2 session | Prompt 3 QA |
| E2E-001 | Playwright auth fixture still missing | Prompt 3 |

---

## Deferred (Out of Prompt 2 Scope)

- Google OAuth / sync (Prompt 7)
- RAG / AI chat real scores (Prompt 4)
- `finalize_work_session` MCP productization (Prompt 5)
- Daily Memory / Evidence (Prompt 6)
- Dashboard, KPIs, Ideas, Content, Meetings, Memories, Portfolio stub routes
- `useMeetings`, `useMemories`, `useQuickCapture` — still use relative `/api/v1/*` fetch (not core-four)
- Playwright E2E execution (Prompt 3)

---

## Prompt 2 Exit Report

```
PROMPT 2 COMPLETE

Branch: recovery/core-daily-driver
Starting SHA: 9480d631f6c677a4f518c3ef5b3c35acf1868d0e
Ending local SHA: f6583b53f6dfae4a2c84913dc39b3a88c71a3ea1

Ventures: PASS (code) — Manual BLOCKED
Projects: PASS (code) — Manual BLOCKED
Tasks: PASS (code) — Manual BLOCKED
People: PASS (code) — Manual BLOCKED

Backend tests: 64/64 PASS
Frontend unit: 14/14 PASS
Typecheck: PASS
Lint: PASS
Build: PASS

Manual CRUD: BLOCKED
Manual logout/login persistence: BLOCKED

Blocked: MAN-001, E2E-001
Deferred: See Deferred section above

CORE FRONTEND STATUS: READY FOR INDEPENDENT E2E

REMOTE ACTIONS: NONE
NO PUSH / NO PR / NO MERGE / NO DEPLOYMENT
```

---

*Prompt 3 may proceed with Playwright auth fixture + E2E against this SHA.*
