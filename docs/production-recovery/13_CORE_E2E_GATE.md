# 13 — Core Daily Driver E2E Gate (Prompt 3)

**Role:** Independent Senior QA Automation Engineer / Core Daily Driver Gatekeeper  
**Date:** 2026-08-25 (continuation — user claimed local env configured; independently re-verified)  
**Branch:** `recovery/core-daily-driver`  
**SHA tested:** `143eda9ad1cf5042b51058264456436f0d5cb1b7`  
**Expected Prompt 2 HEAD:** `143eda9ad1cf5042b51058264456436f0d5cb1b7` — **MATCH**  
**Builder report:** `docs/production-recovery/12_CORE_DAILY_DRIVER_FRONTEND.md` (distrusted; see discrepancies)  
**Remote actions:** **NONE** (no push, PR, merge, deploy)

---

## Verdict

# CORE DAILY DRIVER E2E: **BLOCKED**

GO requires all four real authenticated lifecycle tests to **PASS** in a browser. They did not run. They were **skipped**, not passed. Credentials and a bootable local web env were not invented.

User asserted local env is now manually configured. **Independent re-verify contradicts that claim.** Exact missing items are listed under External prerequisites.

Prompt 4 must **not** start until this gate is **GO**.

---

## Phase 0 — Independent verify (this continuation)


| Check                                   | Result                                                                                                                                                                                  |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git branch --show-current`             | `recovery/core-daily-driver`                                                                                                                                                            |
| `git rev-parse HEAD`                    | `143eda9ad1cf5042b51058264456436f0d5cb1b7`                                                                                                                                              |
| `git status`                            | Dirty **QA harness + gate doc only** (no product app logic edits this session). Uncommitted: Playwright e2e specs/helpers/config, `13_CORE_E2E_GATE.md`, `.gitignore`, `tsconfig.json`. |
| `GET http://127.0.0.1:8000/health/live` | **FAIL** — Unable to connect to the remote server                                                                                                                                       |
| TCP `127.0.0.1:8000`                    | **closed**                                                                                                                                                                              |
| TCP `127.0.0.1:3000`                    | **closed**                                                                                                                                                                              |
| Frontend `/login` bootable              | **NO** — `http://localhost:3000/login` unreachable; Playwright `webServer` gated off when Supabase public env absent                                                                     |


### Env presence (boolean only; values never printed)

Checked: process env + `apps/web/.env.local` + `apps/web/e2e/.env.local` + `apps/web/e2e/.env` + repo-root `.env.local` / `.env`.


| Variable                               | Set?                                                                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------------- |
| `E2E_EMAIL`                            | **false**                                                                                     |
| `E2E_PASSWORD`                         | **false**                                                                                     |
| `NEXT_PUBLIC_SUPABASE_URL`             | **false**                                                                                     |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | **false**                                                                                     |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`        | **false**                                                                                     |
| publishable **OR** anon key            | **false**                                                                                     |
| `NEXT_PUBLIC_API_BASE_URL`             | **true** (file only: `apps/web/.env.local`; insufficient alone)                               |
| `E2E_EMAIL_B`                          | **false** (optional)                                                                          |
| `E2E_PASSWORD_B`                       | **false** (optional)                                                                          |


`apps/web/.env.local` key names present (values not logged): `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV`, `NEXT_PUBLIC_SITE_URL` only.  
`apps/web/e2e/.env.local` — **does not exist**.  
Harness loads credentials from env or gitignored `e2e/.env.local` / `apps/web/.env.local` via `e2e/helpers/credentials.ts`.

---

## Builder-report discrepancies (do not trust Prompt 2 docs)


| Claim in `12_CORE_DAILY_DRIVER_FRONTEND.md`           | Independent finding                                                                    |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Ending SHA `f6583b53f6dfae4a2c84913dc39b3a88c71a3ea1` | HEAD is `143eda9ad1cf5042b51058264456436f0d5cb1b7`                                     |
| Manual CRUD **BLOCKED** (no live stack)               | **Still confirmed** on re-verify: API down; Supabase public env unset; E2E creds unset |
| `data-testid` attributes present on core-four UI      | **Confirmed in source** (prior session; not re-proven in browser)                      |
| Core-four pages are not toast stubs                   | **Code review only.** **Not proven in a browser session.**                             |
| READY FOR INDEPENDENT E2E                             | Harness exists. **Execution remains BLOCKED**                                          |


---

## Auth method and fixtures


| Item              | Status                                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Method            | Playwright `e2e/auth.setup.ts`: UI login (`/login` email + password) → `storageState` at `e2e/.auth/user.json` (gitignored) |
| Credential source | `E2E_EMAIL` / `E2E_PASSWORD` from environment or gitignored `e2e/.env.local` / `apps/web/.env.local`                        |
| Second user       | `E2E_EMAIL_B` / `E2E_PASSWORD_B`                                                                                            |
| Secrets committed | **No**                                                                                                                      |
| Fixture executed  | **No** — primary E2E user unset                                                                                             |
| Auth bypass       | **None**                                                                                                                    |


Template (no secrets): `apps/web/e2e/.env.example`

---

## Browsers and viewports


| Project           | Browser                   | Viewport                          | Result this run                                         |
| ----------------- | ------------------------- | --------------------------------- | ------------------------------------------------------- |
| `unauthenticated` | Chromium (Desktop Chrome) | **1440×900**                      | 3 skipped (cannot boot web without Supabase public env) |
| `chromium`        | Chromium                  | **1440×900**                      | 9 skipped                                               |
| `mobile-chrome`   | Chromium Pixel 5          | **393×727** (device preset)       | 8 skipped                                               |
| Tablet **768**    | —                         | Not a separate Playwright project | **Not executed**                                        |


`setup` project not registered this run (`hasAuth === false`).

---

## Exact command results (this continuation)

### Playwright — `pnpm --filter @second-brain/web test:e2e`


| Metric     | Count                             |
| ---------- | --------------------------------- |
| Discovered | **20**                            |
| Passed     | **0**                             |
| Failed     | **0**                             |
| Skipped    | **20**                            |
| Blocked    | **20** (env/stack; not executed)  |
| Exit code  | **0** (all skipped; **not a GO**) |


Breakdown:


| Spec                                     | Intent                                                            | Chromium | Mobile         | Unauth project |
| ---------------------------------------- | ----------------------------------------------------------------- | -------- | -------------- | -------------- |
| FLOW 1 Venture lifecycle                 | Create / visible / reload / edit / logout-login persist / archive | skipped  | skipped        | —              |
| FLOW 2 Project lifecycle                 | Venture link / reload / edit / persist / archive                  | skipped  | skipped        | —              |
| FLOW 3 Task lifecycle                    | Task→project→venture, todo→in_progress→done, persist, delete      | skipped  | skipped        | —              |
| FLOW 4 Person lifecycle                  | Create / search / detail / edit / persist / archive               | skipped  | skipped        | —              |
| Unauth protected `/ventures` → `/login`  | Negative                                                          | —        | —              | skipped        |
| Login validation (invalid email)         | Negative                                                          | —        | —              | skipped        |
| Login controls visible                   | Smoke                                                             | —        | —              | skipped        |
| Invalid person UUID error UI             | Negative                                                          | skipped  | skipped        | —              |
| People name required                     | Form validation                                                   | skipped  | skipped        | —              |
| Intercepted GET `/ventures` 500 error UI | API error UI                                                      | skipped  | skipped        | —              |
| People search empty/no-match             | Empty state                                                       | skipped  | skipped        | —              |
| User B cannot see User A venture         | Cross-tenant                                                      | skipped  | not in project | —              |


Skip reason: harness refuses to invent env / credentials (`getPrimaryE2EUser()` null and/or `hasSupabasePublicConfig()` false → no `webServer`, authenticated projects have no storageState setup).

### Other gates (same machine, this continuation)


| Command                                     | Result                                       |
| ------------------------------------------- | -------------------------------------------- |
| `pnpm --filter @second-brain/web test`      | **14 passed**, 0 failed (6 files) — exit 0   |
| `pnpm --filter @second-brain/web typecheck` | **PASS** (`tsc --noEmit`) — exit 0           |
| `pnpm --filter @second-brain/web lint`      | **PASS** (0 ESLint warnings/errors) — exit 0 |


These do **not** satisfy Core Daily Driver E2E GO.

---

## Per-domain status


| Domain                | Status      | Evidence                                                                                                             |
| --------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------- |
| Venture               | **BLOCKED** | FLOW 1 not executed                                                                                                  |
| Project               | **BLOCKED** | FLOW 2 not executed                                                                                                  |
| Task                  | **BLOCKED** | FLOW 3 not executed                                                                                                  |
| Person                | **BLOCKED** | FLOW 4 not executed                                                                                                  |
| Unauthenticated guard | **BLOCKED** | Next cannot boot without Supabase public env; unauth specs skipped                                                   |
| Form validation       | **BLOCKED** | Login/people specs not executed against a live page                                                                  |
| API error UI          | **BLOCKED** | Intercept spec not executed                                                                                          |
| Empty states          | **BLOCKED** | Search empty-state spec not executed                                                                                 |
| Cross-tenant / RLS    | **BLOCKED** | `E2E_EMAIL_B` / `E2E_PASSWORD_B` unset; isolation alone would not block GO of four lifecycles if primary env existed |


---

## External prerequisites (exact missing)

Re-run is blocked until **all required** items below exist on this machine. QA will not invent them.

1. **`E2E_EMAIL`** — **MISSING**
2. **`E2E_PASSWORD`** — **MISSING**
3. **`NEXT_PUBLIC_SUPABASE_URL`** — **MISSING**
4. **`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` or `NEXT_PUBLIC_SUPABASE_ANON_KEY`** — **MISSING** (both false)
5. **FastAPI on `127.0.0.1:8000`** — **MISSING** (`/health/live` unreachable; port closed)
6. **Bootable Next on Playwright baseURL (`http://localhost:3000`)** — **MISSING** (port closed; `/login` unreachable; webServer gated off without Supabase public config)

Optional (cross-tenant only; does **not** alone block FLOW 1–4 GO):

1. **`E2E_EMAIL_B` / `E2E_PASSWORD_B`** — **MISSING** → cross-tenant stays **BLOCKED**

Place secrets in shell env or gitignored `apps/web/e2e/.env.local` (and Supabase public keys in `apps/web/.env.local`). Do not commit.

After those are present:

```
pnpm --filter @second-brain/web test:e2e
```

GO only if FLOW 1–4 **pass** (not skip) on at least Chromium 1440.

---

## Application defects

**None proven.** Product CRUD was not exercised. Do not treat code-review of Prompt 2 pages as PASS.

No Prompt 2 application-logic fix list: blocker is missing secrets, missing Supabase public env, and API/Next not listening. **No product logic repaired.**

---

## What this session did

- Independent prerequisite re-verify (git, health, ports, boolean env presence; key names only in `.env.local`).
- Executed Prompt 3 command set: Playwright (20 skipped), unit, typecheck, lint.
- Updated this gate document.
- **No push / PR / merge / deploy.**
- **Did not start Prompt 4.**

---

## Exit block

```
CORE DAILY DRIVER E2E: BLOCKED

SHA: 143eda9ad1cf5042b51058264456436f0d5cb1b7
Branch: recovery/core-daily-driver

Playwright: discovered 20 / passed 0 / failed 0 / skipped 20 / blocked 20
Unit: 14/14 PASS
Typecheck: PASS
Lint: PASS

FLOW 1 Venture: BLOCKED
FLOW 2 Project: BLOCKED
FLOW 3 Task: BLOCKED
FLOW 4 Person: BLOCKED
Cross-tenant: BLOCKED (no second user)

Exact missing:
- E2E_EMAIL
- E2E_PASSWORD
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY / NEXT_PUBLIC_SUPABASE_ANON_KEY
- FastAPI :8000 (/health/live unreachable)
- Next.js :3000 (/login unreachable; webServer gated off)

REMOTE ACTIONS: NONE
NO PUSH / NO PR / NO MERGE / NO DEPLOYMENT

PROMPT 4: DO NOT START
```
