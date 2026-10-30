-- SECOND BRAIN V2 — read-only post-migration RLS acceptance query.
-- Run ONLY against the authorized isolated staging database after
-- migrations 37-40 and before allowing V2 API writes.
-- It does not read customer records or change any database objects.
WITH expected(table_name) AS (
  VALUES ('assistant_preferences'),
         ('messaging_connections'),
         ('messaging_update_receipts'),
         ('commitment_actions'),
         ('notification_outbox'),
         ('notification_delivery_attempts'),
         ('messaging_callback_tokens')
), table_checks AS (
  SELECT e.table_name,
         c.oid IS NOT NULL AS exists_in_public,
         COALESCE(c.relrowsecurity, FALSE) AS rls_enabled,
         COALESCE(
           EXISTS (
             SELECT 1 FROM pg_policies p
             WHERE p.schemaname = 'public'
               AND p.tablename = e.table_name
               AND p.cmd = 'ALL'
               AND p.roles @> ARRAY['authenticated']::name[]
               AND p.qual LIKE '%meeting_server_connection%'
               AND p.with_check LIKE '%meeting_server_connection%'
           ), FALSE
         ) AS server_bound_policy,
         CASE WHEN c.oid IS NULL THEN FALSE
              ELSE has_table_privilege('anon', c.oid, 'SELECT') END AS anonymous_select_grant
  FROM expected e
  LEFT JOIN pg_class c
    ON c.relname = e.table_name
   AND c.relnamespace = 'public'::regnamespace
   AND c.relkind IN ('r','p')
)
SELECT
  COUNT(*) AS expected_tables,
  COUNT(*) FILTER (WHERE exists_in_public) AS present_tables,
  COUNT(*) FILTER (WHERE rls_enabled) AS rls_enabled_tables,
  COUNT(*) FILTER (WHERE server_bound_policy) AS guarded_tables,
  COUNT(*) FILTER (WHERE anonymous_select_grant) AS anon_select_grants,
  ARRAY_AGG(table_name ORDER BY table_name)
    FILTER (WHERE NOT exists_in_public OR NOT rls_enabled
               OR NOT server_bound_policy OR anonymous_select_grant) AS failed_tables,
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'commitments' AND column_name = 'revision'
  ) AS commitment_revision_present
FROM table_checks;
