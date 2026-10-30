-- ============================================================================
-- Migration: 0019_create_jobs_and_exports_tables.sql
-- Description: Add the generic asynchronous job queue (public.jobs) and export
--              records (public.exports) that the application job runner, document
--              upload path, and export service already depend on. These were mapped
--              in the ORM but absent from the canonical schema.
-- Author: Agent — Principal PostgreSQL / Data Architecture Engineer (G1 ONE SCHEMA)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL, -- sync_google_drive, export_markdown, document_processing
    status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    result_payload JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON public.jobs;
CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON public.jobs
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON public.jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_pending ON public.jobs(status, created_at);


CREATE TABLE IF NOT EXISTS public.exports (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    export_type TEXT NOT NULL DEFAULT 'full', -- record, module, full
    status TEXT NOT NULL DEFAULT 'pending',
    file_path TEXT,
    signed_url TEXT,
    expires_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_exports_updated_at ON public.exports;
CREATE TRIGGER trg_exports_updated_at
    BEFORE UPDATE ON public.exports
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_exports_user_status ON public.exports(user_id, status);


-- Row Level Security consistent with migration 0015 (owner-only isolation).
DO $$
DECLARE
    t TEXT;
    tables TEXT[] := ARRAY['jobs', 'exports'];
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
