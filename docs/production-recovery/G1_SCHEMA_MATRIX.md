# G1 — Schema Matrix (Canonical Inventory)

**Source of truth (LOCKED):**

| Layer | Role |
|-------|------|
| `supabase/migrations/` | **Canonical schema authority** — the only place schema is defined |
| SQLAlchemy models | **Application mappings** onto the canonical schema |
| `Base.metadata` | **NOT** a deployment mechanism — never used to create runtime schema |
| SQLite | Isolated **unit-test fixture only** |

Contract encoded in code: `apps/api/app/db/schema_contract.py`
Runtime/CI verification: `apps/api/app/db/schema_verify.py`, `apps/api/tests/integration/test_postgres_schema_contract.py`

---

## A. CREATE TABLE inventory from migrations (62 tables)

| Migration | Tables |
|-----------|--------|
| 0003 profiles & triggers | `profiles` |
| 0004 founder execution | `ventures`, `projects`, `tags`, `project_members`, `tasks`, `task_comments`, `task_tags` |
| 0005 CRM | `organizations`, `people`, `relationships`, `interactions`, `interaction_participants`, `person_venture_links`, `person_project_links` |
| 0006 memory | `meetings`, `meeting_participants`, `memories`, `memory_people`, `memory_projects`, `memory_ventures`, `memory_tags` |
| 0007 ideas & decisions | `ideas`, `idea_people`, `idea_projects`, `idea_memories`, `decisions`, `decision_people` |
| 0008 documents & vectors | `documents`, `decision_documents`, `document_links`, `document_chunks`, `embeddings`, `memory_embeddings`, `embedding_jobs` |
| 0009 KPIs & portfolio | `kpis`, `kpi_definitions`, `kpi_entries`, `achievements`, `achievement_evidence`, `portfolio_case_studies`, `case_study_sources` |
| 0010 AI & content | `ai_conversations`, `ai_messages`, `ai_message_sources`, `content_items`, `content_versions`, `content_sources`, `weekly_reviews`, `weekly_review_sources` |
| 0011 integrations & jobs | `integrations`, `integration_tokens`, `sync_jobs`, `export_jobs`, `export_items` |
| 0012 audit | `audit_logs` |
| 0017 evidence & graph | `work_sessions`, `evidence_items`, `portfolio_evidence`, `entity_edges` |
| **0018 (new, G1)** | *(no new tables — additive columns on `documents`)* |
| **0019 (new, G1)** | `jobs`, `exports` |

Non-table migrations: 0001 extensions, 0002 enums, 0013 validation functions, 0014 indexes, 0015 RLS, 0016 search functions.

---

## B. SQLAlchemy `__tablename__` inventory (33 mappings)

`profiles`, `ventures`, `people`, `organizations`, `interactions`, `relationships`, `projects`, `tasks`,
`meetings`, `meeting_participants`, `memories`, `memory_embeddings`, `ideas`, `decisions`,
`documents`, `document_chunks`*, `embeddings`*, `embedding_jobs`*, `kpis`, `kpi_entries`,
`achievements`, `portfolio_case_studies`, `content_items`, `content_versions`, `weekly_reviews`,
`integrations`, `jobs`, `exports`, `audit_logs`, `work_sessions`, `evidence_items`,
`portfolio_evidence`, `entity_edges`

\* Added in G1 (`apps/api/app/models/rag.py`).

---

## C. Tables reached by repositories / services

| Table | Accessor |
|-------|----------|
| `profiles` | `repositories/profiles.py` |
| `ventures`, `projects`, `tasks` | `repositories/ventures.py`, `projects.py`, `tasks.py`, `services/founder.py` |
| `people`, `organizations`, `relationships` | `repositories/crm.py`, `network.py`, `services/network.py` |
| `interactions` | `repositories/interactions.py` |
| `meetings`, `meeting_participants` | `repositories/meetings.py` |
| `memories`, `memory_embeddings` | `repositories/memories.py`, `knowledge.py` |
| `ideas`, `decisions` | `repositories/knowledge.py` |
| `documents` | `repositories/knowledge.py`, `services/knowledge.py`, `jobs/handlers/document_processing.py` |
| `document_chunks`, `embeddings`, `embedding_jobs` | `repositories/rag.py` (mappings only; pipeline is G4) |
| `kpis`, `kpi_entries`, `achievements`, `portfolio_case_studies` | `repositories/knowledge.py` |
| `content_items`, `content_versions`, `weekly_reviews` | `repositories/knowledge.py` |
| `integrations`, `jobs`, `exports`, `audit_logs` | `repositories/integrations.py`, `jobs/runner.py`, `jobs/handlers/export_markdown.py` |
| `work_sessions`, `evidence_items`, `portfolio_evidence`, `entity_edges` | `repositories/mcp.py` |

---

## D. SQL functions (15)

| Function | Migration |
|----------|-----------|
| `set_updated_at()` | 0003 |
| `handle_new_user()` | 0003 |
| `handle_task_completion()` | 0004 |
| `update_person_last_interaction()` | 0005 |
| `validate_project_venture_ownership()` | 0013 |
| `validate_task_relationships()` | 0013 |
| `validate_person_organization_ownership()` | 0013 |
| `validate_memory_links()` | 0013 |
| `validate_document_links()` | 0013 |
| `validate_interaction_participants()` | 0013 |
| `match_memories(query_embedding vector(768), ...)` | 0016 |
| `search_people_by_text(...)` | 0016 |
| `search_tasks_by_text(...)` | 0016 |
| `match_document_chunks(query_embedding vector(768), ...)` | 0016 |
| `hybrid_knowledge_search(query_embedding vector(768), ...)` | 0016 |

The vector search functions exist in SQL but are **not yet called by application code** — semantic retrieval is G4.

---

## E. pgvector columns and indexes

| Object | Definition |
|--------|-----------|
| `embeddings.embedding` | `extensions.vector(768)` NOT NULL |
| `memory_embeddings.embedding` | `extensions.vector(768)` nullable |
| `idx_embeddings_hnsw_cosine` | HNSW `vector_cosine_ops`, m=16, ef_construction=64 |
| `idx_memory_vector` | IVFFlat `vector_cosine_ops`, lists=100 |

Application side: `VectorType` now delegates to the **official** `pgvector.sqlalchemy.Vector(768)` on PostgreSQL and falls back to JSON-encoded `TEXT` only for the SQLite unit fixture. The previous hand-rolled `UserDefinedType` `get_col_spec` shim is gone. `pgvector>=0.3.0` added to `apps/api/pyproject.toml`.

---

## F. Foreign keys

~133 `REFERENCES` constraints across the canonical schema, of which **62 point at `auth.users(id)` with `ON DELETE CASCADE`** (ownership root). Most-referenced domain parents: `people`, `projects`, `ventures` (12 each), `memories` and `documents` (5 each).

RAG integrity FKs asserted by the contract:

| Child | Parent |
|-------|--------|
| `document_chunks.document_id` | `documents.id` |
| `embeddings.document_chunk_id` | `document_chunks.id` |
| `embedding_jobs.document_chunk_id` | `document_chunks.id` |

---

## G. RLS-enabled tables

| Group | Tables |
|-------|--------|
| Standard owner isolation (0015 macro, 52 tables) | all founder/CRM/memory/idea/document/KPI/AI/content/integration domain tables |
| Evidence & graph (0017 macro) | `work_sessions`, `evidence_items`, `portfolio_evidence`, `entity_edges` |
| **Jobs & exports (0019 macro, new)** | `jobs`, `exports` |
| `profiles` | policies keyed on `id = auth.uid()` |
| `integration_tokens` | RLS enabled, **zero policies** (service-role-only vault) |
| `audit_logs` | SELECT + INSERT only (append-only history) |

---

## H. Classification of every canonical table

### MAPPED (application model exists) — 33

`profiles`, `ventures`, `projects`, `tasks`, `organizations`, `people`, `relationships`, `interactions`,
`meetings`, `meeting_participants`, `memories`, `memory_embeddings`, `ideas`, `decisions`,
`documents`, `document_chunks`, `embeddings`, `embedding_jobs`, `kpis`, `kpi_entries`, `achievements`,
`portfolio_case_studies`, `content_items`, `content_versions`, `weekly_reviews`, `integrations`,
`jobs`, `exports`, `audit_logs`, `work_sessions`, `evidence_items`, `portfolio_evidence`, `entity_edges`

### SQL-ONLY INTENTIONAL — 29

Join/link tables and future-domain tables that are correctly reached through parent aggregates, raw SQL,
or Supabase functions. **These do not require ORM models.**

`tags`, `task_tags`, `task_comments`, `project_members`, `interaction_participants`,
`person_venture_links`, `person_project_links`, `memory_people`, `memory_projects`, `memory_ventures`,
`memory_tags`, `idea_people`, `idea_projects`, `idea_memories`, `decision_people`, `decision_documents`,
`document_links`, `kpi_definitions`, `achievement_evidence`, `case_study_sources`, `ai_conversations`,
`ai_messages`, `ai_message_sources`, `content_sources`, `weekly_review_sources`, `integration_tokens`,
`sync_jobs`, `export_jobs`, `export_items`

Notes:
- `integration_tokens` is deliberately service-role-only; credentials are handled by
  `services/mcp/credential_service.py` rather than a browser-reachable ORM mapping.
- `sync_jobs` / `export_jobs` / `export_items` are the integration-specific queues; the application
  currently uses the generic `jobs` / `exports` queue. Consolidating them is **product work, not G1**.

### MISSING APPLICATION MAPPING — 0

Closed during G1: `document_chunks`, `embeddings`, `embedding_jobs` are now mapped in
`apps/api/app/models/rag.py` with repositories in `apps/api/app/repositories/rag.py`.

### OBSOLETE — 0

`ORM_OBSOLETE_TABLES` is now empty. `jobs` and `exports` were previously ORM-only with no canonical
table — that would have failed on real PostgreSQL — and are now defined by migration 0019.

### DUPLICATE — 1 resolved, 1 accepted

| Item | Resolution |
|------|-----------|
| `apps/api/app/database.py` vs `apps/api/app/dependencies/database.py` (two engines) | **Deleted** `app/database.py` (zero importers). `dependencies/database.py` is the single canonical engine/session. |
| `jobs`/`exports` vs `sync_jobs`/`export_jobs`/`export_items` | Overlapping intent, both canonical. Accepted for G1; consolidation deferred to product work. |

---

## I. Drift resolved during G1 (documents)

The ORM `Document` model and canonical `public.documents` had diverged. Fixed by mapping application
attribute names onto canonical column names plus additive migration 0018:

| Application attribute | Canonical column | Action |
|----------------------|------------------|--------|
| `filename` | `original_filename` | ORM remapped |
| `size_bytes` | `file_size` (BIGINT) | ORM remapped |
| `extension` | `extension` | added by 0018 |
| `extracted_text` | `extracted_text` | added by 0018 |
| `chunking_state` | `chunking_state` | added by 0018 |
| `error_state` | `error_state` | added by 0018 |
| `deleted_at` | `deleted_at` | added by 0018 |
| `title` | `title` (NOT NULL) | default added by 0018; ORM derives it from filename |
| `id`, `user_id` | `uuid` | ORM switched from `String(36)` to `FlexibleUUID` |

Also: `JSONEncodedDict` / `JSONEncodedList` now resolve to native **JSONB** on PostgreSQL (previously
they always bound JSON strings into `jsonb` columns, which real PostgreSQL rejects) while keeping the
JSON-encoded TEXT behaviour for the SQLite unit fixture.
