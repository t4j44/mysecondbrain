-- Additive, default-off assistant foundation. No bot or external service activation.
CREATE TABLE public.assistant_preferences (
 user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
 timezone text NOT NULL,
 quiet_start_minute integer NOT NULL DEFAULT 1320 CHECK(quiet_start_minute BETWEEN 0 AND 1439),
 quiet_end_minute integer NOT NULL DEFAULT 480 CHECK(quiet_end_minute BETWEEN 0 AND 1439),
 quiet_enabled boolean NOT NULL DEFAULT true,
 telegram_enabled boolean NOT NULL DEFAULT false,
 include_details boolean NOT NULL DEFAULT false,
 daily_cap integer NOT NULL DEFAULT 3 CHECK(daily_cap BETWEEN 1 AND 5),
 version integer NOT NULL DEFAULT 1 CHECK(version > 0),
 consent_at timestamptz, revoked_at timestamptz, updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(NOT quiet_enabled OR quiet_start_minute <> quiet_end_minute),
 CHECK(NOT telegram_enabled OR (consent_at IS NOT NULL AND revoked_at IS NULL))
);
CREATE TABLE public.messaging_connections (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 provider varchar(30) NOT NULL DEFAULT 'telegram' CHECK(provider='telegram'),
 status varchar(20) NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','active','revoked')),
 external_chat_hash text, external_user_hash text,
 encrypted_chat_id text, encrypted_user_id text,
 nonce_hash text UNIQUE, nonce_expires_at timestamptz,
 revision integer NOT NULL DEFAULT 1 CHECK(revision > 0),
 linked_at timestamptz, revoked_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,provider), UNIQUE(user_id,id), UNIQUE(provider,external_chat_hash), UNIQUE(provider,external_user_hash),
 CHECK((nonce_hash IS NULL) = (nonce_expires_at IS NULL)),
 CHECK(status <> 'active' OR (external_chat_hash IS NOT NULL AND external_user_hash IS NOT NULL
   AND encrypted_chat_id IS NOT NULL AND encrypted_user_id IS NOT NULL AND linked_at IS NOT NULL
   AND revoked_at IS NULL AND nonce_hash IS NULL)),
 CHECK(status <> 'revoked' OR (external_chat_hash IS NULL AND external_user_hash IS NULL
   AND encrypted_chat_id IS NULL AND encrypted_user_id IS NULL AND nonce_hash IS NULL))
);
CREATE TABLE public.messaging_update_receipts (
 provider varchar(30) NOT NULL DEFAULT 'telegram' CHECK(provider='telegram'),
 update_id bigint NOT NULL CHECK(update_id >= 0),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 connection_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(provider,update_id),
 FOREIGN KEY(user_id,connection_id) REFERENCES public.messaging_connections(user_id,id) ON DELETE CASCADE
);
CREATE INDEX messaging_update_receipts_owner ON public.messaging_update_receipts(user_id);
-- The shared server-connection predicate is already defined by migration 32.
-- RLS still runs as the authenticated owner; PostgREST cannot forge bindings or consent.
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['assistant_preferences','messaging_connections','messaging_update_receipts'] LOOP
 EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON public.%I FROM anon,authenticated',t);
 EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated,service_role',t);
 EXECUTE format('CREATE POLICY assistant_server_owner ON public.%I FOR ALL TO authenticated USING(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection()) WITH CHECK(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())',t);
 END LOOP;
END $$;
