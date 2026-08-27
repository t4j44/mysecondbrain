-- ============================================================================
-- Migration: 0021_mcp_work_session_finalization.sql
-- Description: Make the MCP finalize_work_session workflow representable and
--              idempotent in the canonical schema.
--
--              1. `interaction_type` gains 'work_session'. The finalizer writes
--                 interactions of that type; without the enum value every real
--                 PostgreSQL finalize call would fail on insert.
--              2. `public.interactions` gains the `meta` JSONB and `deleted_at`
--                 columns the application model already maps and the finalizer
--                 already filters on (existing `metadata` values are backfilled).
--              3. A partial UNIQUE index makes idempotency a database guarantee,
--                 not just an application check: one live work session per
--                 (user, client_request_id).
--
-- Author: Agent — Senior MCP / Personal Work Intelligence Engineer (G5)
-- Notes: 'work_session' is compared as text throughout this file. A new enum
--        value cannot be referenced as a literal in the transaction that adds it.
-- ============================================================================

ALTER TYPE interaction_type ADD VALUE IF NOT EXISTS 'work_session';

ALTER TABLE public.interactions
    ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Preserve anything written through the original `metadata` column.
UPDATE public.interactions
   SET meta = COALESCE(metadata, '{}'::jsonb)
 WHERE (meta IS NULL OR meta = '{}'::jsonb)
   AND metadata IS NOT NULL
   AND metadata <> '{}'::jsonb;

-- Idempotency boundary: replaying a session_reference / client_request_id can never
-- produce a second WorkSession, and therefore never a second batch of the tasks,
-- decisions, memories and evidence that hang off it.
CREATE UNIQUE INDEX IF NOT EXISTS uq_interactions_work_session_client_request
    ON public.interactions (user_id, (meta ->> 'client_request_id'))
 WHERE interaction_type::text = 'work_session'
   AND deleted_at IS NULL
   AND meta ->> 'client_request_id' IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_interactions_work_sessions
    ON public.interactions (user_id, date DESC)
 WHERE interaction_type::text = 'work_session'
   AND deleted_at IS NULL;
