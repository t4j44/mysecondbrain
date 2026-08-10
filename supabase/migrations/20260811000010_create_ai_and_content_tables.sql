-- ============================================================================
-- Migration: 0010_create_ai_and_content_tables.sql
-- Description: Create AI conversation history, content items, versions and weekly reviews
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. AI Conversations Table
CREATE TABLE IF NOT EXISTS public.ai_conversations (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    mode TEXT NOT NULL DEFAULT 'advisor', -- advisor, coach, analyzer, drafter
    provider TEXT NOT NULL DEFAULT 'gemini',
    model TEXT NOT NULL DEFAULT 'gemini-3.1-pro',
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_ai_conversations_updated_at ON public.ai_conversations;
CREATE TRIGGER trg_ai_conversations_updated_at
    BEFORE UPDATE ON public.ai_conversations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. AI Messages Table
CREATE TABLE IF NOT EXISTS public.ai_messages (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES public.ai_conversations(id) ON DELETE CASCADE,
    role ai_message_role NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    status ai_message_status NOT NULL DEFAULT 'completed',
    provider TEXT,
    model TEXT,
    usage_metadata JSONB DEFAULT '{}'::jsonb,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 3. AI Message Sources Table (RAG citation traceability)
CREATE TABLE IF NOT EXISTS public.ai_message_sources (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES public.ai_messages(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL, -- memory, interaction, document_chunk, person, project
    source_record_id UUID NOT NULL,
    citation_label TEXT,
    relevance_score FLOAT,
    excerpt TEXT,
    position INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 4. Content Items Table (AI Content Engine)
CREATE TABLE IF NOT EXISTS public.content_items (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL DEFAULT 'linkedin_post', -- linkedin_post, founder_story, case_study, article, update
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    status content_status NOT NULL DEFAULT 'draft',
    audience TEXT,
    objective TEXT,
    provider TEXT DEFAULT 'gemini',
    model TEXT DEFAULT 'gemini-3.1-pro',
    published_date TIMESTAMPTZ,
    external_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_content_items_updated_at ON public.content_items;
CREATE TRIGGER trg_content_items_updated_at
    BEFORE UPDATE ON public.content_items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 5. Content Versions Table (Preserving historical generation edits)
CREATE TABLE IF NOT EXISTS public.content_versions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_item_id UUID NOT NULL REFERENCES public.content_items(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    change_summary TEXT DEFAULT 'Automated version save',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_content_versions UNIQUE(content_item_id, version_number)
);


-- 6. Content Sources Junction Table
CREATE TABLE IF NOT EXISTS public.content_sources (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_item_id UUID NOT NULL REFERENCES public.content_items(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL,
    source_record_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_content_sources UNIQUE(content_item_id, source_record_type, source_record_id)
);


-- 7. Weekly Reviews Table
CREATE TABLE IF NOT EXISTS public.weekly_reviews (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    review_start_date DATE NOT NULL,
    review_end_date DATE NOT NULL,
    generated_content TEXT,
    user_edited_content TEXT,
    status content_status NOT NULL DEFAULT 'draft',
    provider TEXT DEFAULT 'gemini',
    model TEXT DEFAULT 'gemini-3.1-pro',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_weekly_reviews_dates UNIQUE(user_id, review_start_date, review_end_date)
);

DROP TRIGGER IF EXISTS trg_weekly_reviews_updated_at ON public.weekly_reviews;
CREATE TRIGGER trg_weekly_reviews_updated_at
    BEFORE UPDATE ON public.weekly_reviews
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 8. Weekly Review Sources Junction Table
CREATE TABLE IF NOT EXISTS public.weekly_review_sources (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    review_id UUID NOT NULL REFERENCES public.weekly_reviews(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL,
    source_record_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_weekly_review_sources UNIQUE(review_id, source_record_type, source_record_id)
);
