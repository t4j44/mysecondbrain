# G5 — MCP WRITE EXPOSURE & FINALIZE WORK SESSION GATE

**Branch:** `recovery/core-daily-driver`
**Starting SHA:** `f4b0cbe`
**Ending local SHA:** `71c35d2`
**Date:** 2026-08-28
**Owner:** Senior MCP / Personal Work Intelligence Engineer

**Predecessors:** G0 Product Truth (PASS), G1 ONE SCHEMA (PASS), G2 RLS Security (BLOCKED-but-implemented).
G3 (Postgres E2E) and G4 (real RAG) are intentionally skipped by user decision and are **not** implemented here.

---

## Verdicts

| Verdict | Result |
|---------|--------|
| **MCP WRITE REGISTRATION** | **PASS** |
| **WRITE AUTHORIZATION** | **PASS** |
| **FINALIZE E2E** | **BLOCKED** |
| **IDEMPOTENCY** | **PASS (application) / BLOCKED (database constraint)** |
| **PROVENANCE** | **PASS** |
| **G5** | **BLOCKED** |

G5 is **BLOCKED**, not FAIL. Registration, authorization, provenance and application-level
idempotency are implemented and proven by tests that run today. Two things cannot be proven in
this environment and are therefore not claimed: the finalize path against a real migrated
PostgreSQL (no Docker, no psql, no Supabase CLI, no dev database credentials), and extraction
quality against real sessions with a live model (no Gemini key).

---

## Phase 1 — Audit of the 11 implemented-but-unregistered write tools

All eleven live on `MCPDomainTools` in `apps/api/app/mcp/tools.py`. Their logic was **not
rewritten**; only two genuine defects were fixed (below).

| Tool | Input schema (required) | Write scope | Repository / service | User isolation | Idempotency | Audit |
|------|------------------------|-------------|----------------------|----------------|-------------|-------|
| `create_task` | `title` | `mcp:tasks:write` | `Task` ORM | `user_id=self.user_id` on insert | none (each call creates) | `mcp.task.created` |
| `update_task` | `task_id` | `mcp:tasks:write` | `Task` ORM | `WHERE id AND user_id AND deleted_at IS NULL` | natural (same row) | `mcp.task.updated` |
| `complete_task` | `task_id` | `mcp:tasks:write` | `Task` ORM | same owner-scoped predicate | natural (idempotent status) | `mcp.task.completed` |
| `create_person` | `name` | `mcp:people:write` | `Person` ORM | owner-scoped scan + insert | **dedupe** by email, then exact name | `mcp.person.created` / `.deduplicated_matched` |
| `update_person` | `person_id` | `mcp:people:write` | `Person` ORM | owner-scoped predicate | natural | `mcp.person.updated` |
| `create_project` | `name` | `mcp:projects:write` | `Project` ORM | owner-scoped `lower(name)` match | **dedupe** by case-insensitive name | `mcp.project.created` |
| `update_project` | `project_id` | `mcp:projects:write` | `Project` ORM | owner-scoped predicate | natural | `mcp.project.updated` |
| `save_memory` | `title`, `content` | `mcp:memory:write` | `Memory` ORM | `user_id` on insert | none | `mcp.memory.saved` |
| `save_decision` | `decision` | `mcp:decisions:write` | `Decision` ORM | `user_id` on insert | none | `mcp.decision.saved` |
| `save_work_session` | `title` | `mcp:sessions:write` | `Interaction` ORM | `user_id` on insert | records `client_request_id` in meta but does not check it | `mcp.work_session.saved` |
| `finalize_work_session` | none (all optional) | all five write scopes | `Interaction`, `Decision`, `Task`, `Person`, `Memory`, `PortfolioCaseStudy` | every insert carries `user_id`; project/venture resolution is owner-scoped | **replay check** on `client_request_id` / `session_reference` / `conversation_reference` | `mcp.work_session.finalized` with per-domain counts |

**Two real defects found and fixed** (both would have failed at runtime, so neither was
"working logic"):

1. `finalize_work_session` constructed `Memory(linked_project_id=...)`, a column that does not
   exist on the model. Any session with at least one finding raised `TypeError`. Now written to
   `related_projects`.
2. `'work_session'` was not a member of the canonical `interaction_type` enum, so every finalize
   call against real PostgreSQL would have failed on insert. Added in migration 0021.

**No arbitrary-SQL tool exists or was added.** A regression test asserts that no registered tool
name or description offers SQL execution.

---

## Phase 2 — Registration

`apps/api/app/mcp/server.py` now registers all eleven on the official MCP SDK server, and
`apps/api/app/mcp/router.py` exposes them through the REST `/mcp/tools/invoke` compatibility
route with declared JSON input schemas.

Registered surface: **20 tools** = 9 read/draft (unchanged) + 11 write.

`GET /mcp` now reports the truth:

```json
{
  "write_tools_status": "EXPOSED_SCOPE_ENFORCED",
  "write_tools": ["create_task", "...", "finalize_work_session"],
  "write_scopes_required": ["mcp:decisions:write", "mcp:memory:write",
                            "mcp:people:write", "mcp:projects:write",
                            "mcp:sessions:write", "mcp:tasks:write"]
}
```

Write tools carry honest MCP annotations: `read_only_hint=false`, and `destructive_hint=true` on
the four tools that overwrite existing rows (`update_task`, `complete_task`, `update_person`,
`update_project`).

---

## Phase 3 — Authorization

Every write goes through `_write_domain(*scopes)` in `server.py` (or `_invoke_write_tool` on the
REST route). The order is fixed and cannot be bypassed:

1. Resolve the owner from the verified credential (never from client-supplied arguments).
2. `verify_scope` each required granular scope. A missing scope raises before any SQL runs —
   403 on the REST route, an authorization error on the SDK route.
3. Open `rls_db_session(user_id)`, so PostgreSQL RLS remains the second boundary (G2 unchanged).
4. Execute, then COMMIT once. Any exception rolls the whole batch back.

Granular scopes: `mcp:tasks:write`, `mcp:people:write`, `mcp:projects:write`,
`mcp:memory:write`, `mcp:decisions:write`, `mcp:sessions:write`. `finalize_work_session` writes
across five domains in one transaction, so it requires **all five** of
`sessions|tasks|decisions|memory|people:write`; a single `mcp:write` group grant satisfies them
all, so the low-friction path is unaffected.

Only arguments declared in a tool's input schema reach the domain layer; unknown keys (including
an attempted `user_id` override) are dropped. This is regression-tested.

**Read-only credentials receive 403 on all eleven write tools**, and a rejected call persists
nothing. Both are tested.

No identity-free session was introduced. `test_g2_rls_security.py` still passes, including
`test_endpoints_only_receive_rls_scoped_sessions` and
`test_no_module_bypasses_the_session_factory_for_user_work`.

---

## Phase 4 — Finalize workflow and transaction safety

Input stays low friction: `provider`, `session_reference`, `session_payload` (or `summary`),
optional `venture`, optional `project`, optional `title`, `client_request_id`.

Extracted buckets: objective, research, findings, decisions (with rationale and rejected
alternatives), tasks, people, organizations, commitments, evidence, source references,
artifacts, skills, portfolio candidates, open questions.

**Ordering is enforced structurally, not by convention.** `app/mcp/extraction.py` has no database
import and no session parameter; the tool awaits it to completion and only then enters
`_write_domain`:

```
extract (no DB)  →  validate & coerce  →  BEGIN
                                          → resolve project/venture (no phantom creation)
                                          → dedupe people, projects, open tasks
                                          → insert session, decisions, tasks, people, memories,
                                            staged portfolio drafts, audit log
                                        COMMIT
```

A transaction is therefore never held open across model inference.

Records that cannot be resolved are reported, not invented: an unmatched project or venture hint
produces an `unresolved_links` entry instead of a phantom row. Portfolio candidates are written
as **drafts requiring human review**, never as published artifacts.

---

## Phase 5 — Idempotency

Two layers:

* **Application:** replaying the same `client_request_id`, `session_reference` or
  `conversation_reference` returns the original session with `idempotent_replayed: true` and
  creates nothing. Proven for both key kinds, and proven to be per-owner (two users may use the
  same reference). Tasks additionally dedupe against open tasks with the same title, people
  against email/name, projects against case-insensitive name.
* **Database:** `supabase/migrations/20260828000021_mcp_work_session_finalization.sql` adds a
  partial unique index `uq_interactions_work_session_client_request` on
  `(user_id, meta->>'client_request_id')` for live work sessions. Because tasks, decisions,
  memories and evidence hang off the session, a single session guarantee is what prevents
  duplicate downstream records.

The migration also adds `'work_session'` to the `interaction_type` enum and the `meta` /
`deleted_at` columns the application model already maps (backfilling from the existing `metadata`
column).

The database layer is **BLOCKED for verification**: SQLite has no partial unique index over a
JSON expression, so it cannot stand in. `apps/api/tests/integration/test_mcp_finalize_postgres.py`
proves it and is skipped until `POSTGRES_TEST_DATABASE_URL` is set.

---

## Phase 6 — Provenance

* The session row stores provider, references, resolved context, every extracted bucket, the
  created-record summary, and how extraction was performed.
* Decisions carry the session URI in `supporting_documents`.
* Tasks carry `origin_session_id`, `origin_session_uri` and `provider`.
* Memories carry `origin_session_id` / `session_uri` and `source=work_session:<id>`.
* Every write emits an `AuditLog` row; finalize emits per-domain created counts.
* The tool response returns `provenance.session_uri`, `provider`, `client_request_id`, timestamp
  and the extraction telemetry.

Asserted end to end in `test_finalize_creates_the_full_record_set_with_provenance`.

---

## Phase 7 — Manual validation against REAL sessions

Five real completed AI work sessions from this repository were run through the extractor:
`G0_TRUTH_GATE.md`, `G1_DATABASE_SCHEMA_GATE.md`, `G2_RLS_SECURITY_GATE.md`,
`13_CORE_E2E_GATE.md`, `11_LOCAL_DIFF_REVIEW.md` (7.6k–18.2k characters each).

No Gemini key is available, so **every one of these ran in deterministic mode**. The numbers
below measure the deterministic fallback parser, not the intended AI extractor.

Scored across 5 sessions × 17 buckets = 85 observations:

| Outcome | Count | Examples |
|---------|-------|----------|
| Correct | 1 | G2 open questions (the residual-risk list was captured accurately) |
| Partial | 4 | G1 evidence and artifacts; G0/G2 artifacts (heading-derived file lists) |
| Wrong | 4 | 44 and 45 "artifacts" over-extracted from path headings; 13 "findings" that are markdown table delimiter rows; 2 "tasks" that are prose from a failure-semantics section |
| Missing | 76 | objective, decisions, work_completed, people, commitments, skills on all five sessions |

**Deterministic extraction quality on real sessions: POOR.** It only performs acceptably on
transcripts already shaped as tagged sections (as in the unit fixture). It is a safe fallback —
it never fabricates — but it is not the product.

**AI extraction quality: UNVALIDATED / BLOCKED.** No live key, therefore no number is claimed.
The extractor reports its own mode in `provenance.extraction`, with
`quality_validated: false` always set until a scored run exists.

To close this: set `GEMINI_API_KEY` and re-run the five sessions above, scoring
correct/partial/wrong/missing per bucket.

---

## Verification (exact)

| Gate | Command | Discovered | Passed | Failed | Skipped | Result |
|------|---------|------------|--------|--------|---------|--------|
| Backend pytest | `python -m pytest apps/api/tests/ -v` | **149** | **128** | **0** | **21** | **PASS** |
| Ruff | `python -m ruff check apps/api` | — | — | 0 | — | **PASS** (All checks passed) |
| Mypy | `python -m mypy apps/api/app` | 120 files | — | 0 | — | **PASS** (Success: no issues found) |
| Postgres integration | `python -m pytest apps/api/tests/integration/ -v` | 21 | 0 | 0 | **21** | **POSTGRES INTEGRATION BLOCKED** |
| Web gates | — | — | — | — | — | **NOT RUN** — no frontend file changed |

New G5 tests: `apps/api/tests/test_g5_mcp_write_gate.py` (23 unit tests, all passing) and
`apps/api/tests/integration/test_mcp_finalize_postgres.py` (4 postgres-gated tests, skipped).

All 21 skips are the postgres category, gated on `POSTGRES_TEST_DATABASE_URL` exactly as G1 and
G2 do. Nothing was marked xfail or deleted to make a gate pass.

---

## Remaining blockers

| Blocker | Why | How to close |
|---------|-----|--------------|
| Finalize E2E against real PostgreSQL | No Docker, psql, Supabase CLI or dev DB credentials | Point `POSTGRES_TEST_DATABASE_URL` at a migrated dev/staging database (never production) and run `apps/api/tests/integration/` |
| Database-level idempotency constraint | Migration 0021 is written but has never been applied | Same as above |
| AI extraction quality | No `GEMINI_API_KEY` | Configure a key, re-score the five real sessions from Phase 7 |
| G2 cross-tenant RLS denial | Inherited from G2 | Unchanged; same PostgreSQL requirement |
| Evidence is session metadata, not `evidence_items` rows | Deliberately out of G5 scope | A later gate, if evidence needs first-class querying |

---

## Remote actions

**NO PUSH. NO PR. NO MERGE. NO DEPLOY. NO PRODUCTION SUPABASE CHANGES.**
All work is local commits on `recovery/core-daily-driver`. Migration 0021 exists on disk only and
has not been applied anywhere.
