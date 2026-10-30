# Recovery Run Guide — `recovery/core-daily-driver`

**Range documented:** `143eda9` (starting SHA) → `b1937d1` (ending local SHA)
**Branch:** `recovery/core-daily-driver`
**Working tree at time of writing:** clean; `HEAD` is `b1937d1`
**Remote state:** nothing was pushed. No PR, no merge, no deploy, no production Supabase change.

This document is written for the repository owner returning to this work later. Every figure in it
comes from a command run against this repository or from a file read in it. Where a gate document
and the code disagree, the code wins and the disagreement is named explicitly.

---

## 1. Executive summary

This branch did not add features in the usual sense. It converted a codebase that *looked*
finished into one that *tells the truth about what it is*, and then rebuilt the two foundations
that everything else sits on: the database schema and the authorization boundary.

Four things changed materially.

**The application stopped lying.** Before this run, uploading a document produced a row whose
extracted text read `[Extracted knowledge from ...]`; search returned a hardcoded confidence of
`0.89`; Google integration reported `is_connected: true` off a `simulated_refresh_token`; and the
Google sync job returned invented counts (14 files, 5 events). All of those paths now fail closed
with typed errors or return an honest `not_implemented` state. The capability set did not shrink —
it was never there — but the reporting now matches reality.

**`supabase/migrations/` became the only schema authority.** `Base.metadata.create_all` no longer
runs anywhere outside the isolated SQLite unit fixture. Startup connects, verifies the migrated
schema against a written contract, and refuses to serve if verification fails. A duplicate database
engine (`apps/api/app/database.py`) that silently fell back to in-memory SQLite was deleted. Two
migrations were added because the ORM was mapping tables (`jobs`, `exports`) and columns that did
not exist in any migration — writes that would have failed on real PostgreSQL.

**RLS became a real boundary rather than decoration.** The API used to connect as the owning
database role and never inject caller claims, so `auth.uid()` was NULL and Postgres policies were
effectively bypassed; the only tenant separation was the application's `WHERE user_id = :caller`.
Every authenticated request now runs inside a transaction carrying the verified JWT claims and the
`authenticated` role, injected transaction-locally from one module. Application-level filters were
kept as a second layer.

**The MCP write surface and the relationship graph were built out.** Eleven write tools that
existed in code but were never registered are now exposed behind granular `mcp:*:write` scopes,
including a `finalize_work_session` workflow that extracts session intelligence outside any
database transaction. A first-class `person_organization_roles` table and a `commitments` ledger
replaced a single nullable `organization_id` column and a `TEXT[]` bag of commitment strings.

**The honest current state:** the code for all of the above is written, statically enforced, and
covered by tests that pass today against SQLite. Nothing in this range has ever touched a real
PostgreSQL database. Five migrations exist on disk and have been applied nowhere. Twenty-nine tests
that would prove RLS denial, backfill fidelity, database-level idempotency, and schema parity are
skipped for want of a `POSTGRES_TEST_DATABASE_URL`. Document extraction, embeddings, semantic
retrieval, and Google OAuth remain unbuilt by deliberate decision (G3 and G4 were skipped). This
branch is a solid, honest foundation that has not yet been proven against the database it targets.

---

## 2. Commit-by-commit timeline

`git log --oneline 143eda9..b1937d1` returns eleven commits, oldest last. Read bottom-up.

| SHA | Subject | What it did |
|---|---|---|
| `f03d0e5` | G0 Product Truth: fail closed on unfinished capabilities | The substantive G0 commit. Removed fabricated document extraction, truncated-embedding "success", the hardcoded `0.89` RAG confidence, and the simulated Google connect/sync paths. Added `app/ai/embeddings_storage.py` as a rejection gate for fake vectors, and `tests/test_g0_truth_gate.py`. |
| `9c0b754` | docs: record G0 Product Truth ending SHA | Documentation bookkeeping — wrote the ending SHA into `G0_TRUTH_GATE.md`. |
| `42934ec` | docs: set G0 gate ending SHA to branch HEAD | Corrected the recorded SHA after the previous commit changed HEAD. This is why G0 has two documentation commits. |
| `d2c4c66` | G1 ONE SCHEMA: make Supabase migrations the canonical database schema | The substantive G1 commit. Deleted `init_db()`/`create_all` and `app/database.py`; introduced `verify_database_ready()`; added the SQLite fail-fast dialect guard; mapped the RAG tables with the official `pgvector.sqlalchemy.Vector(768)`; added migrations 0018 and 0019, `scripts/db/bootstrap_migrations.py`, and the postgres-gated drift suite. |
| `0e26cc5` | docs: record G1 One Schema gate ending SHA | Bookkeeping. |
| `3ea55e9` | G2 RLS SECURITY: make Supabase RLS a real authorization boundary | The substantive G2 commit. Added `app/db/rls.py`; rewrote `dependencies/database.py` into the single RLS-aware session layer; deleted the identity-free `get_db_session`; moved the job runner, MCP credential verification, and the readiness probe onto an explicit non-injectable admin context; added migration 0020. |
| `f4b0cbe` | docs: record G2 RLS security gate ending SHA | Bookkeeping. |
| `71c35d2` | G5 MCP WRITE EXPOSURE: register the write surface behind granular scopes | The substantive G5 commit. Registered all eleven write tools on both the SDK server and the REST invoke route behind `mcp:*:write` scopes; added `app/mcp/extraction.py` (no database import, by construction); fixed two defects that made `finalize_work_session` unrunnable; added migration 0021. |
| `4d039ee` | docs: record G5 MCP finalize gate ending SHA | Bookkeeping. |
| `2bf3db0` | G5.5 NETWORK INTELLIGENCE: make the relationship graph queryable | The substantive G5.5 commit. Added migration 0022 with `person_organization_roles` and `commitments`, backfilled and deprecated the two legacy fields, and built the owner-scoped query surface in `repositories/network.py`, `services/network.py`, `schemas/network.py`, and the network endpoints. |
| `b1937d1` | docs: record G5.5 network intelligence gate ending SHA | Bookkeeping. `HEAD`. |

The pattern is consistent: one implementation commit per gate, followed by a documentation commit
recording the gate's ending SHA. Only five of the eleven commits change code.

---

## 3. Per-gate detail

### G0 — Product Truth (verdict: PASS)

**What was broken.** Six production paths reported success for work the system had not done:

- `jobs/handlers/document_processing.py` wrote `[Extracted knowledge from <filename>]` into
  `documents.extracted_text` and stored `embedding = str(vector[:10]) + "..."`.
- `ai/retrieval.py` returned a constant `score=0.89` on every result.
- `services/knowledge.py::search_similar` performed an ILIKE substring match while being labelled
  hybrid/vector search.
- `integrations/google_client.py` minted a `simulated_refresh_token`, a fake email, and
  `is_connected=True`.
- `jobs/handlers/sync_google.py` returned `synced_files_count: 14` and `events_synchronized: 5`.

**What changed.** Each path now fails closed or reports honestly. Verified in the current code:

- `document_processing.py` sets `processing_status="failed"`, clears `extracted_text`, sets
  `error_state` to the error code, and raises `DocumentExtractionNotImplementedError`. The handler
  is 49 lines and contains no extraction logic at all.
- `core/constants.py` defines `DOCUMENT_EXTRACTION_NOT_IMPLEMENTED` and
  `INTEGRATION_NOT_IMPLEMENTED`; `core/errors.py` maps both to HTTP **501** (lines 142 and 161).
- `ai/retrieval.py` emits `score=None`, `confidence_available=False`, `search_mode="keyword"`.
  `schemas/knowledge.py` defaults the same two fields to `False` and `"keyword"`.
- `integrations/google_client.py` returns `{"status": "not_implemented", ...}` and raises
  `INTEGRATION_NOT_IMPLEMENTED` on the sync paths.
- New `app/ai/embeddings_storage.py` rejects string, truncated, or wrong-dimension vectors so a
  fake embedding cannot be presented as stored.

**Files:** `app/jobs/handlers/document_processing.py`, `app/jobs/handlers/sync_google.py`,
`app/ai/retrieval.py`, `app/ai/embeddings_storage.py` (new), `app/integrations/google_client.py`,
`app/core/constants.py`, `app/core/errors.py`, `app/schemas/knowledge.py`,
`app/schemas/integrations.py`, `apps/web/app/(dashboard)/settings/integrations/page.tsx`,
`apps/api/tests/test_g0_truth_gate.py` (new).

**Verdict: PASS.** Nothing here required a database, so the verdict is fully earned.

**Documentation note.** `G0_TRUTH_GATE.md` lists six numbered assertions in its Phase 8 section, but
`tests/test_g0_truth_gate.py` currently collects **7** tests. The file was rewritten at G5 (the MCP
assertion changed from "unregistered writes remain unavailable" to "write exposure is advertised
truthfully"), and the count in the prose was not updated. The code is correct; the prose is stale.

### G1 — One Schema (verdict: PASS, with Postgres integration BLOCKED)

**What was broken.** Three separate problems, each capable of causing a production incident:

1. `init_db()` called `Base.metadata.create_all` outside production, so a non-production deployment
   could invent a schema that diverged from the migrations.
2. `apps/api/app/database.py` was a second engine module that silently fell back to an in-memory
   SQLite database. It had zero importers, but its existence made "which engine am I using" an open
   question.
3. `jobs` and `exports` were mapped in the ORM and written by the document-upload path, the job
   runner, and the export service — but did not exist in any migration. On real PostgreSQL those
   writes would have failed. The `documents` table was likewise missing the `extension`,
   `extracted_text`, `chunking_state`, and `error_state` columns the application requires.

**What changed.**

- `init_db()` and `app/database.py` are deleted. `dependencies/database.py` is the single engine
  and sessionmaker. `app/main.py` line 31 calls `await verify_database_ready()` in the lifespan.
- New `app/db/schema_contract.py` (298 lines) enumerates 38 required tables, per-table critical
  column type families, six required foreign keys, the pgvector dimension (768), and the ordered
  `MIGRATION_FILES` list of 22 migrations. New `app/db/schema_verify.py` checks a live database
  against it. `app/db/__init__.py` re-exports the contract constants.
- `config.py` defaults `DATABASE_URL` to PostgreSQL and adds a `validate_database_dialect` model
  validator that raises when `ENVIRONMENT`/`APP_ENV` is one of `integration`, `e2e`, `staging`,
  `production` and the URL is SQLite. `apps/api/conftest.py` pins
  `DATABASE_URL="sqlite+aiosqlite:///:memory:"` with `ENVIRONMENT=test` before `app.config` imports,
  which is the only sanctioned SQLite path.
- RAG tables mapped in `app/models/rag.py` and `app/repositories/rag.py` using
  `pgvector.sqlalchemy.Vector(768)`; `pgvector>=0.3.0` added to `pyproject.toml`.
- `apps/api/scratch_colspec.py`, a 54-line scratch file containing `create_all`, was deleted.

**Verdict: PASS for the schema-authority work; POSTGRES INTEGRATION BLOCKED.** The drift suite
exists and is wired but has never run against a database.

### G2 — RLS Security (implemented; verdict BLOCKED on database proof)

**What was broken.** The API connected with the owning role and never injected caller claims. In
that configuration `auth.uid()` is NULL, so every policy of the form `user_id = auth.uid()` either
was bypassed by owner privileges or would have denied everything. Row-level security existed in the
migrations and did nothing for API traffic. A single missing `WHERE user_id` clause anywhere in the
repository layer would have been a cross-tenant data leak with no second line of defense.

**What changed.**

- New `app/db/rls.py` (96 lines) is a pure identity builder: it produces the claim set
  (`sub`, `role`, `aud`, `email` — nothing client-supplied), the allowed role list, and the ordered
  `set_config(..., is_local => true)` statements. Identity values are bound parameters; only
  module-level constants are interpolated. A non-UUID subject fails closed before any SQL runs.
- `dependencies/database.py` grew from a thin module to 161 changed lines and is now the only place
  identity is injected. It exposes `get_rls_db_session` (the only endpoint dependency),
  `rls_db_session(user_id)` for non-HTTP user-scoped paths, and `admin_db_session(reason=...)`.
  Because services commit mid-request and `SET LOCAL` dies with the transaction, an `after_begin`
  listener re-injects identity at the start of every transaction on the session.
- The identity-free `get_db_session` was removed, and a test fails the build if it returns.
- `admin_db_session` is an async context manager, not a FastAPI dependency, so it cannot be
  injected into an endpoint. Four paths use it, each with a declared reason: MCP credential
  verification, job execution, the readiness probe, and startup verification.
- Migration 0020 hardens every policy to `auth.uid() IS NOT NULL AND user_id = auth.uid()`, drives
  the policy loop off `pg_catalog` so no table can be forgotten, grants the `authenticated` role
  per-table privileges, adds parent-ownership `EXISTS` checks on `document_chunks`, `embeddings`,
  and `embedding_jobs`, adds a self-scoped `profiles` INSERT policy, and revokes `UPDATE`/`DELETE`
  on `audit_logs` and all privileges on `integration_tokens` from `authenticated`.

**Verdict: BLOCKED overall.** The gate document breaks this into four sub-verdicts, which is the
honest framing: RLS ACTIVE FOR API is PASS (statically enforced), ADMIN SEPARATION is PASS,
CROSS-TENANT is BLOCKED, POOL CLAIM ISOLATION is BLOCKED. The twelve tests that would prove tenant
denial and pool safety all skip.

**Known risk worth remembering.** The `after_begin` re-injection listener has never executed against
a live PostgreSQL server. It issues statements through SQLAlchemy's sync connection facade inside
the asyncio greenlet context. If that path misbehaves the failure is loud and fail-closed — queries
run without claims and RLS denies them — but it is the single most important thing to exercise the
moment a dev database exists.

### G3 — Postgres E2E and G4 — Real RAG: deliberately skipped

Both were skipped by explicit user decision, not by failure and not by oversight. G3 would have run
the full end-to-end lifecycle against a migrated PostgreSQL; G4 would have wired real document byte
extraction, real Gemini embeddings, and cosine-ranked semantic retrieval. Their absence is the
direct cause of two of the most visible product gaps: document upload cannot succeed, and search is
keyword-only with a null score. The E2E harness from an earlier prompt is preserved intact under
`apps/web/e2e/` and `docs/production-recovery/13_CORE_E2E_GATE.md`.

### G5 — MCP Write Exposure and Finalize (registration/authorization PASS, gate BLOCKED)

**What was broken.** Eleven write tools were fully implemented on `MCPDomainTools` in
`app/mcp/tools.py` and registered nowhere, so no MCP client could reach them. Two of them were also
broken in ways that guaranteed runtime failure: `finalize_work_session` constructed
`Memory(linked_project_id=...)`, a column that does not exist on the model, so any session with a
finding raised `TypeError`; and `'work_session'` was not a member of the canonical
`interaction_type` enum, so every finalize call against real PostgreSQL would have failed on insert.

**What changed.**

- `app/mcp/server.py` (400 changed lines) registers all eleven on the official MCP SDK server, and
  `app/mcp/router.py` (486 changed lines) exposes them through `POST /mcp/tools/invoke` with
  declared JSON input schemas. The registered surface is 20 tools: 9 read/draft plus 11 write.
- `GET /mcp` reports `"write_tools_status": "EXPOSED_SCOPE_ENFORCED"` (verified at
  `router.py:401`) along with the tool names and the required scope set.
- `app/mcp/security.py` defines the granular scopes. Authorization order is fixed: resolve the
  owner from the verified credential, verify every required scope (403 before any SQL), open
  `rls_db_session(user_id)`, execute, commit once.
- New `app/mcp/extraction.py` (215 lines) performs session extraction. It has no database import
  and no session parameter, so a transaction structurally cannot be held open across model
  inference. It degrades to a deterministic parser and reports its own mode in
  `provenance.extraction` with `quality_validated: false`.
- Migration 0021 adds the `work_session` enum value, the `meta` JSONB and `deleted_at` columns the
  model already maps (backfilling from the existing `metadata` column), and the partial unique
  index `uq_interactions_work_session_client_request` on `(user_id, meta->>'client_request_id')`.

**Verdict: BLOCKED overall**, with MCP WRITE REGISTRATION, WRITE AUTHORIZATION, and PROVENANCE all
PASS, and IDEMPOTENCY PASS at the application layer but BLOCKED at the database layer. SQLite has no
partial unique index over a JSON expression, so it cannot stand in for the constraint.

**Extraction quality, measured honestly.** Five real gate documents from this repository were run
through the extractor with no Gemini key, so all five ran in deterministic fallback mode. Scored
across 5 sessions × 17 buckets = 85 observations: 1 correct, 4 partial, 4 wrong, 76 missing. The
gate document calls this POOR and does not claim any number for AI extraction, which is correct —
that number does not exist yet.

**Code/doc divergence.** `app/mcp/security.py` defines a seventh write scope,
`SCOPE_EVIDENCE_WRITE = "mcp:evidence:write"`, and includes it in the group grant, but no registered
tool requires it. `G5_MCP_FINALIZE_GATE.md` lists only six scopes. The gate document is accurate
about what is *enforced*; the code carries an extra scope constant that is currently inert.

### G5.5 — Network Relationship Intelligence (schema/multi-org/commitments PASS, queries BLOCKED)

**What was broken.** Two data-model limitations made relationship questions unanswerable.
`people.organization_id` was a single nullable UUID, so a founder who also advised two other
startups was unrepresentable and an affiliation could not be recorded as ended.
`interactions.commitments` was a `TEXT[]` with no direction, status, due date, or owner, so "what
did they promise me", "what do I owe them", and "what is overdue" all required re-parsing free text
on every read.

**What changed.** Migration 0022 adds two tables. `person_organization_roles` (14 columns) allows
many affiliations per person with `started_at`/`ended_at` history, a partial unique index on live
rows so a re-run importer cannot fan out duplicates, and a `BEFORE INSERT OR UPDATE` trigger
refusing a role that joins a person and an organization owned by different users. `commitments`
(18 columns) carries `direction` (`owed_to_me` | `owed_by_me` | `unspecified`), `status`, `due_at`,
`completed_at`, and seven partial indexes.

Neither legacy field is dropped — `DROP COLUMN` does not appear in migration 0022, and a test
asserts that. Both are backfilled and then marked deprecated with `COMMENT ON COLUMN`. Migrated
commitments get `direction = 'unspecified'` because the array never recorded one; the migration
refuses to guess, which means those rows appear in neither directional ledger. That is the honest
answer, and it is worth remembering when the ledger looks emptier than expected after a backfill.

The query surface lives in `repositories/network.py` (399 changed lines), `services/network.py`
(337 changed lines), `schemas/network.py` (143 lines, new), and eighteen endpoints added to
`api/v1/endpoints/network.py`, all obtaining sessions through `get_rls_db_session` via
`dependencies/services.py`. Verified endpoint paths include `POST|GET /people/{person_id}/organizations`,
`PATCH|DELETE /network/roles/{id}`, the full `/commitments` CRUD plus `/commitments/{id}/complete`,
`/network/overview`, `/organizations/{id}/summary`, `/organizations/{id}/people`,
`/network/people/{person_id}/relationship`, `/network/stale-contacts`, and
`/network/ventures/{venture_id}/people`.

No relationship score, warmth index, or strength rating is computed anywhere. `founders_known` is a
literal substring match on recorded role text. Graph visualization was explicitly out of scope and
none was built.

**Verdict:** NETWORK SCHEMA, MULTI-ORG, and COMMITMENTS are PASS. NETWORK QUERIES is
PASS (application) / BLOCKED (PostgreSQL backfill and RLS), because the backfill uses `unnest()`
over `TEXT[]` and `CROSS JOIN LATERAL`, neither of which SQLite can execute.

---

## 4. File-level change map

`git diff --stat 143eda9..b1937d1` reports **84 files changed, 9,580 insertions, 503 deletions**.

### Deleted files

| File | Lines removed | Why |
|---|---|---|
| `apps/api/app/database.py` | 24 | Duplicate engine module with a silent in-memory SQLite fallback. Zero importers. Deleted at G1 so there is exactly one engine. |
| `apps/api/scratch_colspec.py` | 54 | Dead scratch file containing `create_all`. Deleted at G1. |
| `apps/web/e2e/essential-flows.spec.ts` | 47 | Replaced by the restructured Playwright suite (`core-lifecycle`, `cross-tenant`, `negative.authenticated`, `unauthenticated`). |

### New API modules

| File | Lines | Purpose |
|---|---|---|
| `app/db/__init__.py` | 17 | Re-exports the schema contract constants. |
| `app/db/schema_contract.py` | 298 | The written schema contract: required tables, critical columns with type families, required foreign keys, pgvector dimension, and the ordered `MIGRATION_FILES` list. |
| `app/db/schema_verify.py` | 179 | Verifies a live database against the contract. Refuses any non-PostgreSQL dialect outright. |
| `app/db/rls.py` | 96 | The single source of RLS identity: claim set, allowed roles, ordered `set_config` statements, identity probe SQL. |
| `app/ai/embeddings_storage.py` | 80 | Rejects string, truncated, and wrong-dimension vectors so a fake embedding cannot report success. |
| `app/mcp/extraction.py` | 215 | Work-session extraction with no database import, so inference cannot hold a transaction. |
| `app/models/rag.py` | 84 | ORM mappings for `document_chunks`, `embeddings`, `embedding_jobs` with `Vector(768)`. |
| `app/repositories/rag.py` | 62 | Data access for the RAG tables. No chunking, embedding, or ranking. |
| `app/schemas/network.py` | 143 | Request/response models for the roles and commitments surface. |
| `app/schemas/__init__.py` | 23 | New package init for the schemas package. |

### Substantially rewritten API modules

`app/mcp/router.py` (+486) and `app/mcp/server.py` (+400) carry the write-tool registration.
`app/repositories/network.py` (+399) and `app/services/network.py` (+337) carry the relationship
queries. `app/api/v1/endpoints/network.py` (+256) adds the eighteen new endpoints.
`app/models/entities.py` (+151) adds `PersonOrganizationRole` and `Commitment` and remaps
`Document` onto the canonical columns. `app/dependencies/database.py` (+161) became the RLS session
layer. `app/dependencies/services.py` (+67) wires the new services onto `get_rls_db_session`.
`app/integrations/google_client.py` (−97 net of a 97-line change) lost its simulation.
`app/jobs/handlers/document_processing.py` (70 changed lines) lost its fabrication.
`app/config.py` (+43), `app/core/errors.py` (+43), `app/mcp/security.py` (+33),
`app/mcp/tools.py` (+29), `app/jobs/handlers/sync_google.py` (+41), `app/jobs/runner.py` (+6),
`app/main.py` (+6), `app/ai/retrieval.py` (+36) round out the API changes.

### Migrations

Five new files, covered in section 5.

### Tests

| File | Tests | Category |
|---|---|---|
| `tests/test_g0_truth_gate.py` | 7 | unit |
| `tests/test_g1_one_schema.py` | 12 | unit |
| `tests/test_g2_rls_security.py` | 22 | unit |
| `tests/test_g5_mcp_write_gate.py` | 23 | unit |
| `tests/test_g5_5_network_intelligence.py` | 22 | unit |
| `tests/integration/test_postgres_schema_contract.py` | 5 | postgres |
| `tests/integration/test_rls_cross_tenant.py` | 12 | postgres |
| `tests/integration/test_mcp_finalize_postgres.py` | 4 | postgres |
| `tests/integration/test_network_intelligence_postgres.py` | 8 | postgres |

Plus `tests/integration/__init__.py` and `tests/integration/conftest.py` (28 lines), which define
the `requires_postgres` skip marker. `apps/api/conftest.py` (13 lines, new at repo-API root) pins
the SQLite unit environment before `app.config` imports. `pyproject.toml` gained the `postgres`
marker and the `pgvector>=0.3.0` dependency.

### Scripts

`scripts/db/bootstrap_migrations.py` (190 lines, new). Refuses any URL containing `prod`,
`production`, or `live`; installs an `auth.users` / `anon` / `authenticated` / `auth.uid()` shim
that is a guarded no-op on Supabase; verifies the migrations directory matches `MIGRATION_FILES`;
applies migrations in contract order; grants sequence and function privileges to `authenticated`;
revokes everything on `integration_tokens`; then validates with `verify_migrated_schema()` and exits
non-zero on mismatch.

### Frontend and E2E

`apps/web/app/(dashboard)/settings/integrations/page.tsx` labels Google as disabled and not
implemented. The Playwright harness was restructured into `core-lifecycle.spec.ts` (249 lines),
`cross-tenant.spec.ts`, `negative.authenticated.spec.ts`, `unauthenticated.spec.ts`,
`auth.setup.ts`, and `helpers/credentials.ts` / `helpers/ui.ts`, with a rewritten
`playwright.config.ts` and a new `e2e/.env.example`.

### Documentation

New: `G0_TRUTH_GATE.md`, `G1_DATABASE_SCHEMA_GATE.md`, `G1_SCHEMA_MATRIX.md`,
`G2_RLS_SECURITY_GATE.md`, `G5_MCP_FINALIZE_GATE.md`, `G5_5_NETWORK_INTELLIGENCE.md`,
`13_CORE_E2E_GATE.md`, `13A_LOCAL_E2E_ENVIRONMENT.md`. Updated: `10_RELEASE_GATE.md`,
`MASTER_PRODUCTION_PLAN.md`, `integration_status.md`, `.gitignore`, `apps/api/.env.example`.

---

## 5. Migrations added in this range

Five migrations were added. **None of them has been applied to any database — not production, not
staging, not a local container.** They exist as files on disk and as entries in `MIGRATION_FILES`.

| File | Gate | What it does |
|---|---|---|
| `20260827000018_align_documents_with_application_contract.sql` | G1 | Additively adds `extension`, `extracted_text`, `chunking_state`, `error_state` to `public.documents`, and gives `title` a default so uploads cannot violate NOT NULL. Purely additive. |
| `20260827000019_create_jobs_and_exports_tables.sql` | G1 | Creates `public.jobs` (the generic async job queue) and `public.exports`, with RLS. These were ORM-mapped and actively written by the upload path, job runner, and export service, but existed in no migration. |
| `20260828000020_harden_rls_authorization_boundary.sql` | G2 | Rewrites every user-owned table's policies to `auth.uid() IS NOT NULL AND user_id = auth.uid()`, driven off `pg_catalog` so no table is missed. Grants `authenticated` per-table privileges. Adds parent-ownership checks on `document_chunks`, `embeddings`, `embedding_jobs`. Adds a self-scoped `profiles` INSERT policy. Revokes `UPDATE`/`DELETE` on `audit_logs` and all privileges on `integration_tokens` from `authenticated`. |
| `20260828000021_mcp_work_session_finalization.sql` | G5 | Adds `'work_session'` to the `interaction_type` enum; adds `meta` (JSONB) and `deleted_at` to `public.interactions`, backfilling `meta` from the existing `metadata` column; adds the partial unique index `uq_interactions_work_session_client_request` on `(user_id, meta->>'client_request_id')` for live work sessions. |
| `20260828000022_network_relationship_intelligence.sql` | G5.5 | Creates `person_organization_roles` and `commitments` with full RLS in the G2 form; backfills both from `people.organization_id` and `interactions.commitments[]`; adds the live-affiliation unique index, the cross-tenant ownership trigger, and seven commitment indexes; marks both legacy fields deprecated with `COMMENT ON COLUMN`. Contains no `DROP COLUMN`. |

The contract in `app/db/schema_contract.py` lists 22 migrations total, ending at 0022, and the
bootstrap script fails loudly if the directory and the contract disagree.

Because startup runs `verify_database_ready()` and the contract now requires `person_organization_roles`,
`commitments`, `jobs`, `exports`, and the new `documents` columns, **the current code will refuse to
start against the existing production database** until 0018–0022 are applied there. That is intended
fail-closed behavior, but it means this branch is not deployable as-is without a migration step.

---

## 6. Behavior changes a user or client will notice

| Surface | Before | Now |
|---|---|---|
| Document upload / processing | Reported success with fabricated extracted text | Job fails: `processing_status="failed"`, `error_state="DOCUMENT_EXTRACTION_NOT_IMPLEMENTED"`, `extracted_text` cleared, HTTP **501** on the error path |
| Search results | `score: 0.89` on every hit, labelled hybrid/semantic | `score: null`, `confidence_available: false`, `search_mode: "keyword"` |
| Google OAuth callback | Wrote a connected row with a simulated refresh token | Returns `status: "not_implemented"`, writes nothing |
| Google Drive / Calendar sync | Returned invented counts | Raises `INTEGRATION_NOT_IMPLEMENTED`, HTTP **501** |
| Settings → Integrations UI | Showed Google as connectable | Labels Google as DISABLED / NOT IMPLEMENTED |
| MCP tool surface | 9 read/draft tools; writes existed in code but were unreachable | 20 tools. `GET /mcp` reports `write_tools_status: "EXPOSED_SCOPE_ENFORCED"`. Write calls without the matching `mcp:*:write` scope get **403** before any SQL runs |
| MCP `finalize_work_session` | Would have crashed (`TypeError`, then an enum violation on PostgreSQL) | Runs; extracts outside the transaction; idempotent on replay of `client_request_id` |
| Network / CRM API | One organization per person; commitments as free text | Eighteen new endpoints for multi-org affiliations, a directional commitment ledger, overdue detection, stale contacts, and organization summaries |
| Application startup | Created missing tables outside production | Verifies the migrated schema and fails closed if it does not match |
| Any non-unit environment pointed at SQLite | Started happily | Raises a configuration error at settings construction, and again at startup |

The startup change is the one most likely to surprise. If you point this branch at a database that
has not had 0018–0022 applied, it will not boot. That is correct behavior, not a regression.

---

## 7. Test suite state

Counts below are from `python -m pytest apps/api/tests/ --collect-only -q` run against `b1937d1`.

| Category | Files | Tests | Status |
|---|---|---|---|
| Unit (`tests/*.py`) | 18 | **150** | Run and pass against the in-memory SQLite fixture |
| Postgres integration (`tests/integration/`) | 4 | **29** | All skipped |
| **Total** | 22 | **179** | 150 passed / 0 failed / 29 skipped |

This matches the figures recorded in `G5_5_NETWORK_INTELLIGENCE.md` exactly, which is a good sign
that the gate document was written from a real run.

Unit test counts by file: `test_g5_mcp_write_gate.py` 23, `test_g2_rls_security.py` 22,
`test_g5_5_network_intelligence.py` 22, `test_g1_one_schema.py` 12, `test_storage_client.py` 10,
`test_pdf_analysis.py` 9, `test_auth_security.py` 8, `test_g0_truth_gate.py` 7,
`test_crm_memory.py` 5, `test_founder_domain.py` 5, `test_knowledge_ai.py` 5,
`test_production_startup_and_pagination.py` 5, `test_security_suite.py` 5, `test_health.py` 4,
`test_integrations_export.py` 3, `test_mcp_auth.py` 3, `test_mcp_api.py` 1, `test_mcp_tools.py` 1.

### Exactly which suites skip, and why

All 29 skips come from `tests/integration/`, gated by a single `pytest.mark.skipif` in
`tests/integration/conftest.py` that fires when `POSTGRES_TEST_DATABASE_URL` is unset. The skip
reason is `POSTGRES INTEGRATION BLOCKED: set POSTGRES_TEST_DATABASE_URL to a migrated
development/staging PostgreSQL database (never production).`

| Suite | Tests | What is unproven while it skips |
|---|---|---|
| `test_postgres_schema_contract.py` | 5 | That the migrated schema actually matches `schema_contract.py`: tables, column types, RAG foreign keys, pgvector dimensions, the `vector` extension |
| `test_rls_cross_tenant.py` | 12 | Cross-tenant SELECT/UPDATE/DELETE/INSERT denial, the unfiltered-query defense-in-depth case, transaction-local claim expiry, pooled-connection claim isolation, the `authenticated` role being active, admin separation, token-vault inaccessibility, and the catalog-wide policy audit |
| `test_mcp_finalize_postgres.py` | 4 | The finalize path end to end on real PostgreSQL, and the partial unique index enforcing idempotency at the database layer |
| `test_network_intelligence_postgres.py` | 8 | The two backfills, RLS on the two new tables, the cross-tenant ownership trigger, and the live-affiliation unique index |

The critical thing to internalize: **the SQLite unit suite does not prove database parity.** It has
no roles, no GUCs, no policies, no triggers, no `unnest()` over arrays, and no partial unique index
over a JSON expression. Everything that matters most about G1, G2, G5 idempotency, and G5.5 backfill
is in the skipped 29.

---

## 8. How to unblock

Every BLOCKED verdict in this run has the same root cause: no PostgreSQL was reachable from the
machine the work was done on. One environment variable closes almost all of them.

### Environment variables actually referenced in the code

Verified against `app/config.py`, `tests/integration/conftest.py`, `scripts/db/bootstrap_migrations.py`,
and `apps/api/.env.example`:

| Variable | Read by | Required for |
|---|---|---|
| `POSTGRES_TEST_DATABASE_URL` | `Settings` (default `""`), `tests/integration/conftest.py`, `bootstrap_migrations.py` | The bootstrap script and the entire postgres integration category. This is the one that matters. |
| `DATABASE_URL` | `Settings` (default `postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres`) | Running the API itself against your dev database |
| `DATABASE_SCHEMA_VERIFY` | `Settings` (default `True`) | Leave it `true`. Startup verifies the migrated schema and never creates it. |
| `ENVIRONMENT` / `APP_ENV` | `Settings` | Must not be `integration`/`e2e`/`staging`/`production` while `DATABASE_URL` is SQLite, or settings construction raises |
| `GEMINI_API_KEY` | `Settings` (default `"placeholder_gemini_key"`) | Scoring MCP extraction quality against real sessions |

`DEV_SUPABASE_URL`, `DEV_SUPABASE_SECRET_KEY`, and `DEV_SUPABASE_ANON_KEY` are documented in
`apps/api/.env.example` (commented out) and named in `G1_DATABASE_SCHEMA_GATE.md`, but I found **no
code in `apps/api/app` that reads them**. They are placeholders for a future dev-Supabase client,
not current requirements. Do not spend time on them to unblock the tests.

### Option A — local pgvector container (fastest)

```powershell
docker run -d --name sb-dev-pg -p 54322:5432 `
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres `
  pgvector/pgvector:pg16

$env:POSTGRES_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
python scripts/db/bootstrap_migrations.py
python -m pytest apps/api/tests/integration/ -v
```

The bootstrap script installs the `auth.users` table, the `anon` and `authenticated` roles, and
`auth.uid()` / `auth.jwt()` / `auth.role()` before applying migrations, because a plain container
has none of those and 62 foreign keys reference `auth.users`. That shim is what makes RLS testable
outside Supabase. Note the image must be a pgvector image — the migrations create `vector` columns.

### Option B — a separate development Supabase project

1. Create a **new** Supabase project. Do not reuse the production project.
2. Copy its connection string from Project Settings → Database.
3. Set the variable and run the same two commands:

```powershell
$env:POSTGRES_TEST_DATABASE_URL = "postgresql://postgres:<dev-password>@db.<dev-ref>.supabase.co:5432/postgres"
python scripts/db/bootstrap_migrations.py
python -m pytest apps/api/tests/integration/ -v
```

The script refuses any URL containing `prod`, `production`, or `live`. That guard is a safety net,
not a guarantee — a Supabase project reference is a random string, so it will not save you from
pasting the wrong project's URL. Check it yourself before running.

On Supabase the auth shim is a guarded no-op: it never overwrites the platform's `auth.users`, its
roles, or its `auth.*` functions.

### What each step converts

| Step | BLOCKED verdicts it converts |
|---|---|
| Bootstrap succeeds and schema validation passes | G1's "migrated PostgreSQL schema verified against a live database" — the last unmet G1 exit criterion |
| `test_postgres_schema_contract.py` passes (5) | G1 POSTGRES INTEGRATION BLOCKED → real result |
| `test_rls_cross_tenant.py` passes (12) | G2 CROSS-TENANT and POOL CLAIM ISOLATION → real results; G2 overall from BLOCKED to a defensible verdict. Also the first live exercise of the `after_begin` re-injection listener |
| `test_mcp_finalize_postgres.py` passes (4) | G5 FINALIZE E2E and the database half of IDEMPOTENCY |
| `test_network_intelligence_postgres.py` passes (8) | G5.5 NETWORK QUERIES backfill and RLS halves |
| Setting a real `GEMINI_API_KEY` and re-scoring the five sessions from G5 Phase 7 | The AI extraction quality blocker. Score correct/partial/wrong/missing per bucket, the same way the deterministic run was scored |

Adding `POSTGRES_TEST_DATABASE_URL` to CI secrets is what makes the drift and RLS suites protect the
repository going forward rather than being decorative.

---

## 9. What is still not built

Stated plainly, with no percentages.

- **Real document extraction.** `DocumentExtractor` exists and can parse txt/md/pdf, but the job
  handler does not call it. Uploading a document always ends in a failed job. G4 owns this.
- **Real embeddings.** No vector is ever persisted. `embeddings_storage.py` is a rejection gate, not
  a pipeline. The `embeddings`, `document_chunks`, and `embedding_jobs` tables are mapped and empty.
- **Semantic retrieval.** Search is a keyword/substring match. The SQL functions `match_memories`,
  `match_document_chunks`, and `hybrid_knowledge_search` exist in migration 0016 and are called by
  nothing.
- **AI confidence scores.** `score` is `None` by design and will stay that way until real ranking
  exists. Do not reintroduce a number here without a real cosine distance behind it.
- **Google OAuth, Drive, and Calendar.** Callback returns `not_implemented`; sync raises 501. There
  is no token exchange, no refresh, and no API client.
- **Graph visualization.** Explicitly out of G5.5 scope. The data model and query surface exist; no
  UI consumes them.
- **Gemini-backed MCP extraction quality.** Unvalidated. The only measured run is the deterministic
  fallback, which scored 1 correct out of 85 observations. No claim is made about the AI path.
- **First-class commitments from the MCP finalizer.** Verified in `app/mcp/tools.py`: the finalizer
  still constructs `Interaction(commitments=[...])`, writing to the array column that migration 0022
  deprecates. The deprecation is a comment, not a code migration. Until this is rerouted, new
  commitments created through MCP will not appear in the `commitments` ledger.
- **MCP tools for roles and commitments.** Deliberately out of G5.5 scope; the data model came first.
- **Non-core frontend stubs.** Ideas, KPIs, and similar surfaces still show toast stubs. Out of scope
  for every gate in this range.
- **Stale RLS documentation.** `docs/database/rls_policy_reference.md` and
  `docs/qa/database-and-rls-report.md` predate G2, still document the bare `user_id = auth.uid()`
  form, and claim verified isolation. Treat migration 0020 and the G2 test suite as authoritative
  and re-derive those documents from the live catalog once a database exists.

---

## 10. Recommended next steps, in priority order

1. **Stand up a dev PostgreSQL and run `scripts/db/bootstrap_migrations.py`.** One afternoon of work
   converts 29 skipped tests into real results and resolves the BLOCKED half of four gates. Nothing
   else on this list should happen first, because everything else is built on assumptions this step
   validates. Pay particular attention to whether the `after_begin` claim re-injection works, since
   it has never executed against a live server.
2. **Add `POSTGRES_TEST_DATABASE_URL` to CI.** Without it the drift and RLS suites skip in CI too,
   which means they protect nothing.
3. **Apply 0018–0022 to whatever database this branch is meant to run against.** The current code
   will not start otherwise, because `verify_database_ready()` requires the new tables and columns.
   Do this in a maintenance window, and take a backup first — 0022 runs backfills.
4. **Re-derive the stale RLS documentation from the live catalog** once step 1 is done, so the two
   pre-G2 documents stop contradicting the migrations.
5. **Route the MCP finalizer's commitments into `public.commitments`** with a real direction. This is
   a small change with a large payoff: it is the last thing writing to a column the schema now calls
   deprecated, and it makes every commitment created through MCP queryable by the G5.5 ledger.
6. **Score AI extraction quality with a real `GEMINI_API_KEY`** against the five sessions from G5
   Phase 7. Until this exists, `finalize_work_session` is running on a parser that scored 1 correct
   out of 85 observations.
7. **Do G4: real extraction and embeddings.** This is the largest remaining piece of product value
   and the one that turns the RAG tables from mapped-and-empty into the actual point of the product.
   It also unblocks a non-null search score.
8. **Do G3: the E2E lifecycle against PostgreSQL.** The Playwright harness is already written and
   preserved; it needs an environment, which step 1 largely provides.
9. **Google OAuth**, if it is still wanted. It is currently the most visible honest-but-broken
   surface in the UI.
10. **Consolidate the overlapping job and export tables.** `jobs`/`exports` from migration 0019
    overlap with the older `sync_jobs`/`export_jobs`/`export_items`. This is product cleanup, not
    urgent, but it will get more expensive the longer both sets carry data.

---

## Appendix: divergences between the gate documents and the code

Recorded here so they are not rediscovered later. In all three cases the code is authoritative.

| Divergence | Detail |
|---|---|
| G0 test count | `G0_TRUTH_GATE.md` Phase 8 lists 6 assertions; `tests/test_g0_truth_gate.py` collects 7 tests. The file was rewritten at G5 and the prose was not updated. |
| MCP write scope count | `G5_MCP_FINALIZE_GATE.md` lists six `mcp:*:write` scopes. `app/mcp/security.py` also defines `SCOPE_EVIDENCE_WRITE = "mcp:evidence:write"` and includes it in the group grant, but no registered tool requires it. The document is accurate about what is enforced; the constant is currently inert. |
| Dev Supabase variables | `G1_DATABASE_SCHEMA_GATE.md` presents `DEV_SUPABASE_URL`, `DEV_SUPABASE_SECRET_KEY`, and `DEV_SUPABASE_ANON_KEY` in a table of "required variable names". No code under `apps/api/app` reads them. Only `POSTGRES_TEST_DATABASE_URL` is required to unblock the integration suite. |

Historical test counts quoted inside the individual gate documents (71 at G0, 88 at G1, 122 at G2,
149 at G5, 179 at G5.5) are point-in-time snapshots and are correct as history. The current count is
179, which matches G5.5 because G5.5 is the last gate in this range.
