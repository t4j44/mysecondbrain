-- ============================================================================
-- Migration: 0015_enable_rls_and_policies.sql
-- Description: Enable Row Level Security and enforce strict auth.uid() isolation
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- Macro block to apply standard isolation policies across all user-owned domain tables
DO $$
DECLARE
    t TEXT;
    tables TEXT[] := ARRAY[
        'ventures', 'projects', 'project_members', 'tags', 'tasks', 'task_comments', 'task_tags',
        'organizations', 'people', 'relationships', 'interactions', 'interaction_participants', 'person_venture_links', 'person_project_links',
        'meetings', 'meeting_participants', 'memories', 'memory_people', 'memory_projects', 'memory_ventures', 'memory_tags',
        'ideas', 'idea_people', 'idea_projects', 'idea_memories', 'decisions', 'decision_people', 'decision_documents',
        'documents', 'document_links', 'document_chunks', 'embeddings', 'memory_embeddings', 'embedding_jobs',
        'kpis', 'kpi_definitions', 'kpi_entries', 'achievements', 'achievement_evidence', 'portfolio_case_studies', 'case_study_sources',
        'ai_conversations', 'ai_messages', 'ai_message_sources', 'content_items', 'content_versions', 'content_sources', 'weekly_reviews', 'weekly_review_sources',
        'integrations', 'sync_jobs', 'export_jobs', 'export_items'
    ];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
        EXECUTE format('DROP POLICY IF EXISTS "Policy_SELECT_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_SELECT_%I" ON public.%I FOR SELECT USING (user_id = auth.uid());', t, t);
        
        EXECUTE format('DROP POLICY IF EXISTS "Policy_INSERT_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_INSERT_%I" ON public.%I FOR INSERT WITH CHECK (user_id = auth.uid());', t, t);
        
        EXECUTE format('DROP POLICY IF EXISTS "Policy_UPDATE_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_UPDATE_%I" ON public.%I FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());', t, t);
        
        EXECUTE format('DROP POLICY IF EXISTS "Policy_DELETE_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_DELETE_%I" ON public.%I FOR DELETE USING (user_id = auth.uid());', t, t);
    END LOOP;
END $$;


-- Special Table 1: public.profiles (uses id = auth.uid())
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own profile" ON public.profiles;
CREATE POLICY "Users view own profile" ON public.profiles FOR SELECT USING (id = auth.uid());

DROP POLICY IF EXISTS "Users update own profile" ON public.profiles;
CREATE POLICY "Users update own profile" ON public.profiles FOR UPDATE USING (id = auth.uid()) WITH CHECK (id = auth.uid());


-- Special Table 2: public.integration_tokens (SENSITIVE VAULT)
-- Enforce RLS but intentionally define ZERO policies for regular users.
-- Browser clients attempting to query this table receive empty results / 403 under RLS.
-- Only server-side backend code using the Service Role key can bypass RLS to decrypt OAuth tokens.
ALTER TABLE public.integration_tokens ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Block all browser access to integration tokens" ON public.integration_tokens;


-- Special Table 3: public.audit_logs (IMMUTABLE APPEND-ONLY)
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own audit logs" ON public.audit_logs;
CREATE POLICY "Users view own audit logs" ON public.audit_logs FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users insert own audit logs" ON public.audit_logs;
CREATE POLICY "Users insert own audit logs" ON public.audit_logs FOR INSERT WITH CHECK (user_id = auth.uid());
-- Zero UPDATE or DELETE policies -> prevents modification or deletion of audit history.
