-- ============================================================================
-- Migration: 0017_create_evidence_and_portfolio_graph_tables.sql
-- Description: Create Work Sessions, Evidence Items, Portfolio Evidence, and Entity Graph Edges
-- Author: Senior Product Intelligence, Evidence and Career Portfolio Engineer
-- ============================================================================

-- 1. Work Sessions Table (Deep work logs, sprints, artifacts, and decisions)
CREATE TABLE IF NOT EXISTS public.work_sessions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    objective TEXT,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    duration_minutes INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    outcomes TEXT,
    artifacts_created JSONB NOT NULL DEFAULT '[]'::jsonb,
    decisions_made JSONB NOT NULL DEFAULT '[]'::jsonb,
    skills_exercised JSONB NOT NULL DEFAULT '[]'::jsonb,
    source TEXT NOT NULL DEFAULT 'manual_log', -- manual_log, ide_tracker, git_session, calendar_sync
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_work_sessions_updated_at ON public.work_sessions;
CREATE TRIGGER trg_work_sessions_updated_at
    BEFORE UPDATE ON public.work_sessions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. Evidence Items Table (Grounded, atomic facts extracted from work history)
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL, -- work_session, decision, document, interaction, kpi_entry, task, memory, achievement, commit
    source_id UUID NOT NULL,
    work_session_id UUID REFERENCES public.work_sessions(id) ON DELETE SET NULL,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    evidence_type TEXT NOT NULL, -- decision_record, code_deliverable, session_log, document_excerpt, kpi_metric, architectural_spec, user_research
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_reference TEXT, -- URL, file path, commit hash, or canonical markdown pointer
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence NUMERIC NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_evidence_items_updated_at ON public.evidence_items;
CREATE TRIGGER trg_evidence_items_updated_at
    BEFORE UPDATE ON public.evidence_items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 3. Portfolio Evidence Table (Skill claims grounded strictly in EvidenceItem IDs)
CREATE TABLE IF NOT EXISTS public.portfolio_evidence (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL, -- Product Management, AI Engineering, RAG Design, TAM/SAM/SOM, etc.
    project TEXT NOT NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    claim TEXT NOT NULL,
    supporting_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of UUID strings referencing evidence_items
    impact TEXT NOT NULL,
    metric TEXT, -- Verified metric IF verified, otherwise NULL (NEVER fabricated)
    metric_verified BOOLEAN NOT NULL DEFAULT false,
    confidence NUMERIC NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'in_review', 'approved', 'rejected')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_portfolio_evidence_updated_at ON public.portfolio_evidence;
CREATE TRIGGER trg_portfolio_evidence_updated_at
    BEFORE UPDATE ON public.portfolio_evidence
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 4. Entity Edges Table (Postgres-Native Generic Graph Model: Zero Neo4j overhead)
CREATE TABLE IF NOT EXISTS public.entity_edges (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_entity_type TEXT NOT NULL, -- skill, portfolio_evidence, evidence_item, work_session, project, venture, decision, task, document
    source_entity_id UUID NOT NULL,
    target_entity_type TEXT NOT NULL,
    target_entity_id UUID NOT NULL,
    relationship_type TEXT NOT NULL, -- evidenced_by, generated_during, demonstrates_skill, contributed_to, derived_from, validates
    weight NUMERIC NOT NULL DEFAULT 1.0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_entity_edge UNIQUE (user_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
);


-- 5. Indexes for fast graph traversal and lookups
CREATE INDEX IF NOT EXISTS idx_work_sessions_user_time ON public.work_sessions(user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_work_sessions_project ON public.work_sessions(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_work_sessions_venture ON public.work_sessions(venture_id) WHERE venture_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_evidence_items_user_source ON public.evidence_items(user_id, source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_work_session ON public.evidence_items(work_session_id) WHERE work_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_evidence_items_project ON public.evidence_items(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_evidence_items_venture ON public.evidence_items(venture_id) WHERE venture_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_evidence_items_type ON public.evidence_items(user_id, evidence_type);

CREATE INDEX IF NOT EXISTS idx_portfolio_evidence_user_skill ON public.portfolio_evidence(user_id, skill);
CREATE INDEX IF NOT EXISTS idx_portfolio_evidence_review_status ON public.portfolio_evidence(user_id, review_status);
CREATE INDEX IF NOT EXISTS idx_portfolio_evidence_project ON public.portfolio_evidence(project_id) WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_entity_edges_source ON public.entity_edges(user_id, source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_edges_target ON public.entity_edges(user_id, target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_edges_rel ON public.entity_edges(user_id, relationship_type);


-- 6. Row Level Security Policies
DO $$
DECLARE
    t TEXT;
    tables TEXT[] := ARRAY['work_sessions', 'evidence_items', 'portfolio_evidence', 'entity_edges'];
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
