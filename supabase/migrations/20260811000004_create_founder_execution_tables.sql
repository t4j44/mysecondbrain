-- ============================================================================
-- Migration: 0004_create_founder_execution_tables.sql
-- Description: Create ventures, projects, tasks, comments, tags and junctions
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Ventures Table
CREATE TABLE IF NOT EXISTS public.ventures (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug extensions.citext NOT NULL,
    vision TEXT,
    mission TEXT,
    description TEXT,
    status venture_status NOT NULL DEFAULT 'active',
    current_priority INTEGER DEFAULT 5 CHECK (current_priority BETWEEN 1 AND 10),
    start_date DATE DEFAULT CURRENT_DATE,
    target_date DATE,
    metadata JSONB DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ventures_user_slug UNIQUE(user_id, slug)
);

DROP TRIGGER IF EXISTS trg_ventures_updated_at ON public.ventures;
CREATE TRIGGER trg_ventures_updated_at
    BEFORE UPDATE ON public.ventures
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    status project_status NOT NULL DEFAULT 'active',
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    start_date DATE DEFAULT CURRENT_DATE,
    target_date DATE,
    completion_date DATE,
    metadata JSONB DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_projects_updated_at ON public.projects;
CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 3. Tags Table
CREATE TABLE IF NOT EXISTS public.tags (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name extensions.citext NOT NULL,
    color TEXT DEFAULT '#10b981',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tags_user_name UNIQUE (user_id, name)
);


-- 4. Project Members (Note: references people table which will be defined in CRM migration; FK created deferred or in CRM migration, but we create the basic table structure here)
CREATE TABLE IF NOT EXISTS public.project_members (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    person_id UUID NOT NULL, -- FK to public.people(id) added in 0005_create_crm_tables.sql
    role TEXT NOT NULL DEFAULT 'contributor',
    responsibility_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_project_members UNIQUE(project_id, person_id)
);


-- 5. Tasks Table
CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    person_id UUID, -- FK to public.people(id) added in 0005_create_crm_tables.sql
    title TEXT NOT NULL,
    description TEXT,
    status task_status NOT NULL DEFAULT 'todo',
    priority task_priority NOT NULL DEFAULT 'medium',
    due_date TIMESTAMPTZ,
    due_at TIMESTAMPTZ GENERATED ALWAYS AS (due_date) STORED,
    start_date TIMESTAMPTZ,
    completed_date TIMESTAMPTZ,
    estimated_effort INTEGER DEFAULT 60, -- minutes
    sort_order INTEGER DEFAULT 0,
    calendar_sync_status TEXT DEFAULT 'disabled',
    gcal_event_id TEXT,
    recurrence_metadata JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_tasks_updated_at ON public.tasks;
CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 6. Task Comments Table
CREATE TABLE IF NOT EXISTS public.task_comments (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
    comment_body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_task_comments_updated_at ON public.task_comments;
CREATE TRIGGER trg_task_comments_updated_at
    BEFORE UPDATE ON public.task_comments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 7. Task Tags Junction Table
CREATE TABLE IF NOT EXISTS public.task_tags (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES public.tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_task_tags UNIQUE (task_id, tag_id)
);

-- Auto-set completed_date when status changes to completed/done
CREATE OR REPLACE FUNCTION public.handle_task_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.status IN ('completed', 'done') AND OLD.status NOT IN ('completed', 'done')) THEN
        NEW.completed_date = NOW();
    ELSIF (NEW.status NOT IN ('completed', 'done')) THEN
        NEW.completed_date = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_handle_task_completion ON public.tasks;
CREATE TRIGGER trg_handle_task_completion
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.handle_task_completion();
