-- ============================================================================
-- Migration: 0007_create_idea_and_decision_tables.sql
-- Description: Create Idea Vault and Decision tracking tables with junctions
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Ideas Table
CREATE TABLE IF NOT EXISTS public.ideas (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    problem TEXT,
    solution TEXT,
    target_users TEXT,
    market TEXT,
    potential_score INTEGER DEFAULT 5 CHECK (potential_score BETWEEN 1 AND 10),
    status idea_status NOT NULL DEFAULT 'draft',
    assumptions TEXT[] DEFAULT '{}',
    risks TEXT[] DEFAULT '{}',
    required_resources TEXT[] DEFAULT '{}',
    validation_evidence TEXT[] DEFAULT '{}',
    next_steps TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_ideas_updated_at ON public.ideas;
CREATE TRIGGER trg_ideas_updated_at
    BEFORE UPDATE ON public.ideas
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. Idea People Junction Table
CREATE TABLE IF NOT EXISTS public.idea_people (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    idea_id UUID NOT NULL REFERENCES public.ideas(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_idea_people UNIQUE(idea_id, person_id)
);


-- 3. Idea Projects Junction Table
CREATE TABLE IF NOT EXISTS public.idea_projects (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    idea_id UUID NOT NULL REFERENCES public.ideas(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_idea_projects UNIQUE(idea_id, project_id)
);


-- 4. Idea Memories Junction Table
CREATE TABLE IF NOT EXISTS public.idea_memories (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    idea_id UUID NOT NULL REFERENCES public.ideas(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES public.memories(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_idea_memories UNIQUE(idea_id, memory_id)
);


-- 5. Decisions Table
CREATE TABLE IF NOT EXISTS public.decisions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    context TEXT,
    decision TEXT NOT NULL,
    rationale TEXT,
    alternatives_considered TEXT[] DEFAULT '{}',
    expected_impact TEXT,
    status TEXT NOT NULL DEFAULT 'active', -- active, reviewed, superseded, reversed
    decision_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    review_date TIMESTAMPTZ,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_decisions_updated_at ON public.decisions;
CREATE TRIGGER trg_decisions_updated_at
    BEFORE UPDATE ON public.decisions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 6. Decision People Junction Table
CREATE TABLE IF NOT EXISTS public.decision_people (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    decision_id UUID NOT NULL REFERENCES public.decisions(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'stakeholder', -- decider, consulted, informed, stakeholder
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_decision_people UNIQUE(decision_id, person_id)
);

-- Note: decision_documents junction table will be created in 0008 after documents table is created.
