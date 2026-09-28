-- MCP authorization vault. Only verified server operations may create grants/tokens.
CREATE TABLE public.mcp_oauth_clients (
 id text PRIMARY KEY, metadata jsonb NOT NULL, secret_hash text,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.mcp_oauth_requests (
 request_hash text PRIMARY KEY, user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
 client_id text NOT NULL REFERENCES public.mcp_oauth_clients(id) ON DELETE CASCADE,
 payload jsonb NOT NULL, expires_at timestamptz NOT NULL, consumed_at timestamptz
);
CREATE TABLE public.mcp_oauth_grants (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 client_id text NOT NULL REFERENCES public.mcp_oauth_clients(id),
 client_name text NOT NULL, scopes jsonb NOT NULL,
 issuer text NOT NULL, resource text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,
 last_used_at timestamptz, revoked_at timestamptz,
 UNIQUE(user_id,id)
);
CREATE INDEX mcp_oauth_grants_owner ON public.mcp_oauth_grants(user_id,created_at DESC);
CREATE TABLE public.mcp_oauth_codes (
 code_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 grant_id uuid NOT NULL, code_challenge text NOT NULL, redirect_uri text NOT NULL,
 expires_at timestamptz NOT NULL, consumed_at timestamptz,
 FOREIGN KEY(user_id,grant_id) REFERENCES public.mcp_oauth_grants(user_id,id) ON DELETE CASCADE
);
CREATE TABLE public.mcp_oauth_tokens (
 token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 grant_id uuid NOT NULL, kind text NOT NULL CHECK(kind IN ('access','refresh')),
 scopes jsonb NOT NULL, expires_at timestamptz NOT NULL, consumed_at timestamptz,
 FOREIGN KEY(user_id,grant_id) REFERENCES public.mcp_oauth_grants(user_id,id) ON DELETE CASCADE
);
CREATE INDEX mcp_oauth_tokens_grant ON public.mcp_oauth_tokens(user_id,grant_id);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['mcp_oauth_clients','mcp_oauth_requests','mcp_oauth_grants','mcp_oauth_codes','mcp_oauth_tokens'] LOOP
 EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON public.%I FROM anon,authenticated',t);
 EXECUTE format('GRANT ALL ON public.%I TO service_role',t);
 END LOOP;
END $$;
-- Owners may inspect their connection metadata; mutation goes through the consent/revoke API.
GRANT SELECT ON public.mcp_oauth_grants TO authenticated;
CREATE POLICY owner_read ON public.mcp_oauth_grants FOR SELECT TO authenticated
 USING(user_id=auth.uid() AND public.account_active(auth.uid()));
