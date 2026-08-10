# Row Level Security (RLS) Policy Reference — Taj's Second Brain

This reference documents the security architecture and Row Level Security (RLS) policies implemented across all 26 core database tables in **Taj's Second Brain**.

---

## 1. Core Security Principle & User Isolation
The absolute security invariant across the entire system is:
> **One authenticated user can NEVER access, connect to, modify, search, or export another user's records.**

By default, every single public table has RLS enabled (`ALTER TABLE public.<table> ENABLE ROW LEVEL SECURITY;`).
Standard user-owned entities enforce direct isolation matching the JWT sub claim:
- **SELECT**: `USING (user_id = auth.uid())`
- **INSERT**: `WITH CHECK (user_id = auth.uid())`
- **UPDATE**: `USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())`
- **DELETE**: `USING (user_id = auth.uid())`

---

## 2. Comprehensive Policy Table Matrix

| Table Name | Ownership Field | SELECT Policy | INSERT Policy | UPDATE Policy | DELETE Policy | Special Restrictions & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `profiles` | `id` | `id = auth.uid()` | Auth trigger only | `id = auth.uid()` | Cascade from auth.users | Linked directly to Supabase auth.users ID |
| `ventures` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Soft-deletable via `archived_at` |
| `projects` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Validates venture belongs to same user |
| `project_members` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Validates person belongs to same user |
| `tags` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Unique tag names scoped per user |
| `tasks` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Cross-user trigger validation for project/venture/person |
| `task_comments` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Cascade delete with task |
| `task_tags` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Junction linking tasks and tags |
| `organizations` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | CRM organizational entities |
| `people` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | No global shared contacts; every contact owned by 1 user |
| `relationships` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Tracks network influence connections |
| `interactions` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Automatically updates person last_interaction_at |
| `interaction_participants`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Validates participant belongs to user |
| `person_venture_links`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Links CRM contacts to ventures |
| `person_project_links`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Links CRM contacts to projects |
| `meetings` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Calendar & manual transcript records |
| `meeting_participants`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Meeting attendees |
| `memories` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Core foundational RAG memory storage |
| `memory_people` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Memory junction to CRM people |
| `memory_projects` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Memory junction to projects |
| `memory_ventures` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Memory junction to ventures |
| `memory_tags` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Memory junction to tags |
| `ideas` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Idea Vault items |
| `idea_people` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Junction table |
| `idea_projects` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Junction table |
| `idea_memories` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Junction table |
| `decisions` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Strategic decision log |
| `decision_people` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Stakeholders |
| `decision_documents`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Supporting documents |
| `documents` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | File system metadata & buckets |
| `document_links` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Polymorphic links |
| `document_chunks` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Chunked parsing for RAG |
| `embeddings` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | 768-dim vectors; user filtered |
| `memory_embeddings` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | v1.0 contract table |
| `embedding_jobs` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Async worker queue |
| `kpis` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | v1.0 compatibility table |
| `kpi_definitions` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Metric configuration |
| `kpi_entries` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Historical numeric logs |
| `achievements` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Verified milestone history |
| `achievement_evidence`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Supporting proof documents |
| `portfolio_case_studies`|`user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Career case studies |
| `case_study_sources`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Traceability junction |
| `ai_conversations`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| AI chat container |
| `ai_messages` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Chat transcript history |
| `ai_message_sources`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| RAG citation links |
| `content_items` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | AI Content Engine posts |
| `content_versions`| `user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Historical revision log |
| `content_sources` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Source attribution |
| `weekly_reviews` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Weekly intelligence synthesis |
| `weekly_review_sources`|`user_id`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| `user_id = auth.uid()`| Source attribution |
| `integrations` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Google Drive & GCal metadata |
| **`integration_tokens`** | `user_id` | **NO POLICY (BLOCKED)** | **NO POLICY (BLOCKED)** | **NO POLICY (BLOCKED)** | **NO POLICY (BLOCKED)** | **SENSITIVE VAULT**: Complete browser read/write block; server-only via Service Role |
| `sync_jobs` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Background worker job queue |
| `export_jobs` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Markdown export tracking |
| `export_items` | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | `user_id = auth.uid()` | Incremental export items |
| **`audit_logs`** | `user_id` | `user_id = auth.uid()` | `user_id = auth.uid()` | **FORBIDDEN (NO POLICY)**| **FORBIDDEN (NO POLICY)**| **IMMUTABLE APPEND-ONLY**: Users cannot alter or erase historical event records |

---

## 3. Service Role Considerations & Server Best Practices
1. **Service Role Key Bypasses RLS**: The Supabase service-role secret key operates as database superuser with respect to RLS policies.
2. **Server-Only Use**: The service role key MUST never be exposed in client bundles, Next.js browser configurations, or Git repositories.
3. **Minimization of Use**: Backend APIs (FastAPI) should normally instantiate user scopes using the incoming JWT Bearer token to benefit from automatic PostgreSQL database RLS filtering. Service role should ONLY be used when processing background worker jobs (such as automated nightly drive backup or AI embedding workers) where a live interactive user JWT is absent, and the backend service MUST manually append `user_id == target_user` filters in Python SQL builders.
