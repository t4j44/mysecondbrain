-- ============================================================================
-- Migration: 0011_create_integrations_and_jobs_tables.sql
-- Description: Create integrations, protected token vaults, sync & export jobs
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Integrations Table
CREATE TABLE IF NOT EXISTS public.integrations (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider integration_provider NOT NULL,
    status integration_status NOT NULL DEFAULT 'connected',
    external_account_identifier TEXT,
    granted_scopes TEXT[] DEFAULT '{}',
    connected_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_successful_sync TIMESTAMPTZ,
    last_attempted_sync TIMESTAMPTZ,
    revoked_date TIMESTAMPTZ,
    provider_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_integrations_user_provider UNIQUE(user_id, provider)
);

DROP TRIGGER IF EXISTS trg_integrations_updated_at ON public.integrations;
CREATE TRIGGER trg_integrations_updated_at
    BEFORE UPDATE ON public.integrations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 2. Integration Tokens (SENSITIVE VAULT: server-only access via RLS)
CREATE TABLE IF NOT EXISTS public.integration_tokens (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES public.integrations(id) ON DELETE CASCADE,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    token_type TEXT NOT NULL DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_integration_tokens UNIQUE(integration_id)
);

DROP TRIGGER IF EXISTS trg_integration_tokens_updated_at ON public.integration_tokens;
CREATE TRIGGER trg_integration_tokens_updated_at
    BEFORE UPDATE ON public.integration_tokens
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 3. Sync Jobs Table
CREATE TABLE IF NOT EXISTS public.sync_jobs (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    integration_id UUID REFERENCES public.integrations(id) ON DELETE SET NULL,
    job_type sync_job_type NOT NULL,
    status sync_job_status NOT NULL DEFAULT 'pending',
    cursor TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    started_date TIMESTAMPTZ,
    completed_date TIMESTAMPTZ,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_sync_jobs_updated_at ON public.sync_jobs;
CREATE TRIGGER trg_sync_jobs_updated_at
    BEFORE UPDATE ON public.sync_jobs
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 4. Export Jobs Table
CREATE TABLE IF NOT EXISTS public.export_jobs (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    export_type export_job_type NOT NULL DEFAULT 'markdown',
    status export_job_status NOT NULL DEFAULT 'queued',
    requested_modules TEXT[] DEFAULT '{}',
    file_path TEXT,
    file_checksum TEXT,
    manifest JSONB DEFAULT '{}'::jsonb,
    retry_count INTEGER NOT NULL DEFAULT 0,
    expiration_date TIMESTAMPTZ NOT NULL DEFAULT (NOW() + interval '7 days'),
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_export_jobs_updated_at ON public.export_jobs;
CREATE TRIGGER trg_export_jobs_updated_at
    BEFORE UPDATE ON public.export_jobs
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 5. Export Items Table (Incremental export validation)
CREATE TABLE IF NOT EXISTS public.export_items (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    export_job_id UUID NOT NULL REFERENCES public.export_jobs(id) ON DELETE CASCADE,
    source_record_type TEXT NOT NULL,
    source_record_id UUID NOT NULL,
    item_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_export_items UNIQUE(export_job_id, source_record_type, source_record_id)
);
