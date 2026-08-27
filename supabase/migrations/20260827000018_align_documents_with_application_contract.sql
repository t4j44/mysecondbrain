-- ============================================================================
-- Migration: 0018_align_documents_with_application_contract.sql
-- Description: Additively align public.documents with the columns the application
--              layer requires (extension, extracted_text, chunking_state, error_state)
--              and give title a default so uploads never violate NOT NULL.
--              supabase/migrations remains the single canonical schema authority.
-- Author: Agent — Principal PostgreSQL / Data Architecture Engineer (G1 ONE SCHEMA)
-- ============================================================================

ALTER TABLE public.documents
    ADD COLUMN IF NOT EXISTS extension TEXT,
    ADD COLUMN IF NOT EXISTS extracted_text TEXT,
    ADD COLUMN IF NOT EXISTS chunking_state TEXT DEFAULT 'unprocessed',
    ADD COLUMN IF NOT EXISTS error_state TEXT,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- `title` stays NOT NULL; the default keeps application inserts valid when the
-- upload path only supplies filenames.
ALTER TABLE public.documents
    ALTER COLUMN title SET DEFAULT 'Untitled document';

CREATE INDEX IF NOT EXISTS idx_documents_checksum ON public.documents(user_id, checksum);
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON public.documents(deleted_at);
