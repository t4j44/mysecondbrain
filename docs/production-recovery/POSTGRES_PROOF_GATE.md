# PostgreSQL Proof Gate — independent verification

**Branch:** `recovery/core-daily-driver`
**Starting SHA:** `75cea9592fa83d886cecd352c190828f3ea878ec` (`75cea95`, `docs: add a verified recovery run guide for 143eda9..b1937d1`)
**Ending SHA:** _(documentation-only commit for this file, if created — see section 11)_
**Prompt-expected SHA:** `b1937d1`. Actual `HEAD` is `75cea95`, the docs-only commit one ahead of `b1937d1`. The
prompt anticipated this; it is confirmed, and no code differs between the two.
**Working tree at start:** clean except one untracked archive, `_cloud_stage.tar.gz`. No local work was modified,
staged, or deleted by this gate. `git diff --stat` was empty.

**Scope executed:** Steps 1, 2, 4 (partially — no target existed to check), 6 (attempted), 7, 8, 9, 10.
**Scope blocked:** Step 3 (obtain a non-production PostgreSQL) and therefore Step 5 (bootstrap migrations) and the
substantive half of Step 6.

**No push, no PR, no merge, no deployment, no production database was contacted or altered.** No environment
secret value is printed anywhere in this document.

---

## 1. Final verdict

> ## POSTGRES PROOF: **BLOCKED**
>
> Blocked for environment reasons only, not for code reasons. This machine has no PostgreSQL, no Docker, no WSL,
> and no configured development Supabase project. Zero PostgreSQL-gated tests executed. All 29 of them skipped,
> exactly as they did in the previous run. **A skipped test is not a pass and is not recorded as one below.**

Nothing in the repository blocked this gate. The migration contract is internally consistent, the bootstrap
script is coherent, the integration suite is correctly wired, and the static gates are green. The only missing
input is a database.

### Verdict table

| Item | Verdict |
|---|---|
| Schema drift | **NOT PROVEN** (no database; the 5 drift tests skipped). Static contract-vs-disk check: PASS |
| RLS | **NOT PROVEN** |
| Cross tenant | **NOT PROVEN** |
| Pool claim isolation | **NOT PROVEN** |
| MCP finalize Postgres tests | **BLOCKED** |
| Network migrations/backfills | **BLOCKED** |
| Legacy commitment write path | **PRESENT** |
| Gemini configuration | **MISSING** |

The prompt's output template offers PASS/FAIL for schema drift. Neither is honest here: the drift suite never ran.
It is recorded as NOT PROVEN, with the static portion that *was* verifiable reported separately in section 5.

---

## 2. Step 1 — Baseline (verified)

```
git branch --show-current   -> recovery/core-daily-driver
git rev-parse HEAD          -> 75cea9592fa83d886cecd352c190828f3ea878ec
git status --short          -> ?? _cloud_stage.tar.gz   (only entry)
git diff --stat             -> (empty)
```

Recent history, newest first: `75cea95` (run guide), `b1937d1` (G5.5 docs), `2bf3db0` (G5.5 implementation),
`4d039ee` (G5 docs), `71c35d2` (G5 implementation). This matches the run guide's timeline.

Note: the pre-conversation git snapshot showed many untracked files under `apps/api/app/...` (network endpoints,
schema contract, entities, migration 0022). Those are all committed as of `HEAD`; the snapshot was stale. The
live working tree is clean.

---

## 3. Step 2 — PostgreSQL test requirements (verified from source, not from the gate documents)

### The variable that gates everything

`POSTGRES_TEST_DATABASE_URL`. One variable, read in three places, all confirmed by reading the files:

| Reader | Behavior |
|---|---|
| `apps/api/tests/integration/conftest.py:7` | `os.getenv("POSTGRES_TEST_DATABASE_URL", "").strip()`; empty string triggers the `requires_postgres` skip marker |
| `scripts/db/bootstrap_migrations.py:114` | Same read; raises `SystemExit` with setup instructions when empty |
| `apps/api/app/config.py` | Declared on `Settings`, default empty |

Other variables named in the run guide and confirmed to exist in `app/config.py`: `DATABASE_URL`,
`DATABASE_SCHEMA_VERIFY`, `ENVIRONMENT` / `APP_ENV`, `GEMINI_API_KEY`, `GEMINI_MODEL`,
`GEMINI_EMBEDDING_MODEL`. Variable **names** only; no values are recorded here. None of them is currently set in
this shell's environment, and no `.env` file exists for the API at all — the only env files in the repository are
`apps/api/.env.example`, `apps/web/.env.example`, `apps/web/.env.local`, and `apps/web/e2e/.env.example`.

### The exact DSN format required (read from the code, not guessed)

`scripts/db/bootstrap_migrations.py` accepts **either** driver spelling and normalizes internally:

- `asyncpg_url()` (line 126) strips `postgresql+asyncpg://` down to `postgresql://` for the raw `asyncpg.connect`
  call that applies migrations.
- `sqlalchemy_url()` (line 130) does the reverse for the SQLAlchemy validation engine.

So `postgresql://user:pass@host:port/dbname` is the canonical form and is what the script's own docstring uses:

```
postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

`postgresql+asyncpg://...` also works for the bootstrap script. However, `tests/integration/conftest.py:24`
passes the raw value straight into `create_async_engine` with **no normalization**, so for the test suite the
value must be one SQLAlchemy can resolve to an async driver. `postgresql://` works when `asyncpg` is the only
installed driver but is fragile; **`postgresql+asyncpg://` is the safer spelling for the test run**, and
`postgresql://` is the safer spelling for the bootstrap script. Both scripts tolerate both, so a single
`postgresql+asyncpg://` value is the one that satisfies both paths.

**Refused inputs.** `PRODUCTION_MARKERS = ("prod", "production", "live")` (line 25). Any URL whose lowercased
form contains one of those substrings causes `SystemExit` before a connection is opened. This is a safety net,
not a guarantee — a Supabase project reference is a random string and will not trip it.

### What the bootstrap actually does, in order

1. `resolve_target_url()` — production-marker refusal.
2. `AUTH_SHIM_SQL` — creates `auth` schema, `auth.users`, the `anon` and `authenticated` roles, and
   `auth.jwt()` / `auth.uid()` / `auth.role()`. Every object is guarded by `IF NOT EXISTS` or a `pg_proc` /
   `pg_roles` existence check, so it is a genuine no-op on a real Supabase project and cannot overwrite the
   platform's own definitions. This shim is what makes RLS testable on a plain container.
3. `migration_paths()` — compares `supabase/migrations/*.sql` against `app.db.schema_contract.MIGRATION_FILES`
   and exits on any drift.
4. Applies each migration in contract order via `asyncpg`.
5. `POST_MIGRATION_GRANT_SQL` — grants sequence/function usage to `authenticated`, revokes all on
   `public.integration_tokens`.
6. `verify_migrated_schema()` — exits non-zero on contract mismatch.

### Migration and contract state (independently confirmed)

Executed against the current source:

```
contract migrations: 22
on disk:             22
match:               True
last 5: ..._0018_align_documents_with_application_contract.sql
        ..._0019_create_jobs_and_exports_tables.sql
        ..._0020_harden_rls_authorization_boundary.sql
        ..._0021_mcp_work_session_finalization.sql
        ..._0022_network_relationship_intelligence.sql
```

`app/db/schema_contract.py` requires **39** tables (the run guide says 38 — the guide is one stale; the code is
authoritative), pins `EMBEDDING_VECTOR_DIMENSIONS = 768`, and exempts only `integration_tokens` from the RLS
policy audit. The tables added by 0019 and 0022 are all present in `APPLICATION_REQUIRED_TABLES`:
`jobs`, `exports`, `person_organization_roles`, `commitments`. The `documents` column list in the contract
includes the four columns added by 0018: `extension`, `extracted_text`, `chunking_state`, `error_state`.

**Therefore the claim that `verify_database_ready()` requires schema from migrations 0018–0022 is CONFIRMED.**
`app/main.py:31` calls `await verify_database_ready()` in the lifespan; the function is defined at
`app/dependencies/database.py:138`. Any database missing 0018–0022 will fail startup. That is the intended
fail-closed behavior, and it also means this branch cannot be deployed without a migration step.

---

## 4. Step 3 — Obtaining a safe non-production PostgreSQL: **FAILED, environment**

Every option in the prompt's preference order was checked. The prompt's note that Docker may be absent was
re-verified rather than assumed, and it is correct.

| Option | Probe | Result |
|---|---|---|
| A. Existing non-production database configured locally | `POSTGRES_TEST_DATABASE_URL`, `DATABASE_URL` in the environment; search for `.env` files | **None.** Both variables unset. No `.env` exists for `apps/api` — only `.env.example`. `apps/web/.env.local` exists but is a Next.js frontend file, not an API database DSN |
| A. A Postgres already running locally | `Get-NetTCPConnection` on ports 5432, 54322, 54321, 6543 | **Nothing listening on any of them** |
| A. A Postgres installed as a service | `Get-Service` filtered on `*postgres*` | **No service** |
| A. Client tooling | `psql`, `pg_ctl`, `initdb` | **All absent from PATH** |
| B. Docker | `docker --version`, `docker info`, `docker-compose`, `Get-Service *docker*` | **Not installed.** `CommandNotFoundException`; no Docker service registered |
| B. Podman | `podman --version` | **Not installed** |
| B. WSL (as a host for a Linux Postgres) | `wsl -l -v` | **`The Windows Subsystem for Linux is not installed.`** WSL cannot host a container or a Postgres either |
| B. Supabase CLI (local stack) | `supabase --version` | **Not installed** |
| Package managers, for completeness | `scoop`, `choco`, `winget` | Only `winget` is present |

One further avenue was attempted and deliberately abandoned: installing a pip-distributed embedded PostgreSQL
(`pgserver`) that would have needed no administrator rights. That install was stopped because it mutates the host
Python environment beyond the repository's declared dependencies, and the prompt's Step 3 option C directs a stop
and report rather than improvised environment changes. It is listed in section 10 as an option the user may
choose, not something taken unilaterally.

**Result: Step 3 option C. Stopped and reported.** Consequently no database existed to run Step 4's safety check
against and no database existed for Step 5 to bootstrap.

---

## 5. Steps 4 and 5 — Safety check and bootstrap: **NOT RUN**

- **Postgres target category: NONE.** No target was created, connected to, or altered. No production or cloud
  resource was created or modified in any way.
- **Safe metadata (host category, database name, PostgreSQL version, pgvector availability): unavailable**, because
  no target exists. In particular **pgvector availability is UNKNOWN**, and it is a hard requirement — the
  contract pins a 768-dimension vector and the migrations create `vector` columns, so whatever database is used
  must be able to `CREATE EXTENSION vector`.
- **Migration result: NOT RUN.** No migration was applied to any database. As the run guide states and this gate
  confirms, all 22 migrations — including 0018 through 0022 — remain applied nowhere.
- **`verify_database_ready()` / `verify_migrated_schema()` result: NOT RUN.**

The one schema check that *was* possible without a database is the static one, and it passes: the migration
directory and `MIGRATION_FILES` agree exactly (22 = 22), so `bootstrap_migrations.py` would clear its drift guard
and proceed to apply migrations the moment a URL exists. That is a real but narrow result — it proves the file
list is consistent, not that the resulting schema matches the contract.

---

## 6. Step 6 — PostgreSQL test run: attempted, all gated tests skipped

The full suite was run without `POSTGRES_TEST_DATABASE_URL` (it could not be set to anything, as no database
exists). Counts are from a JUnit XML report, not from reading a terminal summary line.

| Metric | Count |
|---|---|
| Collected | **179** |
| Passed | **150** |
| Failed | **0** |
| Errors | **0** |
| Skipped | **29** |

pytest exit code `0`. This reproduces the previously reported figures exactly: 179 total, 150 SQLite/unit passing,
29 PostgreSQL-gated skipping. **The previous run's claim is CONFIRMED, including the fact that it is a skip and
not a pass.**

Every one of the 29 skips carries the identical reason string, read from the report:

> `POSTGRES INTEGRATION BLOCKED: set POSTGRES_TEST_DATABASE_URL to a migrated development/staging PostgreSQL database (never production).`

### The 29, grouped as the prompt requires

| Category | Suite | Tests | Result |
|---|---|---|---|
| Schema contract / drift | `tests/integration/test_postgres_schema_contract.py` | 5 | **0 executed, 5 skipped** |
| RLS and cross-tenant, incl. pool-claim isolation | `tests/integration/test_rls_cross_tenant.py` | 12 | **0 executed, 12 skipped** |
| MCP finalize / idempotency | `tests/integration/test_mcp_finalize_postgres.py` | 4 | **0 executed, 4 skipped** |
| Network migration / backfill / query | `tests/integration/test_network_intelligence_postgres.py` | 8 | **0 executed, 8 skipped** |

The tests exist and are named coherently for what they claim to prove — the function names were read directly.
Pool-claim isolation is `test_pooled_connection_carries_no_previous_user_claims`; the defense-in-depth case is
`test_rls_blocks_user_b_even_without_an_application_user_id_filter`; database-layer idempotency is
`test_duplicate_client_request_id_is_rejected_by_the_database` plus `test_the_idempotency_constraint_is_per_owner`;
the two backfills are `test_backfill_promotes_person_organization_id_to_a_primary_role` and
`test_backfill_expands_the_commitments_array_without_guessing_direction`. **None of them ran.** Their existence is
evidence of intent, not of correctness.

The `postgres` marker is registered in `apps/api/pyproject.toml:53-55`, so the gating is by the `requires_postgres`
`skipif` in `tests/integration/conftest.py:9`, keyed solely on the environment variable.

---

## 7. Step 7 — Security proof

Stated plainly, because this is the section most likely to be misread later.

| Claim | Status |
|---|---|
| User A cannot **read** User B's data | **NOT PROVEN** |
| User A cannot **update** User B's data | **NOT PROVEN** |
| User A cannot **delete** User B's data | **NOT PROVEN** |
| RLS survives an application-query path without relying on a `user_id` filter | **NOT PROVEN** |
| Connection-pool identity does not leak from User A to User B | **NOT PROVEN** |

**No PostgreSQL run occurred, so nothing in this table is proven by execution.** A test that skips proves nothing
about the property it names.

What *is* true, and is a weaker statement: the code implementing these boundaries exists and is statically
enforced by the SQLite unit suite (22 tests in `test_g2_rls_security.py` pass), and migration 0020 rewrites every
user-owned table's policies to `auth.uid() IS NOT NULL AND user_id = auth.uid()`. But SQLite has no roles, no
GUCs, and no policies, so the unit suite can only check that the *application* constructs the right statements —
never that the database denies anything.

The specific unexercised risk the run guide flags remains exactly as risky: the `after_begin` claim re-injection
listener in `app/dependencies/database.py` has still never executed against a live PostgreSQL server. Until it
does, whether RLS identity survives a mid-request commit is an assumption.

---

## 8. Step 8 — Finalizer / commitment write path

**LEGACY WRITE PATH PRESENT.**

Verified by direct inspection of `apps/api/app/mcp/tools.py`, not by trusting the gate documents.
`finalize_work_session` builds its session row as:

```1047:1049:apps/api/app/mcp/tools.py
                commitments=[
                    c if isinstance(c, str) else str(c) for c in resolved_commitments
                ],
```

That is the `interactions.commitments` `TEXT[]` column — the exact column migration 0022 marks deprecated with
`COMMENT ON COLUMN`. Commitments are also echoed into the session payload dictionary at lines 1028 and 1245.

Confirming the negative: a search for `Commitment` and `PersonOrganizationRole` across the whole of
`apps/api/app/mcp/` returns exactly one hit — the English word in a comment at line 919. **The first-class
`Commitment` ORM model is never imported and never constructed anywhere in the MCP layer.**

Consequence, stated for the record: every commitment created through `finalize_work_session` lands in the
deprecated array and will not appear in the `commitments` ledger the G5.5 query surface reads. As instructed,
this was **not fixed** in this gate.

---

## 9. Step 9 — Gemini dependency

**Gemini configuration: MISSING.**

- `app/config.py:44` declares `GEMINI_API_KEY: str = "placeholder_gemini_key"` — the default is a placeholder,
  not a key.
- `GEMINI_API_KEY` is **unset** in the environment, and no `.env` exists for `apps/api` to supply it.
- `app/services/gemini_client.py:35` treats both an empty value and the literal placeholder as unconfigured and
  logs a warning.
- `app/mcp/extraction.py:186-191` instantiates `GeminiLLMProvider`, and when unconfigured records the telemetry
  string `"GEMINI_API_KEY is unconfigured; AI extraction unavailable."` and falls back to the deterministic
  parser, reporting `mode` honestly rather than claiming AI extraction.

No key value is printed here, because there is no key and there would be none printed if there were. G4 was not
tested, not built, and no AI extraction success is claimed. MCP finalize extraction, if it ran today, would run
in deterministic fallback mode — the mode that scored 1 correct out of 85 observations at G5.

---

## 10. Step 10 — Static regression

Run from `apps/api`. No application code was modified for any of these.

| Gate | Command | Result |
|---|---|---|
| Unit / full pytest suite | `python -m pytest apps/api/tests/` | **PASS** — 179 collected, 150 passed, 0 failed, 29 skipped, exit 0 |
| Lint | `python -m ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| Types | `python -m mypy app` | **FAIL (2 errors), pre-existing and out of scope** |

The mypy failure, in full:

```
app\services\document_extractor.py:159: error: Unused "type: ignore" comment  [unused-ignore]
app\services\document_extractor.py:160: error: Unused "type: ignore" comment  [unused-ignore]
Found 2 errors in 1 file (checked 120 source files)
```

This is **not a regression from this branch**. `git log 143eda9..HEAD -- apps/api/app/services/document_extractor.py`
returns **zero commits** — the file was last touched by `a4e947b`, before the recovery range began. The errors are
`unused-ignore` on `type: ignore` comments guarding an optional PDF dependency, which is precisely the class of
error whose presence depends on whether that dependency is installed in the local interpreter. Fixing it would mean
editing unrelated application code to make a gate green, which the prompt forbids. Recorded and left alone.

---

## 11. SHAs

- **Starting SHA:** `75cea9592fa83d886cecd352c190828f3ea878ec`
- **Ending SHA:** if a documentation-only commit adding this file is created, it becomes the ending SHA and should
  be written back into this line. No code file was changed by this gate — the only new file is this document.

---

## 12. What the user must do manually to unblock this gate

This is the complete, precise set of instructions. Pick **one** of the three options. All commands are PowerShell
(`;` as the separator).

### Option 1 — Docker Desktop with a pgvector image (recommended; fully disposable)

Docker is not installed on this machine, so this begins with an install that requires administrator rights and,
typically, a reboot.

```powershell
winget install --id Docker.DockerDesktop -e
```

Reboot if prompted, launch Docker Desktop once so the engine starts, then confirm `docker info` succeeds. Then:

```powershell
docker run -d --name sb-dev-pg -p 54322:5432 `
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres `
  pgvector/pgvector:pg16
```

The image **must** be a pgvector build; a stock `postgres` image will fail the migrations that create `vector`
columns.

Note that Docker Desktop on Windows normally requires WSL2, which is also absent here. `wsl --install` (administrator,
reboot required) may be needed first. Docker Desktop's Hyper-V backend is the alternative if WSL is not wanted.

### Option 2 — a separate development Supabase project (no local install)

1. Create a **new** Supabase project. Do **not** reuse the production Second Brain project.
2. Copy its connection string from Project Settings → Database.
3. Confirm by eye that the project reference is the development one. The bootstrap script's `prod`/`production`/`live`
   substring guard will **not** save you here, because Supabase project references are random strings.

Supabase provides `pgvector`, `auth.users`, the `anon`/`authenticated` roles, and the `auth.*` functions natively,
so the bootstrap script's shim correctly no-ops.

### Option 3 — an embedded PostgreSQL via pip (no administrator rights)

A package such as `pgserver` bundles PostgreSQL binaries and pgvector and can run a throwaway data directory
without an installer. This was deliberately **not** attempted in this gate because it mutates the Python
environment. Choose it only if you accept that change; verify pgvector support and Windows support for the exact
package version before relying on it.

### Then, whichever option was chosen

```powershell
$env:POSTGRES_TEST_DATABASE_URL = "postgresql+asyncpg://postgres:<password>@127.0.0.1:54322/postgres"
python scripts/db/bootstrap_migrations.py
python -m pytest apps/api/tests/integration/ -v
```

Set the variable **in the shell only**. Do not write it into a committed file. For a Supabase target, substitute
`postgresql+asyncpg://postgres:<dev-password>@db.<dev-ref>.supabase.co:5432/postgres`.

**Expected outcome when it works.** `bootstrap_migrations.py` prints `applying ...` twenty-two times, then
`Bootstrap complete: migrations applied and schema contract validated.` and exits `0`. The integration run should
then collect **29** tests and skip **none**. If any still skip, the environment variable did not reach the pytest
process.

**What to watch first.** The single most informative result in that run is whether the `after_begin` claim
re-injection in `app/dependencies/database.py` works against a live server. It has never executed. If it
misbehaves the failure is fail-closed and loud — queries run without claims and RLS denies them — so a wave of
denial failures across `test_rls_cross_tenant.py` points there rather than at the policies.

**What this converts.** Bootstrap success closes G1's last open exit criterion. The 5 schema-contract tests convert
G1's POSTGRES INTEGRATION verdict; the 12 RLS tests convert G2 CROSS-TENANT and POOL CLAIM ISOLATION and give
section 7 of this document real answers; the 4 finalize tests convert the database half of G5 IDEMPOTENCY; the 8
network tests convert the G5.5 backfill and RLS halves. Adding `POSTGRES_TEST_DATABASE_URL` to CI secrets is what
makes these suites protect the repository rather than decorate it.

---

## 13. Remote safety attestation

No push. No pull request. No merge. No deployment. No production database was contacted, created, migrated, or
altered. No cloud resource of any kind was created or modified. No secret value appears in this document. The only
filesystem change made by this gate is the creation of this file. G3 and G4 were not started.
