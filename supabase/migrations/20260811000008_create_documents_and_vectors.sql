-- ============================================================================
-- Migration: 0008_create_documents_and_vectors.sql
-- Description: Create documents, chunks, decision_documents, and pgvector tables
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Documents Table
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    original_filename TEXT,
    sanitized_filename TEXT,
    mime_type TEXT DEFAULT 'text/plain',
    file_size BIGINT DEFAULT 0,
    storage_bucket TEXT NOT NULL DEFAULT 'user_documents',
    storage_path TEXT NOT NULL,
    checksum TEXT,
    processing_status document_processing_status NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    extracted_text_status TEXT DEFAULT 'pending',
    embedding_status TEXT DEFAULT 'pending',
    source TEXT DEFAULT 'upload',
    uploaded_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_documents_user_path UNIQUE(user_id, storage_bucket, storage_path)
);

DROP TRIGGER IF EXISTS trg_documents_updated_at ON public.documents;
CREATE TRIGGER trg_documents_updated_at
    BEFORE UPDATE ON public.documents
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Attach deferred decision_documents table from migration 0007
CREATE TABLE IF NOT EXISTS public.decision_documents (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    decision_id UUID NOT NULL REFERENCES public.decisions(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_decision_documents UNIQUE(decision_id, document_id)
);


-- 2. Document Links Table (Polymorphic references to entities)
CREATE TABLE IF NOT EXISTS public.document_links (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL, -- person, venture, project, meeting, memory, idea, decision, achievement
    target_id UUID NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_links UNIQUE(document_id, target_type, target_id)
);


-- 3. Document Chunks Table
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    chunk_text TEXT NOT NULL,
    token_count INTEGER,
    character_count INTEGER,
    page_number INTEGER,
    section_title TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    checksum TEXT,
    embedding_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_chunks UNIQUE(document_id, chunk_index)
);


-- 4. Embeddings Table (768 dimensions for Gemini text-embedding-004)
CREATE TABLE IF NOT EXISTS public.embeddings (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL, -- memory, interaction, document_chunk, idea, person
    source_record_id UUID NOT NULL,
    document_chunk_id UUID REFERENCES public.document_chunks(id) ON DELETE CASCADE,
    embedding extensions.vector(768) NOT NULL,
    provider TEXT NOT NULL DEFAULT 'gemini',
    model TEXT NOT NULL DEFAULT 'text-embedding-004',
    dimensions INTEGER NOT NULL DEFAULT 768,
    content_checksum TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_embeddings_updated_at ON public.embeddings;
CREATE TRIGGER trg_embeddings_updated_at
    BEFORE UPDATE ON public.embeddings
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 5. Memory Embeddings Table (Strict adherence to database_schema.md v1.0 contract)
CREATE TABLE IF NOT EXISTS public.memory_embeddings (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL, -- person, interaction, project, idea, achievement, note
    entity_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding extensions.vector(768),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 6. Embedding Jobs Table (Asynchronous indexing queue)
CREATE TABLE IF NOT EXISTS public.embedding_jobs (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL,
    source_record_id UUID NOT NULL,
    document_chunk_id UUID REFERENCES public.document_chunks(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_embedding_jobs_updated_at ON public.embedding_jobs;
CREATE TRIGGER trg_embedding_jobs_updated_at
    BEFORE UPDATE ON public.embedding_jobs
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
