# Pre-G3 Real Supabase Auth + RLS Smoke

**Date:** 2026-09-06  
**Workspace:** `E:\second brain`  
**Scope:** Local Next.js + local FastAPI against non-production Supabase staging  
**Auth mode:** Real Supabase Auth required (no mock)  
**Database:** Real PostgreSQL + RLS required (no SQLite as proof)  
**Production access:** Not used  
**Deployment/push:** Not performed

## Final verdict

| Gate | Result |
|---|---|
| REAL SUPABASE AUTH | **FAIL** |
| REAL RLS ISOLATION | **FAIL** |
| PRE-G3 PRODUCT | **FAIL** |

# PRE-G3 REAL SUPABASE SMOKE: **FAIL**

Blocked at preflight. The mission precondition (“ignored env files are populated”)
is **false** in this workspace. No staging database URL, Supabase API credentials,
or User A/B Auth passwords are available on disk or in the process environment.
No product, auth, RLS, or mobile flow was executed.

SQLite was not used as proof. Production was not contacted. No deployment was
attempted. No secrets were invented.

---

## 1. Database initialization

| Check | Result | Evidence |
|---|---|---|
| Load `apps/api/.env` | **FAIL** | File does not exist |
| Set `POSTGRES_TEST_DATABASE_URL` from staging | **FAIL** | No staging DSN available |
| `python scripts/db/bootstrap_migrations.py` | **FAIL** | Exit 1 — `POSTGRES_TEST_DATABASE_URL is not set` |
| `python scripts/db/check_type_drift.py` | **FAIL** | Exit 2 — `POSTGRES_TEST_DATABASE_URL is not set` |
| COLUMNS MISSING FROM THE DATABASE: 0 | **FAIL** | Not run |
| TYPE MISMATCHES: 0 | **FAIL** | Not run |
| ENUM VALUE MISMATCHES: 0 | **FAIL** | Not run |
| CLEAN: ORM matches the migrated schema | **FAIL** | Not run |

Exact bootstrap stderr:

```text
POSTGRES_TEST_DATABASE_URL is not set. Configure a separate development/staging
PostgreSQL or Supabase project (see docs/production-recovery/G1_DATABASE_SCHEMA_GATE.md).
```

Exact drift stderr:

```text
POSTGRES_TEST_DATABASE_URL is not set. Point it at a migrated dev database.
```

---

## 2. Backend (FastAPI 127.0.0.1:8000)

| Check | Result | Evidence |
|---|---|---|
| Start FastAPI on 127.0.0.1:8000 | **FAIL** | No `apps/api/.env` / `DATABASE_URL` |
| `GET /health/live` = 200 | **FAIL** | Not started |
| `GET /health/ready` = 200 (DB connected) | **FAIL** | Not started |

---

## 3. Frontend (Next.js localhost:3000)

| Check | Result | Evidence |
|---|---|---|
| Start Next.js on localhost:3000 | **FAIL** | Staging Supabase public config missing |
| Staging `NEXT_PUBLIC_SUPABASE_URL` | **FAIL** | Absent from `apps/web/.env.local` |
| Staging `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | **FAIL** | Absent from `apps/web/.env.local` |

Observed `apps/web/.env.local` (non-secret values only):

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_SITE_URL=http://127.0.0.1:3000
```

---

## 4. Auth (User A)

| Flow | Result | Evidence |
|---|---|---|
| Login | **FAIL** | No User A credentials; no Supabase Auth config |
| Refresh — still logged in | **FAIL** | Not executed |
| Logout | **FAIL** | Not executed |
| Login again | **FAIL** | Not executed |
| Auth area | **FAIL** | — |

---

## 5. User A product flows

### Venture

| Flow | Result |
|---|---|
| create | **FAIL** |
| list | **FAIL** |
| read | **FAIL** |
| edit | **FAIL** |
| reload | **FAIL** |

### Project

| Flow | Result |
|---|---|
| create under Venture | **FAIL** |
| list | **FAIL** |
| read | **FAIL** |
| edit | **FAIL** |
| reload | **FAIL** |

### Task

| Flow | Result |
|---|---|
| create under Project | **FAIL** |
| todo → in_progress | **FAIL** |
| reload | **FAIL** |
| in_progress → done | **FAIL** |
| reload | **FAIL** |

### Person

| Flow | Result |
|---|---|
| create | **FAIL** |
| list/search | **FAIL** |
| read | **FAIL** |
| edit | **FAIL** |
| reload | **FAIL** |

Persistence overall: **FAIL** (not executed).

---

## 6. User B isolation (RLS)

| Check | Result | Evidence |
|---|---|---|
| Login User B | **FAIL** | `apps/web/e2e/.env.local` missing; no `E2E_EMAIL_B` / `E2E_PASSWORD_B` |
| B cannot list A’s data | **FAIL** | Not executed |
| B cannot read A Venture by id | **FAIL** | Not executed |
| B cannot update A Venture | **FAIL** | Not executed |
| B cannot delete A Venture | **FAIL** | Not executed |
| Same for Project | **FAIL** | Not executed |
| Same for Task | **FAIL** | Not executed |
| Same for Person | **FAIL** | Not executed |

Expected safe denial (404/403) was not observed because no second session was
possible. No User A content was exposed (no product session ran).

---

## 7. Mobile (~390×844)

| Check | Result | Evidence |
|---|---|---|
| Primary navigation usable | **FAIL** | App not started |
| Venture / Project / Task / Person | **FAIL** | Not executed |
| Login / logout | **FAIL** | Not executed |

---

## Preflight inventory (no secret values)

| Artifact | Present? | Notes |
|---|---|---|
| `apps/api/.env` | **NO** | Templates only: `.env.example`, `docs/production-recovery/preflight/api.env.template` |
| `apps/web/.env.local` | **YES** | Local API URL only; no Supabase public keys |
| `apps/web/e2e/.env.local` | **NO** | Templates only: `.env.example`, `.env.local.example`, preflight template |
| Process/User/Machine: `DATABASE_URL` | **MISSING** | |
| Process/User/Machine: `POSTGRES_TEST_DATABASE_URL` | **MISSING** | |
| Process/User/Machine: `SUPABASE_URL` | **MISSING** | |
| Process/User/Machine: `SUPABASE_SECRET_KEY` | **MISSING** | |
| Process/User/Machine: `E2E_EMAIL` / `E2E_PASSWORD` | **MISSING** | |
| Process/User/Machine: `E2E_EMAIL_B` / `E2E_PASSWORD_B` | **MISSING** | |
| SQLite used as proof | **NO** | |
| Production used | **NO** | |

---

## Required before rerun

Populate the three gitignored files from the preflight templates (staging only):

1. `docs/production-recovery/preflight/api.env.template` → `apps/api/.env`  
   Include `DATABASE_URL`, `POSTGRES_TEST_DATABASE_URL` (same staging DB),
   `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `APP_ENV=staging`,
   `ENVIRONMENT=staging`, `DATABASE_SCHEMA_VERIFY=true`, plus local JWT secrets.
2. `docs/production-recovery/preflight/web.env.local.template` → `apps/web/.env.local`  
   Include `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
3. `docs/production-recovery/preflight/e2e.env.local.template` → `apps/web/e2e/.env.local`  
   User A and User B staging Auth credentials.

Then rerun this exact mission. Do not point any of the above at production.
Do not deploy until this smoke scores PASS.
