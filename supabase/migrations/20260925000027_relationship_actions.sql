-- Approved actions and receipts stay with the contact's owner.
ALTER TABLE public.people ADD CONSTRAINT people_owner_identity UNIQUE(user_id, id);
CREATE TABLE public.relationship_actions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 person_id uuid NOT NULL,
 request_id uuid NOT NULL,
 suggestion_key text NOT NULL,
 action varchar(30) NOT NULL CHECK (action IN ('completed','scheduled','dismissed')),
 outcome text,
 scheduled_at timestamptz,
 receipt jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT relationship_action_request UNIQUE(user_id, request_id),
 FOREIGN KEY(user_id, person_id) REFERENCES public.people(user_id, id) ON DELETE CASCADE
);
CREATE INDEX relationship_actions_owner_person ON public.relationship_actions(user_id, person_id);
ALTER TABLE public.relationship_actions ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.relationship_actions TO authenticated, service_role;
CREATE POLICY owner_access ON public.relationship_actions FOR ALL TO authenticated
 USING(user_id = auth.uid()) WITH CHECK(user_id = auth.uid());
CREATE POLICY account_active_guard ON public.relationship_actions AS RESTRICTIVE FOR ALL TO authenticated
 USING(public.account_active(auth.uid())) WITH CHECK(public.account_active(auth.uid()));
