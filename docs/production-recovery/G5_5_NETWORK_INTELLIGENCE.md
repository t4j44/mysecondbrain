# G5.5 — NETWORK RELATIONSHIP INTELLIGENCE GATE

**Branch:** `recovery/core-daily-driver`
**Starting SHA:** `4d039ee`
**Ending local SHA:** _(recorded in the commit that lands this document)_
**Date:** 2026-08-28
**Owner:** Senior CRM / Relationship Graph Data Engineer

**Predecessors:** G0 Product Truth (PASS), G1 ONE SCHEMA (PASS), G2 RLS (implemented; Postgres
proof BLOCKED), G5 MCP Write Exposure (BLOCKED-but-implemented). G3 (Postgres E2E) and G4 (real
RAG) remain intentionally skipped by user decision and are **not** implemented here.

**Scope note:** this gate upgrades the *data model and query surface* only. Graph visualization
was explicitly out of scope and none was built.

---

## Verdicts

| Verdict | Result |
|---------|--------|
| **NETWORK SCHEMA** | **PASS** |
| **MULTI-ORG** | **PASS** |
| **COMMITMENTS** | **PASS** |
| **NETWORK QUERIES** | **PASS (application) / BLOCKED (PostgreSQL backfill + RLS)** |

The three schema/model verdicts are PASS because the tables, mappings, contract registration and
the full query surface exist and are proven by tests that run today. NETWORK QUERIES is qualified,
not inflated: every query is proven against the SQLite unit fixture, but migration 0022 has never
been applied to a real PostgreSQL, so the **backfill** and the **RLS boundary on the two new
tables** are unproven and reported BLOCKED. Nothing here is claimed as verified on PostgreSQL.

---

## Phase 1 — The limitations this gate closes

| Limitation (confirmed by audit) | Why it blocked relationship intelligence |
|---|---|
| `people.organization_id UUID` — a single nullable column | A person could belong to exactly one organization. A founder who also advises two other startups was unrepresentable, and there was no way to record that an affiliation *ended*. |
| `interactions.commitments TEXT[]` | A free-text bag with no direction, no status, no due date and no owner. "What did they promise me", "what do I owe them" and "what is overdue" were all unanswerable — the strings would have had to be re-parsed on every read. |

Neither field is dropped by this gate. Both are backfilled and then deprecated in place.

---

## Phase 2 — `person_organization_roles`

`supabase/migrations/20260828000022_network_relationship_intelligence.sql`, section 1.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID NOT NULL → `auth.users` CASCADE | ownership root |
| `person_id` | UUID NOT NULL → `people` CASCADE | |
| `organization_id` | UUID NOT NULL → `organizations` CASCADE | |
| `role` | TEXT | e.g. `Founder`, `Advisor`, `Head of Product` |
| `relationship_type` | TEXT NOT NULL DEFAULT `contact` | |
| `is_primary` | BOOLEAN NOT NULL DEFAULT false | a stored fact, not a ranking |
| `started_at` / `ended_at` | TIMESTAMPTZ | `ended_at IS NULL` = current affiliation |
| `source` | TEXT NOT NULL DEFAULT `manual` | provenance, e.g. `migrated:people.organization_id` |
| `confidence` | NUMERIC NOT NULL DEFAULT 1.0, CHECK 0–1 | |
| `deleted_at`, `created_at`, `updated_at` | TIMESTAMPTZ | `set_updated_at()` trigger |

A person may hold **many rows** across **many organizations**. History is retained by setting
`ended_at` rather than deleting, and `ck_person_organization_roles_window` rejects an end date
before the start date.

Two integrity guarantees beyond the FKs:

* `uq_person_organization_roles_live` — a partial unique index on
  `(user_id, person_id, organization_id, COALESCE(role, ''))` for live, un-ended rows. Re-running
  an importer cannot fan one real-world role out into duplicates.
* `validate_person_organization_role_ownership()` — a `BEFORE INSERT OR UPDATE` trigger that
  refuses a role joining a person and an organization owned by different users. The same rule is
  enforced in `PersonOrganizationRoleService.create_role` because the SQLite unit fixture has no
  triggers.

---

## Phase 3 — `commitments`

Section 2 of the same migration.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID NOT NULL → `auth.users` CASCADE | |
| `from_person_id` / `to_person_id` | UUID → `people` SET NULL | who owes whom |
| `organization_id`, `venture_id`, `project_id` | UUID → respective tables SET NULL | context |
| `interaction_id`, `meeting_id` | UUID → respective tables SET NULL | where it was made |
| `direction` | TEXT NOT NULL, CHECK | `owed_to_me` \| `owed_by_me` \| `unspecified` |
| `description` | TEXT NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT `open`, CHECK | `open` \| `completed` \| `cancelled` |
| `due_at`, `completed_at` | TIMESTAMPTZ | overdue = `open` AND `due_at < now()` |
| `source` | TEXT NOT NULL DEFAULT `manual` | provenance |
| `deleted_at`, `created_at`, `updated_at` | TIMESTAMPTZ | `set_updated_at()` trigger |

`direction` is the field that makes the ledger queryable in both directions.
`unspecified` exists for exactly one reason: the legacy array never recorded a direction, and this
migration refuses to invent one.

Seven partial indexes back the queries: `(user_id, status, due_at)`, a dedicated overdue index,
and one each for `from_person_id`, `to_person_id`, `organization_id`, `venture_id`,
`interaction_id`.

---

## Phase 4 — Migration and data preservation

**Nothing is dropped and nothing is discarded.** `DROP COLUMN` does not appear in migration 0022;
a test asserts this.

| Legacy source | Migrated to | Rule |
|---|---|---|
| `people.organization_id` (+ `people.role`, `people.relationship_type`, `people.created_at`) | one `person_organization_roles` row per person, `is_primary = true`, `source = 'migrated:people.organization_id'`, `started_at = people.created_at` | joined on matching `user_id` so a cross-tenant row can never be created; guarded by `NOT EXISTS` so re-running is safe |
| `interactions.commitments[]` | one `commitments` row per non-blank array element, `source = 'migrated:interactions.commitments'`, `status = 'open'` | `direction = 'unspecified'` — **never guessed**; the counterparty stays reachable through `interaction_id`, and `organization_id` is resolved from the interaction's person |

Both legacy columns are then marked with `COMMENT ON COLUMN ... 'DEPRECATED as of migration
0022 ... Retained (not dropped) for backward compatibility'`, and both new tables carry a
`COMMENT ON TABLE` naming them authoritative. Deprecated, not deleted: historical reads keep
working and pre-0022 data remains readable in its original form.

A migrated commitment with `direction = 'unspecified'` deliberately appears in neither "they
promised me" nor "I owe them". That is the honest answer for a record whose direction was never
captured; it still appears in the unfiltered ledger and in the person view via `interaction_id`.

---

## Phase 5 — Network queries

All implemented in `NetworkIntelligenceRepository` (`apps/api/app/repositories/network.py`) and
exposed through `NetworkIntelligenceService` / `CommitmentService` /
`PersonOrganizationRoleService`.

| Question | Endpoint | How it is answered |
|---|---|---|
| How many startups are in my network? | `GET /api/v1/network/overview?industry=startup` | count of organizations with ≥1 connected person, grouped by the **recorded** `industry`. The schema stores no company-stage field, so none is invented — "startup" is whatever the user recorded. |
| Who do I know at startup X? | `GET /api/v1/organizations/{id}/people` | join `people` × `person_organization_roles` |
| What role does each person have? | same endpoint | `role`, `relationship_type`, `is_primary`, `is_current` per row |
| When did I last speak to them? | same endpoint, and `/network/people/{id}/relationship` | `MAX(interactions.date)` for that person |
| What was discussed? | same | title + summary of the most recent interaction |
| What did they promise me? | `GET /api/v1/commitments?direction=owed_to_me&commitment_status=open` | |
| What do I owe them? | `GET /api/v1/commitments?direction=owed_by_me&commitment_status=open` | |
| Which commitments are overdue? | `GET /api/v1/commitments?overdue_only=true` | `status='open' AND due_at IS NOT NULL AND due_at < now()` |
| Which founders haven't I spoken to in 30 days? | `GET /api/v1/network/stale-contacts?days=30&founders_only=true` | LEFT JOIN against last-interaction; founder detected by literal role text on the affiliation **or** on `people.role`. A never-contacted contact is stale by definition and returns a **null** timestamp, not a fabricated one. |
| Who is relevant to Venture X? | `GET /api/v1/network/ventures/{id}/people` | people with interactions or commitments recorded against that venture, ordered by those counts |

Full CRUD is also exposed: `POST|GET /people/{id}/organizations`,
`PATCH|DELETE /network/roles/{id}`, `POST|GET /commitments`,
`GET|PATCH|DELETE /commitments/{id}`, `POST /commitments/{id}/complete`.

Every one of these obtains its session from `get_rls_db_session` via
`app/dependencies/services.py`, so G2 is unchanged: no identity-free session was introduced and
no endpoint issues `SET LOCAL` itself. `test_g2_rls_security.py` still passes in full.

---

## Phase 6 — Organization summary

`GET /api/v1/organizations/{id}/summary` returns exactly the required metrics:

```json
{
  "organization_id": "...", "name": "Summit Robotics", "industry": "startup",
  "connected_people_count": 1,
  "founders_known": 1,
  "last_interaction_at": "2026-08-25T09:12:00Z",
  "open_commitments": 2,
  "overdue_commitments": 1
}
```

Every value is a direct `COUNT`, a `MAX(date)` or a stored field. **No AI relationship score,
warmth index or strength rating is computed anywhere in this gate** — a test asserts the response
contains no key matching `score`.

`founders_known` is a literal substring match on the recorded role text (so `Co-Founder` counts,
`Advisor` does not), not an inference. A commitment counts against an organization when it names
the organization directly *or* when one of its connected people is on either side of it.

---

## Phase 7 — Contract and model registration (G1 preserved)

`supabase/migrations/` remains the sole schema authority. No `Base.metadata.create_all` runs
outside the SQLite unit fixture, and nothing here introduces SQLite anywhere else.

Updated in `apps/api/app/db/schema_contract.py`:

* `APPLICATION_REQUIRED_TABLES` += `person_organization_roles`, `commitments`
* `APPLICATION_REQUIRED_COLUMNS` += full column contracts for both tables (14 and 18 columns)
* `APPLICATION_REQUIRED_FOREIGN_KEYS` += `person_organization_roles.person_id → people.id`,
  `person_organization_roles.organization_id → organizations.id`,
  `commitments.interaction_id → interactions.id`
* `MIGRATION_FILES` += `20260828000022_network_relationship_intelligence.sql`

ORM mappings `PersonOrganizationRole` and `Commitment` added to `apps/api/app/models/entities.py`
using the existing `FlexibleUUID` / `utc_now` conventions of the CRM entities.

RLS on both new tables uses the G2 intentional form —
`auth.uid() IS NOT NULL AND user_id = auth.uid()` — for SELECT, INSERT, UPDATE and DELETE, with
`GRANT SELECT, INSERT, UPDATE, DELETE ... TO authenticated`. A test parses the migration and
asserts all four policies carry that exact predicate.

---

## Verification (exact)

| Gate | Command | Discovered | Passed | Failed | Skipped | Result |
|------|---------|------------|--------|--------|---------|--------|
| Backend pytest | `python -m pytest apps/api/tests/ -v` | **179** | **150** | **0** | **29** | **PASS** |
| Ruff | `python -m ruff check apps/api` | — | — | 0 | — | **PASS** (All checks passed) |
| Mypy | `python -m mypy apps/api/app` | 120 files | — | 0 | — | **PASS** (Success: no issues found) |
| Postgres integration | `python -m pytest apps/api/tests/integration/ -q` | 29 | 0 | 0 | **29** | **POSTGRES INTEGRATION BLOCKED** |
| Web gates | — | — | — | — | — | **NOT RUN** — no frontend file changed |

Baseline before this gate was 149 discovered / 128 passed / 21 skipped. The delta is **+30 tests**:

* `apps/api/tests/test_g5_5_network_intelligence.py` — **22 unit tests, all passing.**
  Covers: person in 2 organizations; Founder role; Advisor role; historical ended role retained
  and filterable; open / overdue / completed commitments separated; completing a commitment
  clearing it from the overdue ledger; last interaction and topic; founders not spoken to in 30
  days; industry-filtered network overview; venture relevance; the combined person view; and
  cross-user isolation across every new endpoint (including an attempt to affiliate a contact with
  another user's organization, and an attempted cross-tenant role update). Also asserts the
  migration contract: 0022 registered, `DROP COLUMN` absent, deprecation comments present,
  backfill present, direction not guessed, and the four policies in G2 owner form.
* `apps/api/tests/integration/test_network_intelligence_postgres.py` — **8 postgres-gated tests,
  all skipped.** Gated on `POSTGRES_TEST_DATABASE_URL` using the same
  `tests/integration/conftest.py` pattern as G1, G2 and G5.

Nothing was marked xfail, deleted or weakened to make a gate pass. All 29 skips are the postgres
category.

---

## Remaining blockers

| Blocker | Why | How to close |
|---|---|---|
| Migration 0022 has never been applied | No Docker, no psql, no Supabase CLI, no dev database credentials | Point `POSTGRES_TEST_DATABASE_URL` at a migrated dev/staging database (never production) and run `apps/api/tests/integration/` |
| Backfill fidelity (`people.organization_id` → roles, `interactions.commitments[]` → rows) | Requires real PostgreSQL: `unnest()` over `TEXT[]` and `CROSS JOIN LATERAL` have no SQLite equivalent | Same as above; `test_backfill_*` in the new integration file proves both |
| RLS denial on `person_organization_roles` and `commitments` | SQLite has no roles, GUCs or policies; unit isolation is owner-scoped predicates only | Same as above; `test_rls_hides_the_relationship_graph_from_other_tenants` proves it |
| Cross-tenant ownership trigger and the live-affiliation unique index | Neither exists in SQLite | Same as above |
| MCP surface for roles and commitments | Deliberately out of G5.5 scope — the data model came first | A later gate, if `finalize_work_session` should write first-class commitments instead of the legacy array |
| `interactions.commitments[]` still written by the MCP finalizer | Deprecation is a marker, not a code migration | Follow-up work: route finalize commitments into `public.commitments` with a real direction |
| Inherited G2 / G5 blockers | Unchanged | Same PostgreSQL requirement |

---

## Remote actions

**NO PUSH. NO PR. NO MERGE. NO DEPLOY. NO PRODUCTION SUPABASE CHANGES.**
All work is local commits on `recovery/core-daily-driver`. Migration 0022 exists on disk only and
has not been applied anywhere.
