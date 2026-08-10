-- ============================================================================
-- Migration: 0006_create_memory_tables.sql
-- Description: Create meetings, memories, and junction tables for memory links
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Meetings Table
CREATE TABLE IF NOT EXISTS public.meetings (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ NOT NULL DEFAULT (NOW() + interval '30 minutes'),
    location TEXT,
    meeting_type TEXT DEFAULT 'in_person',
    status meeting_status NOT NULL DEFAULT 'scheduled',
    source TEXT DEFAULT 'manual',
    external_calendar_event_id TEXT,
    summary TEXT,
    decisions TEXT[] DEFAULT '{}',
    action_items TEXT[] DEFAULT '{}',
    raw_notes TEXT,
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_meetings_updated_at ON public.meetings;
CREATE TRIGGER trg_meetings_updated_at
    BEFORE UPDATE ON public.meetings
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Attach deferred meeting FK on interactions
ALTER TABLE public.interactions
    ADD CONSTRAINT fk_interactions_meeting FOREIGN KEY (meeting_id) REFERENCES public.meetings(id) ON DELETE SET NULL;


-- 2. Meeting Participants Junction Table
CREATE TABLE IF NOT EXISTS public.meeting_participants (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'attendee',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_meeting_participants UNIQUE(meeting_id, person_id)
);


-- 3. Memories Table
CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    memory_type TEXT NOT NULL DEFAULT 'general', -- general, insight, lesson, conversation, reflection
    body TEXT NOT NULL,
    content TEXT GENERATED ALWAYS AS (body) STORED,
    summary TEXT,
    source TEXT DEFAULT 'user',
    memory_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    importance INTEGER DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    sentiment TEXT DEFAULT 'neutral',
    visibility visibility_status NOT NULL DEFAULT 'private',
    embedding_status TEXT NOT NULL DEFAULT 'pending', -- pending, indexed, error
    archived_at TIMESTAMPTZ DEFAULT NULL,
    is_archived BOOLEAN GENERATED ALWAYS AS (archived_at IS NOT NULL) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_memories_updated_at ON public.memories;
CREATE TRIGGER trg_memories_updated_at
    BEFORE UPDATE ON public.memories
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 4. Memory People Junction Table
CREATE TABLE IF NOT EXISTS public.memory_people (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES public.memories(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_memory_people UNIQUE(memory_id, person_id)
);


-- 5. Memory Projects Junction Table
CREATE TABLE IF NOT EXISTS public.memory_projects (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES public.memories(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_memory_projects UNIQUE(memory_id, project_id)
);


-- 6. Memory Ventures Junction Table
CREATE TABLE IF NOT EXISTS public.memory_ventures (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES public.memories(id) ON DELETE CASCADE,
    venture_id UUID NOT NULL REFERENCES public.ventures(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_memory_ventures UNIQUE(memory_id, venture_id)
);


-- 7. Memory Tags Junction Table
CREATE TABLE IF NOT EXISTS public.memory_tags (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES public.memories(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES public.tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_memory_tags UNIQUE(memory_id, tag_id)
);
