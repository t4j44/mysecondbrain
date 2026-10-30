# 13A — Local E2E Environment Preflight

**Date:** 2026-08-25 (Prompt 3A re-run — independent verify after user claimed env files exist)  
**Mission:** Unblock Prompt 3 by making the local stack bootable for authenticated Playwright E2E.  
**Scope:** Environment / infrastructure only. No product logic changes. No remote actions.

## Identity

| Field | Value |
| --- | --- |
| Branch | `recovery/core-daily-driver` |
| SHA | `143eda9ad1cf5042b51058264456436f0d5cb1b7` |
| Verdict | **LOCAL E2E ENVIRONMENT: BLOCKED** |

## Independent verification note

User claimed required env files physically exist with key names present.

**Independent check under `E:\second brain` (no values printed):** claim **not** satisfied.

| Path | On-disk |
| --- | --- |
| `apps/web/.env.local` | EXISTS (129 bytes) — Supabase URL/key keys **not** present |
| `apps/web/e2e/.env.local` | **ABSENT** |
| `apps/api/.env` | **ABSENT** |

Only env-like files found under `apps/`: `.env.example` files + `apps/web/.env.local`.

## Dirty working tree (classified)

**QA harness (OK to remain — do not discard):**

- `.gitignore` (modified)
- `apps/web/playwright.config.ts` (modified)
- `apps/web/tsconfig.json` (modified)
- `apps/web/e2e/essential-flows.spec.ts` (deleted — replaced by new specs)
- Untracked: `apps/web/e2e/.env.example`, `auth.setup.ts`, `core-lifecycle.spec.ts`, `cross-tenant.spec.ts`, `helpers/`, `negative.authenticated.spec.ts`, `unauthenticated.spec.ts`
- Untracked: `docs/production-recovery/13_CORE_E2E_GATE.md`
- This file: `docs/production-recovery/13A_LOCAL_E2E_ENVIRONMENT.md`

**App product logic:** none in dirty set.

**Secret files:** not committed; paths checked via `git check-ignore`.

## Phase results

### Gitignore — PASS

| Path | Ignored |
| --- | --- |
| `apps/web/.env.local` | yes (`**/.env.*`) |
| `apps/web/e2e/.env.local` | yes (`**/.env.*`) |
| `apps/web/e2e/.auth/` | yes (`**/e2e/.auth/`) |
| `apps/api/.env` | yes (`**/.env`) |

### Backend settings inspection (code)

**Source of truth:** `apps/api/app/config.py` (re-exported via `apps/api/app/core/config.py`).  
**Auth:** JWKS derived from `SUPABASE_URL` (or `SUPABASE_JWKS_URL`); optional HS256 via `SUPABASE_JWT_SECRET` / non-prod `JWT_SECRET`.  
**Boot:** non-production accepts SQLite default when `DATABASE_URL` unset.

**STOP rule for Prompt 3A:** authenticated local E2E requires at least `SUPABASE_URL` in `apps/api/.env` (or process env). That var is **MISSING** → backend gate fails → FastAPI/Next **not** started; smokes **not** run.

### Backend env — BLOCKED

File `apps/api/.env`: **does not exist**. Process env for the same keys: all **MISSING**.

| Variable | Presence |
| --- | --- |
| `SUPABASE_URL` | MISSING |
| `SUPABASE_SECRET_KEY` | MISSING |
| `SUPABASE_SERVICE_ROLE_KEY` | MISSING |
| `SUPABASE_JWKS_URL` | MISSING |
| `SUPABASE_JWT_SECRET` | MISSING |
| `DATABASE_URL` | MISSING (code default would apply if started) |
| `JWT_SECRET` | MISSING (code default would apply) |
| `TOKEN_ENCRYPTION_KEY` | MISSING (code default would apply) |
| `APP_ENV` | MISSING |
| `ENVIRONMENT` | MISSING |
| `FRONTEND_URL` | MISSING |
| `GEMINI_API_KEY` | MISSING |
| `CORS_ORIGINS` | MISSING |

**Add to `apps/api/.env` (do not invent values; do not commit):**

1. `SUPABASE_URL` — same Project URL as web `NEXT_PUBLIC_SUPABASE_URL`.
2. Recommended: `SUPABASE_SECRET_KEY` (or legacy `SUPABASE_SERVICE_ROLE_KEY`).
3. Recommended local: `APP_ENV=development`, `ENVIRONMENT=development`, `FRONTEND_URL=http://localhost:3000`.
4. Optional: omit `DATABASE_URL` to use local SQLite default for non-prod.

### Web env — BLOCKED

File `apps/web/.env.local` **exists**. Key names present only: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV`, `NEXT_PUBLIC_SITE_URL`.

| Variable | Presence |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | SET |
| `NEXT_PUBLIC_SITE_URL` | SET |
| `NEXT_PUBLIC_APP_ENV` | SET |
| `NEXT_PUBLIC_SUPABASE_URL` | **MISSING** |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | **MISSING** |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **MISSING** |

`hasSupabasePublicConfig=false`.

### E2E primary — BLOCKED

File `apps/web/e2e/.env.local`: **does not exist**.  
Also not present in `apps/web/.env.local` or process env.

| Variable | Presence |
| --- | --- |
| `E2E_EMAIL` | MISSING |
| `E2E_PASSWORD` | MISSING |

`hasAuth=false`.

### E2E second user — OPTIONAL MISSING

| Variable | Presence |
| --- | --- |
| `E2E_EMAIL_B` | MISSING |
| `E2E_PASSWORD_B` | MISSING |

Needed only for cross-tenant specs; does not alone define READY.

### FastAPI — BLOCKED (not started)

Skipped per Prompt 3A STOP: backend `SUPABASE_URL` MISSING.  
Ports: `8000` FREE. Health probes not run.

### Next.js — BLOCKED (not started)

Skipped: Supabase public config missing; backend gate failed.  
Ports: `3000` FREE. `/login` not verified.

### Auth smoke — BLOCKED

Not attempted (missing E2E credentials + servers not started).

### API smoke — BLOCKED

Not attempted (`GET /ventures` requires auth + running API).

### Playwright discovery — PASS (count only)

`pnpm --filter @second-brain/web exec playwright test --list` → **Total: 20 tests in 4 files** (> 0).  
Harness flags: `hasAuth=false`, `hasSupabasePublicConfig=false`.

Full Prompt 3 lifecycle suite **not** executed.

## Servers left running

**None.** FastAPI and Next.js were not started. Ports 8000 and 3000 free.

## READY gate checklist

| Gate | Status |
| --- | --- |
| Secret files ignored | PASS |
| Supabase URL + key present (web) | FAIL |
| E2E_EMAIL + E2E_PASSWORD present | FAIL |
| Backend env present (`SUPABASE_URL` at minimum) | FAIL |
| FastAPI `/health/live` 200 | FAIL (not started) |
| Next `/login` loads | FAIL (not started) |
| Auth smoke succeeds | FAIL |
| Authenticated API read succeeds | FAIL |
| Playwright discovers tests (> 0) | PASS (20) |
| hasAuth=true | FAIL |
| hasSupabasePublicConfig=true | FAIL |

## Exact remaining prerequisites (BLOCKED)

1. **`apps/web/.env.local`** — add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` **or** `NEXT_PUBLIC_SUPABASE_ANON_KEY` (real values; do not invent).
2. **`apps/web/e2e/.env.local`** — create file; set `E2E_EMAIL` and `E2E_PASSWORD` for a real Supabase Auth test user.
3. **`apps/api/.env`** — create file; set at least `SUPABASE_URL` (same project as web). Recommended: `SUPABASE_SECRET_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`), `APP_ENV=development`, `ENVIRONMENT=development`, `FRONTEND_URL=http://localhost:3000`.

Then re-run Prompt 3A only (start FastAPI + Next, auth/API smoke, re-check harness flags).

Optional: `E2E_EMAIL_B` / `E2E_PASSWORD_B` for cross-tenant specs.

## Remote actions

**NONE** — no push, PR, merge, deploy, or production migrations.
