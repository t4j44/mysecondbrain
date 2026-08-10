# Database Schema Implementation Notes & Architectural Decisions — Taj's Second Brain

This technical memorandum explains key PostgreSQL implementation decisions, contract resolutions, index evaluations, and architectural patterns established during Phase 1 database engineering by **Agent 2**.

---

## 1. Deviations & Expansion from `database_schema.md` v1.0
While Agent 1's initial `database_schema.md` (v1.0) defined 10 foundational core tables, the production scope mandated by the Lead Orchestrator across all 9 PRD modules required expanding the relational footprint to **26 primary domain modules and 30 supporting junction/version tables (56 tables total)**.

### Contract Resolutions & Compatibility Protections
1. **Dual KPI Representation**: To avoid breaking tests targeting v1.0 `public.kpis` while supporting immutable target tracking without overwriting past entries, we retain `public.kpis` as a summarized dashboard compatibility table while implementing `public.kpi_definitions` and `public.kpi_entries` for rigorous historical analytics.
2. **Vector Table Alignment**: `database_schema.md` v1.0 defined `memory_embeddings`. We implement this table with exact v1.0 column specifications, while concurrently establishing `public.embeddings` and `public.embedding_jobs` to support multi-modal vector tracking (memories, document chunks, interactions) with versioning and checksum deduplication.
3. **Timestamp vs Field Naming**: Where existing specs varied between `due_date` vs `due_at`, or `date` vs `interaction_at`, we leverage PostgreSQL **Generated Stored Columns** (`due_at TIMESTAMPTZ GENERATED ALWAYS AS (due_date) STORED`) so that queries on either column succeed identically without performance penalties.
4. **Junction Tables over JSONB Arrays**: While lightweight entity references can be stored in JSONB or text arrays, formal many-to-many relationships (e.g. `memory_people`, `idea_projects`, `decision_documents`) are implemented as strictly indexed junction tables to preserve database referential integrity and facilitate graph queries.

---

## 2. PostgreSQL Implementation Decisions
- **`citext` Extension**: Utilized for emails, tags, venture slugs, and organization names to ensure case-insensitive uniqueness without relying on functional `LOWER()` indexes or application-side string mutation.
- **Timestamp Standardization**: All chronological fields use `TIMESTAMPTZ` set default to `NOW()` in UTC. Client timestamps are normalized at the database interface layer.
- **Automated Triggers**: Reusable `set_updated_at()` functions execute with `SECURITY DEFINER` and restricted `search_path` (`public, extensions`) to eliminate vulnerabilities from malformed search environments.

---

## 3. Index & Vector Strategy (HNSW vs IVFFlat)
### Vector Index Evaluation
- **IVFFlat (`memory_embeddings`)**: Configured with `lists = 100` to satisfy v1.0 design contracts. IVFFlat requires an initial training data population to calculate Voronoi cluster centroids efficiently.
- **HNSW (`embeddings`)**: Evaluated and implemented as the primary index for enterprise RAG retrieval (`HNSW with m = 16, ef_construction = 64`). **Rationale**: Unlike IVFFlat, Hierarchical Navigable Small World (HNSW) graphs require zero pre-existing training data, support instantaneous high-recall vector queries immediately upon individual record insertion, and handle continuous incremental knowledge growth gracefully without needing periodic re-indexing maintenance.

### Full-Text & Trigram Indexing
- **`pg_trgm` GIN Indexes**: Created across high-value text search columns (`people.name`, `tasks.title`, `memories.title`, `documents.title`) to provide lightning-fast fuzzy string matching and typo-tolerant auto-completion for frontend terminal components.

---

## 4. Soft-Delete & Archival Strategy
To prevent uncontrolled cascading deletions from irreversibly destroying decades of accumulated founder knowledge, all mutable core entities implement a standard soft-delete design:
- **`archived_at TIMESTAMPTZ DEFAULT NULL`**: When set, indicates record archival or logical deletion.
- **`is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED`**: Facilitates Boolean query filtering in UI components.
- **Search Exclusions**: All search SQL functions (`match_document_chunks`, `search_people_by_text`, etc.) enforce explicit filters excluding archived records (`WHERE archived_at IS NULL`) unless historical audit exploration is requested.
- **Approved Cascades (`ON DELETE CASCADE`)**: Restricted strictly to child entities that have zero standalone historical significance when their parent vanishes (e.g., junction rows, temporary sync tasks, task comments on permanently purged tasks, or document chunk embeddings when a file is physically wiped).

---

## 5. Security & Sensitive Vault Architecture
- **Integration Tokens**: Table `public.integration_tokens` has RLS enabled but deliberately exposes ZERO client user policies. This architectural blackout ensures no frontend JavaScript bundle or compromised browser session can query OAuth refresh tokens or API secrets.
- **Audit Logs**: Implemented as an append-only registry. RLS policies explicitly grant `SELECT` and `INSERT` to authenticated users for their own actions while denying all `UPDATE` and `DELETE` attempts, ensuring verifiable chronological audit trails.
