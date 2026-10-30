-- Let one user connect several Google accounts for each capability (Drive, Calendar, Gmail).
-- Additive and reversible: the old rule allowed one row per user and provider.
-- Rows connected before the account email was recorded keep a NULL identifier; they share
-- the empty key, so there is still at most one such row per user and provider.
ALTER TABLE public.integrations DROP CONSTRAINT IF EXISTS uq_integrations_user_provider;
CREATE UNIQUE INDEX IF NOT EXISTS uq_integrations_user_provider_account
 ON public.integrations (user_id, provider, (coalesce(lower(external_account_identifier), '')));
