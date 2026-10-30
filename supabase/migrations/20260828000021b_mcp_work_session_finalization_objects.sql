-- 0021b: columns, backfill and idempotency indexes. Runs after 0021a committed,
-- so 'work_session' can be compared as the enum itself. Enum equality is
-- IMMUTABLE; the previous `interaction_type::text = 'work_session'` was not,
-- and PostgreSQL rejects it in an index predicate.
ALTER TABLE public.interactions
    ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

UPDATE public.interactions
   SET meta = COALESCE(metadata, '{}'::jsonb)
 WHERE (meta IS NULL OR meta = '{}'::jsonb)
   AND metadata IS NOT NULL
   AND metadata <> '{}'::jsonb;

CREATE UNIQUE INDEX IF NOT EXISTS uq_interactions_work_session_client_request
    ON public.interactions (user_id, (meta ->> 'client_request_id'))
 WHERE interaction_type = 'work_session'
   AND deleted_at IS NULL
   AND meta ->> 'client_request_id' IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_interactions_work_sessions
    ON public.interactions (user_id, date DESC)
 WHERE interaction_type = 'work_session'
   AND deleted_at IS NULL;
