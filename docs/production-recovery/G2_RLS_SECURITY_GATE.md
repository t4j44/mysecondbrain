# G2 — RLS Security Gate (REAL AUTHORIZATION BOUNDARY)

**Role:** Principal Application Security + PostgreSQL Authorization Engineer
**Date:** 2026-08-28
**Branch:** `recovery/core-daily-driver`
**Starting SHA:** `0e26cc5`
**Ending local SHA:** see the exit report at the bottom of this document
**Remote actions:** **NONE** — **NO PUSH, NO PR, NO MERGE, NO DEPLOYMENT**

---

## Verdicts

| Verdict | Result |
|---------|--------|
| **RLS ACTIVE FOR API** | **PASS** — implemented and centralized; every authenticated request path now runs under transaction-local claims and the `authenticated` role. Runtime execution against a real PostgreSQL server is **not** confirmed on this machine (see *Postgres status*). |
| **CROSS-TENANT** | **BLOCKED** — two-user denial tests are written and wired; they require a dev/staging PostgreSQL. |
| **POOL CLAIM ISOLATION** | **BLOCKED** — tests written; require the same database. |
| **ADMIN SEPARATION** | **PASS** — statically verified, no database required. |
| **G2 SECURITY** | **BLOCKED** — implementation complete, PostgreSQL verification not executable here. **No PASS is claimed for anything a database would have had to prove.** |

Before G2, PostgreSQL RLS was **decorative** for API traffic: the application connected with the
owning role and never injected caller claims, so `auth.uid()` was NULL and policies were either
skipped (owner bypass) or would have denied everything. The only tenant boundary was the
application's `WHERE user_id = :caller`. That single point of failure is now backed by the database.

---

## Architecture (implemented)

```
validate Supabase JWT (get_current_user)
  └─ BEGIN
       ├─ set_config('request.jwt.claims',      <verified claims>, true)   -- transaction-local
       ├─ set_config('request.jwt.claim.sub',   <verified sub>,    true)
       ├─ set_config('role',                    'authenticated',   true)   -- = SET LOCAL ROLE
       ├─ queries (application user_id filters retained)
       │    └─ RLS policies evaluate auth.uid()
       └─ COMMIT / ROLLBACK   -- identity dies with the transaction
```

* Everything uses `set_config(..., is_local => true)` — the function form of `SET LOCAL`. There is
  no plain `SET` anywhere, so identity can never survive a connection returning to the pool. The
  pool's own rollback-on-return is a second layer of the same guarantee.
* Identity values are **bound parameters**; only module-level constants are interpolated into SQL,
  so there is no injection surface in the role or subject.
* Claims are built from the verified token only (`sub`, `role`, `aud`, `email`). Arbitrary
  client-supplied claims cannot be smuggled into the GUC.
* The subject must parse as a UUID or the request fails closed before any SQL runs.
* Because services commit mid-request and identity is transaction-local, an `after_begin` listener
  re-injects it at the start of **every** transaction on the session. Without this, post-commit
  queries would run with no claims and RLS would deny them.
* Defense in depth is preserved: the repository layer keeps its explicit `user_id` filters. RLS is
  an independent second boundary, not a replacement.

### Files

| File | Role |
|------|------|
| `apps/api/app/db/rls.py` | **New.** Pure identity builder: claim set, allowed roles, ordered `set_config` statements, identity probe SQL. |
| `apps/api/app/dependencies/database.py` | **The one** place that injects identity. Provides `get_rls_db_session` (the only endpoint DB dependency), `rls_db_session(...)` (non-HTTP user-scoped paths), `admin_db_session(reason=...)`, and `current_identity()`. |
| `supabase/migrations/20260828000020_harden_rls_authorization_boundary.sql` | **New.** Policy hardening, `authenticated` grants, indirect-ownership checks. |
| `scripts/db/bootstrap_migrations.py` | Auth shim extended with `anon`/`authenticated` roles and `auth.uid()`/`auth.jwt()`/`auth.role()` so a plain container can actually exercise RLS. Guarded — a no-op on Supabase, never overwrites platform definitions. |

`get_db_session` — the identity-free dependency — was **removed**. A test fails the build if it
returns, because any authenticated endpoint injecting it would silently bypass RLS.

---

## Audit — every database path classified

| Path | Class | Session context |
|------|-------|-----------------|
| 22 domain service factories in `dependencies/services.py` (profiles, ventures, projects, tasks, KPIs, reviews, dashboard, people, orgs, interactions, meetings, memories, ideas, decisions, documents, AI, achievements, portfolio, content, integrations, exports, audit) | **USER-SCOPED** | `get_rls_db_session` |
| `api/v1/endpoints/mcp.py` — MCP credential CRUD (6 endpoints) | **USER-SCOPED** | `get_rls_db_session` |
| `mcp/router.py` — `POST /mcp/tools/invoke` tool execution | **USER-SCOPED** | `rls_db_session(sec_ctx.user_id)` |
| `mcp/server.py` — 9 registered MCP SDK read/draft tools | **USER-SCOPED** | `rls_db_session(user_id)` |
| `repositories/base.py` + all domain repositories | **USER-SCOPED** | Inherit the caller's session; explicit `user_id` filters retained |
| `mcp/router.py` / `mcp/server.py` — API-key verification | **SYSTEM/ADMIN** | `admin_db_session(reason="mcp_*_verification")` — must scan credentials across profiles before an owner is known |
| `jobs/runner.py` — `JobRunner.run_job_by_id` and handlers | **SYSTEM/ADMIN** | `admin_db_session(reason="job_execution:<id>")` — resolves jobs across all owners |
| `main.py` — `/health/ready` | **SYSTEM/ADMIN** | `admin_db_session(reason="readiness_probe")` — `SELECT 1` only |
| `dependencies/database.py` — `verify_database_ready` (startup) | **SYSTEM/ADMIN** | Engine-level, catalog reads only, no user data |
| `/health`, `/health/live`, `GET /mcp`, `GET /mcp/tools` | **PUBLIC** | No database access |
| `public.integration_tokens` (OAuth vault) | **SYSTEM/ADMIN ONLY** | RLS on, zero policies, `authenticated` privileges revoked |

`admin_db_session` is an async context manager, **not** a FastAPI dependency, so it cannot be
injected into an endpoint. Tests assert that no module under `app/api`, `app/mcp`,
`app/dependencies` or `app/services` writes `Depends(admin_db_session)`, and that only
`dependencies/database.py` constructs sessions from the factory.

---

## RLS policy audit and fixes

**Coverage before G2 was good; correctness and reachability were the problems.**

| Finding | Disposition |
|---------|-------------|
| Policies used the bare form `user_id = auth.uid()` | Hardened to the explicit `auth.uid() IS NOT NULL AND user_id = auth.uid()` so an absent identity is unambiguously denied rather than relying on NULL-comparison semantics. |
| `authenticated` had no guaranteed table privileges | Migration 0020 grants `SELECT/INSERT/UPDATE/DELETE` per table, otherwise the role switch would fail before policies were even reached. |
| Policy lists were hand-maintained arrays (0015, 0017, 0019), so a new table could be forgotten | 0020 drives the loop off `pg_catalog`: **every** `public` table owning a `user_id` is enabled and policied. No table can be missed. |
| `document_chunks`, `embeddings`, `embedding_jobs` had only direct `user_id` checks — a chunk could be attached to another user's document | INSERT/UPDATE policies now also require the parent row to belong to `auth.uid()` (`EXISTS` on `documents` / `document_chunks`, NULL-tolerant where the FK is optional). Existing policies were **replaced**, not supplemented, because multiple permissive policies for one command are OR'ed and would have weakened the check. |
| `profiles` had no INSERT policy, but the application creates the caller's own profile row (MCP credential path) | Added `WITH CHECK (auth.uid() IS NOT NULL AND id = auth.uid())`. Still no DELETE policy. |
| `audit_logs` immutability rested on absent policies alone | Also `REVOKE UPDATE, DELETE ... FROM authenticated`. Append-only preserved. |
| `integration_tokens` relied on "RLS with no policies" | Plus `REVOKE ALL ... FROM authenticated`, and any policy that ever appears is dropped. Reachable only from the admin context. |
| Tasks/projects/people cross-user linkage | Already enforced by the validation triggers from migration 0013; unchanged. |

**No RLS was disabled, dropped or weakened to make tests pass.** A test fails the build if
`DISABLE ROW LEVEL SECURITY` ever appears in a migration, and another asserts every `CREATE POLICY`
in the tree references `auth.uid()`.

`FORCE ROW LEVEL SECURITY` was deliberately **not** applied: the admin/system context legitimately
needs cross-owner access, and forcing RLS on the owner role would break the job runner and
credential verification. Admin separation is enforced in the application instead, explicitly and
testably.

---

## Tests

### Unit category — `apps/api/tests/test_g2_rls_security.py` (22 tests, all run here)

Architecture and policy invariants, no database required:

* Every injected setting is `set_config(..., true)`; a plain `SET` fails the test.
* Identity values are bound parameters and never appear in SQL text.
* Claims carry the verified `sub`/`role`/`email`; the role is `authenticated`.
* Role switching is restricted to `authenticated`/`anon`; `postgres`, `service_role` and an
  injection attempt are all rejected.
* Non-UUID / empty / `None` subjects fail closed.
* Client claims cannot be smuggled — the claim set is exactly `{sub, role, aud, email}`.
* `set_config(` exists in exactly **one** module (`db/rls.py`): no duplicated SET LOCAL logic.
* No API/MCP/service module injects an identity-free or admin session.
* `get_db_session` no longer exists; `get_rls_db_session` and `admin_db_session` do.
* `admin_db_session` is not injectable and requires an explicit `reason`.
* The four privileged paths each declare their admin reason.
* Migration audit: all policies owner-scoped, the G2 migration uses `auth.uid() IS NOT NULL`,
  nothing disables RLS, vault/audit-log privileges revoked, indirect ownership checked, and the
  migration contract includes 0020.

### PostgreSQL integration category — `apps/api/tests/integration/test_rls_cross_tenant.py` (12 tests, all SKIPPED here)

Marker `postgres`, gated on `POSTGRES_TEST_DATABASE_URL`, same pattern as the G1 drift suite:

| Test | Proves |
|------|--------|
| `test_user_b_cannot_read_user_a_record` | Cross-tenant SELECT returns nothing. |
| `test_user_b_cannot_update_user_a_record` | UPDATE affects 0 rows; owner's value intact afterwards. |
| `test_user_b_cannot_delete_user_a_record` | DELETE affects 0 rows; row still present for the owner. |
| **`test_rls_blocks_user_b_even_without_an_application_user_id_filter`** | **Defense in depth**: a deliberately unfiltered `SELECT id, user_id FROM ventures` under B's claims still cannot see A's row. RLS alone holds. |
| `test_user_b_cannot_insert_a_row_owned_by_user_a` | `WITH CHECK` rejects impersonated ownership. |
| `test_claims_do_not_survive_a_commit_without_reinjection` | Identity really is transaction-local. |
| `test_pooled_connection_carries_no_previous_user_claims` | **Pool safety**: A → release → B leaves no trace of A. |
| `test_rls_role_is_active_inside_a_scoped_transaction` | `current_user` is `authenticated`, not the owner. |
| `test_admin_context_is_a_separate_authorization_domain` | Admin keeps the owner role and is not RLS-limited. |
| `test_token_vault_is_unreachable_for_the_authenticated_role` | `integration_tokens` → permission denied. |
| `test_every_user_owned_table_has_rls_with_owner_policies` | Catalog audit: no user-owned table unprotected. |
| `test_all_policies_reference_auth_uid` | Live policy predicates all reference `auth.uid()`. |

All two-user tests run against a **dev/staging** database only, create their own `auth.users` rows,
and clean up after themselves. Nothing points at production.

---

## MCP

MCP user-scoped reads now cross exactly the same tenant boundary as REST:

* Both MCP entry points (official SDK server and the REST `/mcp/tools/invoke` compatibility route)
  resolve the owner from the verified credential, then execute tools inside
  `rls_db_session(user_id)`.
* Credential verification is separated into the admin context, because matching a key prefix
  requires scanning profiles before any owner is known. This also fixes a latent break: under RLS
  that scan would have returned nothing from a user-scoped session.
* **No write tools were registered.** The registered set is unchanged (9 read/draft tools); the 11
  implemented-but-unexposed write tools stay unexposed. Write exposure remains **G5**.

---

## Verification (exact)

| Gate | Command | Discovered | Passed | Failed | Skipped | Result |
|------|---------|------------|--------|--------|---------|--------|
| Backend pytest | `python -m pytest apps/api/tests/ -v` | **122** | **105** | **0** | **17** | **PASS** |
| Ruff | `python -m ruff check apps/api` | — | — | 0 | — | **PASS** |
| Mypy | `python -m mypy apps/api/app` | 119 files | — | 0 | — | **PASS** |
| Postgres integration | `python -m pytest apps/api/tests/integration/ -v` | 17 | 0 | 0 | **17** | **POSTGRES INTEGRATION BLOCKED** |
| Web test / typecheck / lint / build | `pnpm --filter @second-brain/web ...` | — | — | — | — | **NOT AFFECTED** (no frontend files changed) |

The 17 skips are exactly the postgres category: 5 G1 schema-drift tests + 12 new G2 RLS tests,
skipped with reason `POSTGRES INTEGRATION BLOCKED: set POSTGRES_TEST_DATABASE_URL ...`.
Nothing is reported as PASS without a real database behind it.

---

## Postgres verification status

**BLOCKED.** No Docker, no `psql`, no Supabase CLI and no development database credentials on this
machine. Production Supabase was **not** touched. To unblock:

```powershell
$env:POSTGRES_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
python scripts/db/bootstrap_migrations.py
python -m pytest apps/api/tests/integration/ -v
```

---

## Remaining blockers and honest risks

* **Cross-tenant denial and pool isolation are unproven here.** The tests exist and will fail CI
  if RLS regresses, but they need `POSTGRES_TEST_DATABASE_URL` in CI.
* **The `after_begin` re-injection listener has not executed against a live PostgreSQL server.**
  It issues its statements through SQLAlchemy's sync connection facade inside the asyncio greenlet
  context. If that path misbehaves, the failure mode is *fail-closed and loud* — queries run
  without claims and RLS denies them — not a silent leak. This is the first thing to exercise once
  a dev database exists.
* **Migration 0020 has never been applied to any database.** It is local only.
* `docs/database/rls_policy_reference.md` and `docs/qa/database-and-rls-report.md` still document
  the pre-G2 bare `user_id = auth.uid()` form and claim verified isolation. They predate this gate
  and should be re-derived from the live catalog once a dev database exists; the migrations and the
  tests in this gate are the authority in the meantime.
* Supabase Storage path policies were not re-audited (out of G2 scope; storage is G4-adjacent).
* `profiles` INSERT is now self-service; if a Supabase auth trigger also inserts profiles, the two
  paths are compatible but the trigger remains the preferred creator.

---

## Exit criteria checklist

| Criterion | Met? |
|-----------|------|
| One centralized RLS-aware session dependency; no duplicated SET LOCAL | **YES** |
| Verified JWT claims injected transaction-locally, never plain `SET` | **YES** |
| `authenticated` role set per transaction | **YES** |
| Application `user_id` filters retained (defense in depth) | **YES** |
| Identity-free session dependency removed and regression-tested | **YES** |
| Admin/system context explicit and not endpoint-injectable | **YES** |
| Policies audited, hardened, and catalog-driven so no table is missed | **YES** |
| Indirect-ownership child tables checked against their parent | **YES** |
| RLS never deleted or weakened to ease testing | **YES** |
| MCP user-scoped reads use the same tenant boundary | **YES** |
| MCP write tools still unregistered (G5) | **YES** |
| Two-user cross-tenant denial proven against PostgreSQL | **NO — BLOCKED** |
| Pool claim isolation proven against PostgreSQL | **NO — BLOCKED** |
| G0 fail-closed truth behaviour and G1 one-schema authority preserved | **YES** |

---

## Explicit remote policy

**NO PUSH. NO PR. NO MERGE. NO DEPLOYMENT.** No remote branch modification. No production Supabase
changes. Migration 0020 exists locally only.

**STOP. DO NOT BEGIN G3.**

---

## Exit report

```
G2 SECURITY: BLOCKED (implementation complete; PostgreSQL verification not executable)

RLS ACTIVE FOR API:    PASS (centralized, statically enforced; runtime unconfirmed)
CROSS-TENANT:          BLOCKED
POOL CLAIM ISOLATION:  BLOCKED
ADMIN SEPARATION:      PASS

Branch: recovery/core-daily-driver
Starting SHA: 0e26cc5

Done: new app/db/rls.py builds transaction-local, parameter-bound Supabase claims from the
  verified JWT; dependencies/database.py became the single RLS-aware session layer
  (get_rls_db_session + rls_db_session + admin_db_session) with per-transaction
  re-injection; identity-free get_db_session deleted; all 22 domain services, MCP
  credential endpoints, MCP SDK tools and MCP REST invoke moved onto RLS sessions;
  job runner, credential verification and readiness probe moved to an explicit,
  non-injectable admin context; migration 0020 hardens every user-owned table to
  auth.uid() IS NOT NULL AND user_id = auth.uid() driven off pg_catalog, grants the
  authenticated role, adds parent-ownership checks for document_chunks/embeddings/
  embedding_jobs, adds a self-scoped profiles INSERT policy, and locks the token vault
  and audit-log immutability at the privilege level; bootstrap shim gained the
  anon/authenticated roles and auth.uid()/auth.jwt()/auth.role().

Tests: pytest 122 discovered / 105 passed / 0 failed / 17 skipped (postgres category:
  5 G1 drift + 12 new G2 RLS); ruff PASS; mypy PASS (119 files); web gates NOT AFFECTED

Postgres verification: BLOCKED — no Docker/psql/Supabase CLI and no dev credentials

NO PUSH, NO PR, NO MERGE, NO DEPLOYMENT
```
