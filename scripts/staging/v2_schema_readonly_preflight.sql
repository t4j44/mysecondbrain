-- V2 READ-ONLY staging schema preflight.
-- No DDL, no secret/data extraction, no writes. Run using a read-only
-- admin SQL interface before migrations 37-40 and again afterward.
-- Expected before upgrade: 7 missing V2 tables; commitment revision absent.
-- Expected after upgrade: 0 missing V2 tables; commitment revision present.
-- Presence is not proof of correct RLS, migration history, provider readiness,
-- recovery, or live two-account isolation.
WITH expected(name) AS (
 VALUES ('assistant_preferences'),
        ('messaging_connections'),
        ('messaging_update_receipts'),
        ('commitment_actions'),
        ('notification_outbox'),
        ('notification_delivery_attempts'),
        ('messaging_callback_tokens')
), relation_check AS (
 SELECT name, to_regclass(format('public.%I', name)) IS NOT NULL AS present
 FROM expected
)
SELECT
  (SELECT count(*) FROM relation_check WHERE present) AS v2_tables_present,
  (SELECT count(*) FROM relation_check WHERE NOT present) AS v2_tables_missing,
  (SELECT array_agg(name ORDER BY name) FROM relation_check WHERE NOT present) AS missing_tables,
  to_regprocedure('public.meeting_server_connection()') IS NOT NULL AS server_connection_check_present,
  to_regprocedure('public.account_active(uuid)') IS NOT NULL AS account_check_present,
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'commitments'
      AND column_name = 'revision'
  ) AS commitment_revision_present,
  EXISTS (SELECT 1 FROM auth.users LIMIT 1) AS has_existing_auth_accounts,
  EXISTS (SELECT 1 FROM public.commitments LIMIT 1) AS has_existing_commitment_data;
