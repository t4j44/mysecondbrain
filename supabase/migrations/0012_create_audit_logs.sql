-- ============================================================================
-- Migration: 0012_create_audit_logs.sql
-- Description: Create immutable append-only audit logs table
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    actor_type TEXT NOT NULL DEFAULT 'user', -- user, service, system, ai
    actor_identifier TEXT, -- user email, agent id, or tool name
    event_type TEXT NOT NULL, -- e.g. login, export_markdown, mcp_invoke, delete_venture
    resource_type TEXT NOT NULL, -- table or domain entity name
    resource_id UUID,
    request_id TEXT,
    result_status TEXT NOT NULL DEFAULT 'success', -- success, forbidden, error
    ip_metadata JSONB DEFAULT '{}'::jsonb,
    user_agent_metadata JSONB DEFAULT '{}'::jsonb,
    safe_event_metadata JSONB DEFAULT '{}'::jsonb, -- Strict rule: NO tokens, NO prompts, NO raw contents
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Note: Audit logs are intentionally append-only.
-- No updated_at trigger is applied, and RLS policies forbid normal UPDATE or DELETE by users.
