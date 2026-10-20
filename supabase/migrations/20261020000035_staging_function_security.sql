-- Staging security hardening: close RPC access to trigger-only SECURITY DEFINER functions.
-- Retain authenticated execution of account_active(uuid) for restrictive RLS policies.
-- Add pinned search paths to trigger functions; references inside are schema-qualified.
DO $$
DECLARE fn record;
BEGIN
  FOR fn IN
    SELECT p.oid::regprocedure AS signature
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.prosecdef
      AND p.proname <> 'account_active'
      AND p.prorettype = 'pg_catalog.trigger'::regtype
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC, anon, authenticated', fn.signature);
  END LOOP;
END $$;

REVOKE EXECUTE ON FUNCTION public.account_active(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.account_active(uuid) TO authenticated, service_role;
ALTER FUNCTION public.set_updated_at() SET search_path = '';
ALTER FUNCTION public.handle_task_completion() SET search_path = '';
ALTER FUNCTION public.update_person_last_interaction() SET search_path = '';
