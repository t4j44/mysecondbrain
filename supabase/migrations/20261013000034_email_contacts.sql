-- When the user last sent mail to, and last received mail from, each saved person, per connected
-- Google account. Dates only: no subject, snippet, body, address or message id is stored.
-- Rows are derived, rebuilt by re-syncing, and removed with the person, the connection or the account.
ALTER TABLE public.integrations ADD CONSTRAINT integrations_owner_identity UNIQUE(user_id,id);
CREATE TABLE public.email_contacts (
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 integration_id uuid NOT NULL,
 person_id uuid NOT NULL,
 last_sent_at timestamptz,
 last_received_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(integration_id,person_id),
 CONSTRAINT email_contacts_has_a_date CHECK(last_sent_at IS NOT NULL OR last_received_at IS NOT NULL),
 FOREIGN KEY(user_id,integration_id) REFERENCES public.integrations(user_id,id) ON DELETE CASCADE,
 FOREIGN KEY(user_id,person_id) REFERENCES public.people(user_id,id) ON DELETE CASCADE
);
CREATE INDEX email_contacts_person ON public.email_contacts(user_id,person_id);
ALTER TABLE public.email_contacts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.email_contacts FROM anon;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.email_contacts TO authenticated,service_role;
CREATE POLICY owner_access ON public.email_contacts TO authenticated
 USING(user_id=auth.uid()) WITH CHECK(user_id=auth.uid());
CREATE POLICY account_active_guard ON public.email_contacts AS RESTRICTIVE TO authenticated
 USING(public.account_active(auth.uid())) WITH CHECK(public.account_active(auth.uid()));
