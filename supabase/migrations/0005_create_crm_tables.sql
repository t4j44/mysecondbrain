-- ============================================================================
-- Migration: 0005_create_crm_tables.sql
-- Description: Create organizations, people CRM, relationships, interactions and links
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Organizations Table
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name extensions.citext NOT NULL,
    industry TEXT,
    website TEXT,
    location TEXT,
    description TEXT,
    notes TEXT,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_organizations_user_name UNIQUE(user_id, name)
);

DROP TRIGGER IF EXISTS trg_organizations_updated_at ON public.organizations;
CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. People CRM Table
CREATE TABLE IF NOT EXISTS public.people (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    role TEXT,
    company TEXT,
    industry TEXT,
    location TEXT,
    email extensions.citext,
    phone TEXT,
    profile_image TEXT,
    linkedin_url TEXT,
    social_links JSONB DEFAULT '{}'::jsonb,
    relationship_type relationship_type NOT NULL DEFAULT 'contact',
    relationship_strength INTEGER DEFAULT 5 CHECK (relationship_strength BETWEEN 1 AND 10),
    how_we_met TEXT,
    important_insights TEXT[] DEFAULT '{}',
    personal_context TEXT,
    last_interaction_at TIMESTAMPTZ,
    follow_up_date TIMESTAMPTZ,
    notes TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_people_updated_at ON public.people;
CREATE TRIGGER trg_people_updated_at
    BEFORE UPDATE ON public.people
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Add deferred foreign keys from execution migration now that people exists
ALTER TABLE public.project_members
    ADD CONSTRAINT fk_project_members_person FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;

ALTER TABLE public.tasks
    ADD CONSTRAINT fk_tasks_person FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE SET NULL;


-- 3. Relationships Table
CREATE TABLE IF NOT EXISTS public.relationships (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    target_person_id UUID REFERENCES public.people(id) ON DELETE CASCADE,
    relationship_label TEXT NOT NULL,
    strength INTEGER DEFAULT 5 CHECK (strength BETWEEN 1 AND 10),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_relationships_updated_at ON public.relationships;
CREATE TRIGGER trg_relationships_updated_at
    BEFORE UPDATE ON public.relationships
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 4. Interactions Table
CREATE TABLE IF NOT EXISTS public.interactions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    person_id UUID REFERENCES public.people(id) ON DELETE SET NULL,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    meeting_id UUID, -- FK to meetings added in 0006
    interaction_type interaction_type NOT NULL DEFAULT 'meeting',
    title TEXT NOT NULL,
    summary TEXT,
    detailed_notes TEXT,
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interaction_at TIMESTAMPTZ GENERATED ALWAYS AS (date) STORED,
    location TEXT,
    key_takeaways TEXT[] DEFAULT '{}',
    important_insights TEXT[] DEFAULT '{}',
    next_actions TEXT[] DEFAULT '{}',
    commitments TEXT[] DEFAULT '{}',
    follow_up_date TIMESTAMPTZ,
    markdown_path TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_interactions_updated_at ON public.interactions;
CREATE TRIGGER trg_interactions_updated_at
    BEFORE UPDATE ON public.interactions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 5. Interaction Participants Junction Table
CREATE TABLE IF NOT EXISTS public.interaction_participants (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    interaction_id UUID NOT NULL REFERENCES public.interactions(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_interaction_participants UNIQUE(interaction_id, person_id)
);


-- 6. Person Venture Links Junction Table
CREATE TABLE IF NOT EXISTS public.person_venture_links (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    venture_id UUID NOT NULL REFERENCES public.ventures(id) ON DELETE CASCADE,
    relationship_role TEXT NOT NULL DEFAULT 'advisor',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_person_venture_links UNIQUE(person_id, venture_id)
);


-- 7. Person Project Links Junction Table
CREATE TABLE IF NOT EXISTS public.person_project_links (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    relationship_role TEXT NOT NULL DEFAULT 'contributor',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_person_project_links UNIQUE(person_id, project_id)
);

-- Trigger to auto-update person last_interaction_at on interaction insertion
CREATE OR REPLACE FUNCTION public.update_person_last_interaction()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.person_id IS NOT NULL THEN
        UPDATE public.people
        SET last_interaction_at = GREATEST(COALESCE(last_interaction_at, NEW.date), NEW.date)
        WHERE id = NEW.person_id AND user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_update_person_last_interaction ON public.interactions;
CREATE TRIGGER trg_update_person_last_interaction
    AFTER INSERT OR UPDATE OF date, person_id ON public.interactions
    FOR EACH ROW EXECUTE FUNCTION public.update_person_last_interaction();
