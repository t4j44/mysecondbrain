CREATE TABLE public.public_profile_claims (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 person_id uuid NOT NULL,
 field varchar(40) NOT NULL CHECK(field IN ('role','company','industry','location','professional_context')),
 value text NOT NULL, source_url text NOT NULL, source_type varchar(40) NOT NULL,
 source_quote text NOT NULL, researched_at timestamptz NOT NULL, identity_basis text NOT NULL,
 confidence varchar(40) NOT NULL DEFAULT 'single_source', confidence_reason text NOT NULL,
 verification_state varchar(30) NOT NULL DEFAULT 'proposed' CHECK(verification_state IN ('proposed','verified','rejected')),
 memory_id uuid, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(user_id, person_id) REFERENCES public.people(user_id, id) ON DELETE CASCADE
);
CREATE INDEX public_profile_claims_owner_person ON public.public_profile_claims(user_id, person_id);
ALTER TABLE public.public_profile_claims ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.public_profile_claims TO authenticated, service_role;
CREATE POLICY owner_access ON public.public_profile_claims FOR ALL TO authenticated
 USING(user_id = auth.uid()) WITH CHECK(user_id = auth.uid());
CREATE POLICY account_active_guard ON public.public_profile_claims AS RESTRICTIVE FOR ALL TO authenticated
 USING(public.account_active(auth.uid())) WITH CHECK(public.account_active(auth.uid()));
