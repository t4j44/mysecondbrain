-- Restrict the RLS helper to the authenticated principal, never an arbitrary UUID.
-- account_closures has no client-readable policies by design; SECURITY DEFINER is
-- required for the restrictive account_active_guard policies to see closure rows.
-- Keep the existing function signature because those policies depend on it.
CREATE OR REPLACE FUNCTION public.account_active(owner uuid)
RETURNS boolean
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path TO ''
AS $fn$
  SELECT COALESCE(owner = (SELECT auth.uid()), false)
    AND NOT EXISTS (
      SELECT 1 FROM public.account_closures WHERE user_id = owner
    )
$fn$;

REVOKE EXECUTE ON FUNCTION public.account_active(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.account_active(uuid) TO authenticated, service_role;
