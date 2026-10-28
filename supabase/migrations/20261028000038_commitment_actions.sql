-- Additive follow-through on the existing canonical commitment ledger.
ALTER TABLE public.commitments
 ADD COLUMN revision integer NOT NULL DEFAULT 1 CHECK(revision > 0),
 ADD COLUMN reminder_at timestamptz,
 ADD COLUMN source_timezone varchar(100),
 ADD CONSTRAINT commitments_owner_identity UNIQUE(user_id,id);
ALTER TABLE public.commitments DROP CONSTRAINT commitments_status_check;
ALTER TABLE public.commitments ADD CONSTRAINT commitments_status_check
 CHECK(status IN ('open','in_progress','waiting','snoozed','completed','cancelled'));

CREATE FUNCTION public.advance_commitment_revision() RETURNS trigger
 LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
 NEW.revision := OLD.revision + 1;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public.advance_commitment_revision() FROM PUBLIC, anon, authenticated;
CREATE TRIGGER commitment_revision BEFORE UPDATE ON public.commitments
 FOR EACH ROW EXECUTE FUNCTION public.advance_commitment_revision();

CREATE TABLE public.commitment_actions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 commitment_id uuid NOT NULL,
 request_id uuid NOT NULL,
 action varchar(20) NOT NULL CHECK(action IN ('done','working','snooze','help','cancel')),
 request_hash varchar(64) NOT NULL,
 receipt jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,request_id),
 FOREIGN KEY(user_id,commitment_id) REFERENCES public.commitments(user_id,id) ON DELETE CASCADE
);
CREATE INDEX commitment_actions_source ON public.commitment_actions(user_id,commitment_id,created_at);
ALTER TABLE public.commitment_actions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.commitment_actions FROM anon,authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.commitment_actions TO authenticated,service_role;
CREATE POLICY commitment_action_server_owner ON public.commitment_actions FOR ALL TO authenticated
 USING(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())
 WITH CHECK(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection());
