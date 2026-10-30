-- ============================================================================
-- Migration: 0020_harden_rls_authorization_boundary.sql
-- Description: Make RLS a real authorization boundary for API traffic (G2).
--              1. Every public table owning a user_id gets RLS enabled and the
--                 explicit owner form: auth.uid() IS NOT NULL AND user_id = auth.uid().
--                 Driving the loop off the catalog means no table can be missed.
--              2. Table privileges are granted to `authenticated` so the API's
--                 SET LOCAL ROLE authenticated transactions reach the policies at all,
--                 while the token vault stays unreachable for that role.
--              3. Child tables whose ownership is indirect (document_chunks,
--                 embeddings, embedding_jobs) additionally require the parent row to
--                 belong to the caller, so a chunk can never be attached to another
--                 user's document.
--              4. profiles gains a self-scoped INSERT policy (the application creates
--                 the caller's own profile row on first use).
--              Existing policy names are reused, so this migration is idempotent and
--              does not remove protection anywhere.
-- Author: Agent — Principal Application Security / PostgreSQL Authorization (G2)
-- ============================================================================

-- Tables handled explicitly below and therefore excluded from the generic loop.
-- profiles is keyed on id, audit_logs is append-only, integration_tokens is a vault
-- with intentionally zero policies.
DO $$
DECLARE
    t TEXT;
    special TEXT[] := ARRAY['profiles', 'audit_logs', 'integration_tokens'];
BEGIN
    FOR t IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND a.attname = 'user_id'
          AND a.attnum > 0
          AND NOT a.attisdropped
          AND NOT (c.relname = ANY(special))
        ORDER BY c.relname
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON public.%I TO authenticated;', t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_SELECT_%I" ON public.%I;', t, t);
        EXECUTE format(
            'CREATE POLICY "Policy_SELECT_%I" ON public.%I FOR SELECT '
            'USING (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_INSERT_%I" ON public.%I;', t, t);
        EXECUTE format(
            'CREATE POLICY "Policy_INSERT_%I" ON public.%I FOR INSERT '
            'WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_UPDATE_%I" ON public.%I;', t, t);
        EXECUTE format(
            'CREATE POLICY "Policy_UPDATE_%I" ON public.%I FOR UPDATE '
            'USING (auth.uid() IS NOT NULL AND user_id = auth.uid()) '
            'WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_DELETE_%I" ON public.%I;', t, t);
        EXECUTE format(
            'CREATE POLICY "Policy_DELETE_%I" ON public.%I FOR DELETE '
            'USING (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);
    END LOOP;
END $$;


-- ---------------------------------------------------------------------------
-- Indirect ownership: the parent row must also belong to the caller.
-- Replaces (not supplements) the generic write policies, because multiple
-- permissive policies for one command are OR'ed and would weaken the check.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS "Policy_INSERT_document_chunks" ON public.document_chunks;
CREATE POLICY "Policy_INSERT_document_chunks" ON public.document_chunks
    FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL
        AND user_id = auth.uid()
        AND EXISTS (
            SELECT 1 FROM public.documents d
            WHERE d.id = document_id AND d.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Policy_UPDATE_document_chunks" ON public.document_chunks;
CREATE POLICY "Policy_UPDATE_document_chunks" ON public.document_chunks
    FOR UPDATE USING (auth.uid() IS NOT NULL AND user_id = auth.uid())
    WITH CHECK (
        auth.uid() IS NOT NULL
        AND user_id = auth.uid()
        AND EXISTS (
            SELECT 1 FROM public.documents d
            WHERE d.id = document_id AND d.user_id = auth.uid()
        )
    );

DO $$
DECLARE
    t TEXT;
    tables TEXT[] := ARRAY['embeddings', 'embedding_jobs'];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        EXECUTE format('DROP POLICY IF EXISTS "Policy_INSERT_%I" ON public.%I;', t, t);
        EXECUTE format(
            'CREATE POLICY "Policy_INSERT_%I" ON public.%I FOR INSERT WITH CHECK ('
            '  auth.uid() IS NOT NULL AND user_id = auth.uid()'
            '  AND (document_chunk_id IS NULL OR EXISTS ('
            '    SELECT 1 FROM public.document_chunks ch'
            '    WHERE ch.id = document_chunk_id AND ch.user_id = auth.uid()))'
            ');', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_UPDATE_%I" ON public.%I;', t, t);
        EXECUTE format(
            'CREATE POLICY "Policy_UPDATE_%I" ON public.%I FOR UPDATE '
            'USING (auth.uid() IS NOT NULL AND user_id = auth.uid()) '
            'WITH CHECK ('
            '  auth.uid() IS NOT NULL AND user_id = auth.uid()'
            '  AND (document_chunk_id IS NULL OR EXISTS ('
            '    SELECT 1 FROM public.document_chunks ch'
            '    WHERE ch.id = document_chunk_id AND ch.user_id = auth.uid()))'
            ');', t, t);
    END LOOP;
END $$;


-- ---------------------------------------------------------------------------
-- profiles: keyed on id, self-service only.
-- ---------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON public.profiles TO authenticated;

DROP POLICY IF EXISTS "Users view own profile" ON public.profiles;
CREATE POLICY "Users view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() IS NOT NULL AND id = auth.uid());

DROP POLICY IF EXISTS "Users update own profile" ON public.profiles;
CREATE POLICY "Users update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() IS NOT NULL AND id = auth.uid())
    WITH CHECK (auth.uid() IS NOT NULL AND id = auth.uid());

-- The application creates the caller's own profile row on first use (MCP credentials,
-- onboarding). Restricted to the caller's own id; no DELETE policy.
DROP POLICY IF EXISTS "Users insert own profile" ON public.profiles;
CREATE POLICY "Users insert own profile" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL AND id = auth.uid());


-- ---------------------------------------------------------------------------
-- audit_logs: immutable append-only. No UPDATE or DELETE policy, and the
-- authenticated role is not granted those privileges either.
-- ---------------------------------------------------------------------------
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
REVOKE UPDATE, DELETE ON public.audit_logs FROM authenticated;
GRANT SELECT, INSERT ON public.audit_logs TO authenticated;

DROP POLICY IF EXISTS "Users view own audit logs" ON public.audit_logs;
CREATE POLICY "Users view own audit logs" ON public.audit_logs
    FOR SELECT USING (auth.uid() IS NOT NULL AND user_id = auth.uid());

DROP POLICY IF EXISTS "Users insert own audit logs" ON public.audit_logs;
CREATE POLICY "Users insert own audit logs" ON public.audit_logs
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- integration_tokens: OAuth vault. RLS on, zero policies, and no privileges for
-- the authenticated role, so encrypted tokens are reachable only from the
-- privileged admin database context.
-- ---------------------------------------------------------------------------
ALTER TABLE public.integration_tokens ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.integration_tokens FROM authenticated;

DO $$
DECLARE
    p TEXT;
BEGIN
    FOR p IN
        SELECT policyname FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'integration_tokens'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.integration_tokens;', p);
    END LOOP;
END $$;
