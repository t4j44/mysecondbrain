-- ============================================================================
-- Migration: 0014_create_indexes.sql
-- Description: Create B-Tree, GIN, Trigram, and pgvector HNSW/IVFFlat indexes
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Founder Execution Composite Indexes
CREATE INDEX IF NOT EXISTS idx_ventures_user_status ON public.ventures(user_id, status) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_projects_user_venture_status ON public.projects(user_id, venture_id, status) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON public.tasks(user_id, status) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON public.tasks(user_id, due_date) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON public.tasks(user_id, due_at) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_user_project_status ON public.tasks(user_id, project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_user_venture_status ON public.tasks(user_id, venture_id, status);

-- 2. CRM & Network Intelligence Indexes
CREATE INDEX IF NOT EXISTS idx_people_user_name ON public.people(user_id, name) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_people_tags ON public.people USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_people_last_interaction ON public.people(user_id, last_interaction_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_user_date ON public.interactions(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_user_at ON public.interactions(user_id, interaction_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_person ON public.interactions(user_id, person_id);

-- 3. Meetings, Memories & Ideas Indexes
CREATE INDEX IF NOT EXISTS idx_meetings_user_start ON public.meetings(user_id, start_time DESC) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_user_date ON public.memories(user_id, memory_date DESC) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_user_created ON public.memories(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_user_status ON public.ideas(user_id, status) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_user_date ON public.decisions(user_id, decision_date DESC);

-- 4. Documents & Vector Search Indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_created ON public.documents(user_id, created_at DESC) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON public.document_chunks(document_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_embeddings_source_record ON public.embeddings(user_id, source_record_type, source_record_id);

-- HNSW vector index on embeddings table for fast incremental cosine similarity retrieval
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine ON public.embeddings USING hnsw (embedding extensions.vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- IVFFlat vector index on memory_embeddings (Strict alignment with database_schema.md v1.0)
CREATE INDEX IF NOT EXISTS idx_memory_vector ON public.memory_embeddings USING ivfflat (embedding extensions.vector_cosine_ops) WITH (lists = 100);

-- 5. AI Intelligence & Content Engine Indexes
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_updated ON public.ai_conversations(user_id, updated_at DESC) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation ON public.ai_messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_content_items_user_created ON public.content_items(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_weekly_reviews_user_dates ON public.weekly_reviews(user_id, review_start_date, review_end_date);
CREATE INDEX IF NOT EXISTS idx_kpi_entries_definition_date ON public.kpi_entries(definition_id, entry_date DESC);

-- 6. Integrations, Jobs, & Audit Logs Indexes
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON public.sync_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON public.export_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON public.audit_logs(user_id, created_at DESC);

-- 7. Trigram (pg_trgm) Keyword & Fuzzy Search GIN Indexes
CREATE INDEX IF NOT EXISTS idx_trgm_people_name ON public.people USING GIN (name extensions.gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_trgm_tasks_title ON public.tasks USING GIN (title extensions.gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_trgm_memories_title ON public.memories USING GIN (title extensions.gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_trgm_interactions_title ON public.interactions USING GIN (title extensions.gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_trgm_documents_title ON public.documents USING GIN (title extensions.gin_trgm_ops);
