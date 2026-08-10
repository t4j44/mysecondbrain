-- ============================================================================
-- Migration: 0009_create_kpis_and_portfolio_tables.sql
-- Description: Create KPI definitions/entries and achievement portfolio tables
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. KPIs table (Strict adherence to database_schema.md v1.0 contract)
CREATE TABLE IF NOT EXISTS public.kpis (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- founder, network, learning
    metric_name TEXT NOT NULL,
    target_value NUMERIC NOT NULL,
    current_value NUMERIC NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'count',
    period TEXT NOT NULL DEFAULT 'weekly',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_kpis_updated_at ON public.kpis;
CREATE TRIGGER trg_kpis_updated_at
    BEFORE UPDATE ON public.kpis
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. KPI Definitions Table (Expanded historical KPI architecture)
CREATE TABLE IF NOT EXISTS public.kpi_definitions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    category kpi_category NOT NULL DEFAULT 'founder',
    unit TEXT NOT NULL DEFAULT 'count',
    target_value NUMERIC NOT NULL,
    target_period kpi_period NOT NULL DEFAULT 'weekly',
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_kpi_definitions_updated_at ON public.kpi_definitions;
CREATE TRIGGER trg_kpi_definitions_updated_at
    BEFORE UPDATE ON public.kpi_definitions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 3. KPI Entries Table (Immutable historical tracking)
CREATE TABLE IF NOT EXISTS public.kpi_entries (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    definition_id UUID NOT NULL REFERENCES public.kpi_definitions(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    numeric_value NUMERIC NOT NULL,
    text_value TEXT,
    notes TEXT,
    evidence_document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 4. Achievements Table
CREATE TABLE IF NOT EXISTS public.achievements (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    role TEXT NOT NULL,
    problem TEXT,
    responsibilities TEXT[] DEFAULT '{}',
    actions TEXT[] DEFAULT '{}',
    impact TEXT,
    skills TEXT[] DEFAULT '{}',
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    achievement_date DATE GENERATED ALWAYS AS (date) STORED,
    visibility visibility_status NOT NULL DEFAULT 'private',
    verification_status TEXT NOT NULL DEFAULT 'unverified', -- unverified, documented, verified
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_achievements_updated_at ON public.achievements;
CREATE TRIGGER trg_achievements_updated_at
    BEFORE UPDATE ON public.achievements
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 5. Achievement Evidence Junction Table
CREATE TABLE IF NOT EXISTS public.achievement_evidence (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES public.achievements(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_achievement_evidence UNIQUE(achievement_id, document_id)
);


-- 6. Portfolio Case Studies Table
CREATE TABLE IF NOT EXISTS public.portfolio_case_studies (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    target_role TEXT NOT NULL DEFAULT 'AI Product Manager / Founder',
    problem TEXT,
    context TEXT,
    responsibilities TEXT[] DEFAULT '{}',
    actions TEXT[] DEFAULT '{}',
    impact TEXT,
    skills TEXT[] DEFAULT '{}',
    draft_status TEXT NOT NULL DEFAULT 'draft', -- draft, ready, archived
    published BOOLEAN NOT NULL DEFAULT false,
    source_references JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_portfolio_case_studies_updated_at ON public.portfolio_case_studies;
CREATE TRIGGER trg_portfolio_case_studies_updated_at
    BEFORE UPDATE ON public.portfolio_case_studies
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 7. Case Study Sources Junction Table
CREATE TABLE IF NOT EXISTS public.case_study_sources (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    case_study_id UUID NOT NULL REFERENCES public.portfolio_case_studies(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL, -- achievement, project, venture, document
    source_record_id UUID NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_case_study_sources UNIQUE(case_study_id, source_record_type, source_record_id)
);
