# G1 — Database Schema Gate (ONE SCHEMA)

**Role:** Principal PostgreSQL / Data Architecture Engineer
**Date:** 2026-08-27
**Branch:** `recovery/core-daily-driver`
**Starting SHA:** `42934ec`
**Ending local SHA:** `<see exit report below>`
**Remote actions:** **NONE** — **NO PUSH, NO PR, NO MERGE, NO DEPLOY**

---

## Verdict

# G1 ONE SCHEMA: **PASS** (with POSTGRES INTEGRATION BLOCKED)

`supabase/migrations/` is now the single schema authority. The application never creates schema at
runtime, SQLite is refused outside isolated unit tests, the duplicate engine is gone, and the RAG
tables are intentionally mapped. **Live PostgreSQL verification could not be executed on this machine**
— no Docker, no `psql`, no Supabase CLI, and no development database credentials. The drift gate exists
and is wired, but it reports **POSTGRES INTEGRATION BLOCKED** until a separate dev project is configured.

---

## Source of truth (LOCKED)

| Layer | Role |
|-------|------|
| `supabase/migrations/` | Canonical schema authority |
| SQLAlchemy models | Application mappings onto the canonical schema |
| `Base.metadata` | Never a deployment mechanism |
| SQLite | Isolated unit-test fixture only |

Full inventory and per-table classification: [`G1_SCHEMA_MATRIX.md`](./G1_SCHEMA_MATRIX.md).

---

## Pre-existing working-tree work (inspected and integrated)

The tree started with uncommitted exploratory work. Disposition:

| Item | Disposition |
|------|-------------|
| `apps/api/app/db/schema_contract.py`, `schema_verify.py` (untracked) | **Kept and finished** — now imported by startup verification, the bootstrap script, and the drift test. Extended with the `documents` columns added by migration 0018 and the `jobs`/`exports` contract. |
| `apps/api/app/config.py` (modified: postgres default, `DATABASE_SCHEMA_VERIFY`, sqlite helpers) | **Kept and completed** — the unused helpers are now enforced by a `validate_database_dialect` model validator. |
| `apps/api/scratch_colspec.py` | **Deleted** — dead scratch file containing `create_all`. |

No half-wired code remains.

---

## Step 1 — Schema inventory

See [`G1_SCHEMA_MATRIX.md`](./G1_SCHEMA_MATRIX.md): 62 canonical tables, 33 ORM mappings, 15 SQL
functions, 2 pgvector columns + 2 vector indexes, ~133 foreign keys (62 to `auth.users`), and the RLS
groups. Every table is classified MAPPED / SQL-ONLY INTENTIONAL / MISSING / OBSOLETE / DUPLICATE.

Key finding: `jobs` and `exports` were mapped in the ORM but **absent from migrations** while being used
by the document-upload path, job runner, and export service. On real PostgreSQL those writes would have
failed. Migration 0019 defines them canonically with RLS.

---

## Step 2 — Schema creation removed from startup

- `init_db()` (which called `Base.metadata.create_all` for non-production) is **deleted**.
- Replaced by `verify_database_ready()` in `apps/api/app/dependencies/database.py`: connect → verify
  the migrated schema → fail closed. It never issues DDL.
- `app/main.py` lifespan calls `verify_database_ready()`.
- Regression test `test_runtime_never_creates_schema` fails the build if `create_all(` reappears
  anywhere under `apps/api/app`.
- Unit tests still use their own isolated in-memory SQLite fixture in `tests/conftest.py`.

---

## Step 3 — SQLite forbidden outside unit tests

- `Settings.validate_database_dialect` raises a configuration error when
  `ENVIRONMENT`/`APP_ENV` is `integration`, `e2e`, `staging`, or `production` **and** `DATABASE_URL` is
  SQLite.
- `verify_database_ready()` repeats the guard at startup, and `verify_migrated_schema()` refuses any
  non-PostgreSQL dialect outright.
- Default `DATABASE_URL` is now PostgreSQL; the SQLite URL is pinned only by `apps/api/conftest.py`
  for the unit category.
- Tests: `test_sqlite_forbidden_outside_unit_tests` (integration/e2e/staging) and
  `test_sqlite_forbidden_in_production`.

---

## Step 4 — Duplicate engine resolved

| Module | Outcome |
|--------|---------|
| `apps/api/app/database.py` | **Deleted.** Zero importers; it also silently fell back to in-memory SQLite. |
| `apps/api/app/dependencies/database.py` | **Canonical.** One engine, one `async_sessionmaker`, one intentional pool (`pool_size=5`, `max_overflow=5`, `pool_recycle=1800`, `pool_pre_ping=True` on PostgreSQL; `check_same_thread` only for the SQLite unit fixture). |

Test `test_single_canonical_engine` asserts exactly one module may call `create_async_engine`.

---

## Step 5 — RAG table mappings (mappings only; pipeline is G4)

| Table | Model | Repository |
|-------|-------|-----------|
| `documents` | `models/entities.py::Document` (remapped to canonical columns) | `repositories/knowledge.py::DocumentRepository` |
| `document_chunks` | `models/rag.py::DocumentChunk` | `repositories/rag.py::DocumentChunkRepository` |
| `embeddings` | `models/rag.py::Embedding` | `repositories/rag.py::EmbeddingRepository` |
| `embedding_jobs` | `models/rag.py::EmbeddingJob` | `repositories/rag.py::EmbeddingJobRepository` |

- `embedding` uses the **official** `pgvector.sqlalchemy.Vector(768)` on PostgreSQL; the home-grown
  `get_col_spec` shim is removed. `pgvector>=0.3.0` added to `apps/api/pyproject.toml`.
- Repositories expose data access only — no chunking, no embedding generation, no similarity ranking.
- G0 fail-closed behaviour is untouched: nothing here can report embedding or extraction success.

---

## Step 6 — Development Supabase configuration (names only, no credentials)

Production Supabase ≠ Development/E2E Supabase. Required variable names (documented in
`apps/api/.env.example`, values never committed):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Runtime database (PostgreSQL, migrated) |
| `DATABASE_SCHEMA_VERIFY` | Keep `true`; startup verifies and never creates schema |
| `POSTGRES_TEST_DATABASE_URL` | **Separate dev/staging** PostgreSQL for bootstrap + integration tests |
| `DEV_SUPABASE_URL` | Dev project URL |
| `DEV_SUPABASE_SECRET_KEY` | Dev server secret key |
| `DEV_SUPABASE_ANON_KEY` | Dev anon key |

The bootstrap script refuses any URL containing `prod`, `production`, or `live`.

---

## Step 7 — Migration bootstrap

`scripts/db/bootstrap_migrations.py`:

```powershell
$env:POSTGRES_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
python scripts/db/bootstrap_migrations.py
```

1. Refuses production-looking URLs.
2. Creates a minimal `auth.users` stand-in (no-op on Supabase, required by plain PostgreSQL containers
   because 62 foreign keys reference `auth.users`).
3. Verifies `supabase/migrations` matches `MIGRATION_FILES` in the contract, then applies migrations
   **1..19 in order** (extensions first, so `vector`/`uuid-ossp`/`pgcrypto` exist before use).
4. Validates the resulting schema with `verify_migrated_schema()` and exits non-zero on any mismatch.

Verified locally: the production-URL refusal triggers, and the 19-migration contract/directory sync
check passes. **Applying migrations against a live database was not executed** (see Postgres status).

---

## Step 8 — Schema drift check

`apps/api/tests/integration/test_postgres_schema_contract.py` (marker `postgres`) compares the live
migrated database against `schema_contract.py`: required tables, critical columns and type families,
RAG foreign keys, pgvector dimensions, and the `vector` extension. Any drift fails the suite, so it
fails CI once `POSTGRES_TEST_DATABASE_URL` is provided to CI.

Contract-level drift is additionally guarded without a database by
`test_migration_contract_matches_migrations_directory` and `test_orm_tables_are_classified_against_migrations`,
which run in the unit category today.

---

## Step 9 — Test categories

| Category | Location | Database |
|----------|----------|----------|
| unit | `apps/api/tests/*.py` | isolated in-memory SQLite fixture |
| postgres integration | `apps/api/tests/integration/` | migrated PostgreSQL (`POSTGRES_TEST_DATABASE_URL`) |
| e2e | existing Playwright harness (preserved, out of G1 scope) | migrated PostgreSQL |

**The SQLite unit suite does not prove database parity.** Parity is proven only by the postgres
integration category, which is currently skipped.

---

## Verification (exact)

| Gate | Command | Discovered | Passed | Failed | Skipped | Result |
|------|---------|------------|--------|--------|---------|--------|
| Backend pytest | `python -m pytest apps/api/tests/ -v` | **88** | **83** | **0** | **5** | **PASS** |
| Ruff | `python -m ruff check apps/api` | — | — | 0 | — | **PASS** |
| Mypy | `python -m mypy apps/api/app` | 118 files | — | 0 | — | **PASS** |
| Web test / typecheck / lint / build | `pnpm --filter @second-brain/web ...` | — | — | — | — | **NOT AFFECTED** (no frontend files changed) |
| Postgres integration | `python -m pytest apps/api/tests/integration/` | 5 | 0 | 0 | **5** | **POSTGRES INTEGRATION BLOCKED** |

The 5 skips are exactly the postgres drift suite, skipped with reason
`POSTGRES INTEGRATION BLOCKED: set POSTGRES_TEST_DATABASE_URL ...`. No result is reported as PASS
without a real database behind it.

---

## Postgres verification status

**BLOCKED.** This machine has no Docker, no `psql`, no Supabase CLI, and no development database
credentials. Production Supabase was **not** touched, per instruction. To unblock:

1. Create a **separate** Supabase development project (or run a local `pgvector`-enabled container).
2. Set `POSTGRES_TEST_DATABASE_URL` to it (never production).
3. `python scripts/db/bootstrap_migrations.py`
4. `python -m pytest apps/api/tests/integration/ -v`

---

## Exit criteria checklist

| Criterion | Met? |
|-----------|------|
| Migrations are the canonical schema authority | **YES** |
| `create_all` removed from runtime (regression-tested) | **YES** |
| SQLite forbidden for integration/e2e/staging/production | **YES** |
| Duplicate DB engine resolved (one pool architecture) | **YES** |
| Required RAG tables mapped intentionally with official pgvector | **YES** |
| Schema-drift test exists and fails CI on drift | **YES** |
| Migrated PostgreSQL schema verified against a live database | **NO — BLOCKED (no dev credentials)** |
| G0 fail-closed truth behaviour preserved | **YES** |

---

## Remaining blockers

- **Postgres integration BLOCKED** — needs a separate dev/staging Supabase project or local container.
- CI must be given `POSTGRES_TEST_DATABASE_URL` for the drift gate to actually run there.
- `jobs`/`exports` overlap with `sync_jobs`/`export_jobs`/`export_items`; consolidation is product work.
- Vector search SQL functions (`match_memories`, `match_document_chunks`, `hybrid_knowledge_search`)
  exist but are unused — **G4** owns semantic retrieval.
- `Idea`, `Decision`, `JobRecord`, `ExportRecord` still declare `String(36)` identifiers rather than
  `FlexibleUUID`; harmless today but should be normalised when those domains are next touched.

---

## Explicit remote policy

**NO PUSH. NO PR. NO MERGE. NO DEPLOY.** No remote branch modification. Production Supabase untouched.

**STOP. DO NOT BEGIN G2.**

---

## Exit report

```
G1 ONE SCHEMA: PASS (POSTGRES INTEGRATION BLOCKED)

Branch: recovery/core-daily-driver
Starting SHA: 42934ec
Ending local SHA: <commit sha>

Done: migrations locked as canonical authority; create_all removed from startup and
  regression-tested; SQLite fail-fast guard for integration/e2e/staging/production;
  duplicate app/database.py engine deleted (single pooled engine); RAG tables
  (documents, document_chunks, embeddings, embedding_jobs) mapped with official
  pgvector Vector(768); migrations 0018/0019 close documents-column and jobs/exports
  gaps; JSONB now used natively on PostgreSQL; bootstrap script + schema-drift test.

Tests: pytest 88 discovered / 83 passed / 0 failed / 5 skipped (postgres suite);
  ruff PASS; mypy PASS (118 files); web gates NOT AFFECTED

Postgres verification: BLOCKED — no Docker/psql/Supabase CLI and no dev credentials

NO PUSH, NO PR, NO MERGE, NO DEPLOY
```
