-- ============================================================================
-- Migration: 0023_align_canonical_columns_with_application_contract.sql
-- Description: Add the columns the application genuinely requires but the canonical
--              schema never declared. Every column here was reached by classifying
--              all 114 ORM/database mismatches (see
--              docs/production-recovery/G1_REOPENED_ORM_DRIFT_MATRIX.md); only the
--              DATABASE_COLUMN_REQUIRED class appears below.
--
--              Mismatches that were a *naming* difference were fixed in the ORM by
--              mapping to the existing canonical column, not by adding a column here.
--              Mismatches that were relational were left to the canonical link tables.
--
--              Two deletion concepts coexist deliberately:
--                archived_at  — user-visible archival (already canonical, with the
--                               generated is_archived companion on most tables)
--                deleted_at   — soft delete enforced by BaseRepository, which excludes
--                               deleted rows from every get/list and never issues a
--                               hard DELETE. Already canonical on interactions,
--                               commitments, person_organization_roles and documents;
--                               this migration completes the pattern for the remaining
--                               mapped tables.
--
-- Author: Agent — Principal PostgreSQL + SQLAlchemy Schema Reconciliation Engineer (G1 reopened)
-- Notes: Additive and idempotent. No column is dropped, no data is destroyed, no
--        existing migration is rewritten. Safe to replay.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Soft-delete completion (BaseRepository.delete / get_by_id / list)
-- ---------------------------------------------------------------------------
ALTER TABLE public.achievements           ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.content_items          ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.decisions              ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.evidence_items         ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.ideas                  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.kpi_definitions        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.meetings               ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.memories               ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.organizations          ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.people                 ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.portfolio_case_studies ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.portfolio_evidence     ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.projects               ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.tasks                  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.ventures               ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.weekly_reviews         ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE public.work_sessions          ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- ---------------------------------------------------------------------------
-- 1b. Application relationship payloads that are intentionally denormalized.
--     The normalized junction tables remain authoritative for new graph work;
--     these columns preserve the existing API/read model and imported payloads.
-- ---------------------------------------------------------------------------
ALTER TABLE public.content_items
    ADD COLUMN IF NOT EXISTS source_records JSONB DEFAULT '[]'::jsonb;

ALTER TABLE public.decisions
    ADD COLUMN IF NOT EXISTS supporting_people JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS supporting_documents JSONB DEFAULT '[]'::jsonb;

ALTER TABLE public.memories
    ADD COLUMN IF NOT EXISTS related_people UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS related_projects UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS related_ventures UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS linked_venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS linked_person_id UUID REFERENCES public.people(id) ON DELETE SET NULL;

ALTER TABLE public.portfolio_case_studies
    ADD COLUMN IF NOT EXISTS achievement_id UUID REFERENCES public.achievements(id) ON DELETE SET NULL;

ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS member_links JSONB DEFAULT '[]'::jsonb;

ALTER TABLE public.tasks
    ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- ---------------------------------------------------------------------------
-- 2. Archival completion for tables the application archives but the schema missed
-- ---------------------------------------------------------------------------
ALTER TABLE public.content_items          ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE public.interactions           ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE public.kpi_definitions        ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE public.portfolio_case_studies ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE public.weekly_reviews         ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- ---------------------------------------------------------------------------
-- 3. Content pipeline (services/content, schemas/knowledge ContentItem contract)
-- ---------------------------------------------------------------------------
ALTER TABLE public.content_items
    ADD COLUMN IF NOT EXISTS provider_metadata JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS publication_metadata JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS current_version_number INTEGER NOT NULL DEFAULT 1;

-- ---------------------------------------------------------------------------
-- 4. Idea -> project conversion pointer (services/knowledge.py convert_idea_to_project).
--    This is a single 1:1 conversion marker, not the idea_projects many-to-many.
-- ---------------------------------------------------------------------------
ALTER TABLE public.ideas
    ADD COLUMN IF NOT EXISTS converted_project_id UUID
        REFERENCES public.projects(id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- 5. KPI definitions: the application tracks a denormalized latest value and the
--    documents that evidence the target.
-- ---------------------------------------------------------------------------
ALTER TABLE public.kpi_definitions
    ADD COLUMN IF NOT EXISTS current_value DOUBLE PRECISION NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS evidence_docs JSONB DEFAULT '[]'::jsonb;

-- ---------------------------------------------------------------------------
-- 6. Meetings: venture scope, recording link and free-form metadata.
--    `meeting_participants.attendance_status` is distinct from the existing `role`
--    column: role is what the person is to the meeting, attendance is whether they came.
-- ---------------------------------------------------------------------------
ALTER TABLE public.meetings
    ADD COLUMN IF NOT EXISTS venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS recording_url TEXT,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

ALTER TABLE public.meeting_participants
    ADD COLUMN IF NOT EXISTS attendance_status TEXT NOT NULL DEFAULT 'attended';

-- ---------------------------------------------------------------------------
-- 7. Memories: AI-summary provenance and free-form metadata.
-- ---------------------------------------------------------------------------
ALTER TABLE public.memories
    ADD COLUMN IF NOT EXISTS is_ai_summary BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- ---------------------------------------------------------------------------
-- 8. Organizations: enrichment fields exposed by the CRM API.
--    `website` already exists and is what the ORM now maps; `domain` is the bare
--    apex domain used for contact matching and is not derivable from it.
-- ---------------------------------------------------------------------------
ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS domain TEXT,
    ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- ---------------------------------------------------------------------------
-- 9. Portfolio case studies: the project a case study is about, and AI provenance.
-- ---------------------------------------------------------------------------
ALTER TABLE public.portfolio_case_studies
    ADD COLUMN IF NOT EXISTS project_name TEXT,
    ADD COLUMN IF NOT EXISTS is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE;

-- ---------------------------------------------------------------------------
-- 10. Tasks: calendar synchronization payload. Distinct from the existing
--     `calendar_sync_status` (a state string) and `recurrence_metadata` (RRULE data).
-- ---------------------------------------------------------------------------
ALTER TABLE public.tasks
    ADD COLUMN IF NOT EXISTS calendar_sync_metadata JSONB DEFAULT '{}'::jsonb;

-- ---------------------------------------------------------------------------
-- 11. Weekly reviews: human title, the review's own date, and AI provenance.
--     Backfilled from the existing review window so the NOT NULL is safe on
--     databases that already hold rows.
-- ---------------------------------------------------------------------------
ALTER TABLE public.weekly_reviews
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS review_date TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE public.weekly_reviews
   SET title = COALESCE(
           title,
           'Weekly review ' || COALESCE(review_start_date::date::text, created_at::date::text)
       ),
       review_date = COALESCE(review_date, review_start_date, created_at)
 WHERE title IS NULL OR review_date IS NULL;

ALTER TABLE public.weekly_reviews
    ALTER COLUMN title SET NOT NULL,
    ALTER COLUMN review_date SET NOT NULL;

-- ---------------------------------------------------------------------------
-- 12. Indexes supporting the soft-delete predicate on the hot daily-driver paths.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_tasks_live            ON public.tasks (user_id, due_date)        WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_projects_live         ON public.projects (user_id, status)       WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_ventures_live         ON public.ventures (user_id, status)       WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_people_live           ON public.people (user_id, name)           WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_live         ON public.memories (user_id, memory_date)  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_meetings_live         ON public.meetings (user_id, start_time)   WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_work_sessions_live    ON public.work_sessions (user_id, start_time) WHERE deleted_at IS NULL;
