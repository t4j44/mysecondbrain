ALTER TABLE public.notification_outbox
 ADD CONSTRAINT notification_outbox_owner_identity UNIQUE(user_id,id),
 ADD COLUMN attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count BETWEEN 0 AND 3);
CREATE TABLE public.notification_delivery_attempts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 outbox_id uuid NOT NULL,
 attempt_number integer NOT NULL CHECK(attempt_number BETWEEN 1 AND 3),
 status varchar(20) NOT NULL DEFAULT 'started' CHECK(status IN ('started','delivered','failed','uncertain')),
 error_code varchar(50),
 started_at timestamptz NOT NULL DEFAULT now(),
 completed_at timestamptz,
 UNIQUE(outbox_id,attempt_number),
 FOREIGN KEY(user_id,outbox_id) REFERENCES public.notification_outbox(user_id,id) ON DELETE CASCADE
);
CREATE INDEX notification_attempts_owner ON public.notification_delivery_attempts(user_id,started_at);
CREATE TABLE public.messaging_callback_tokens (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 outbox_id uuid NOT NULL,
 token_hash varchar(64) NOT NULL UNIQUE,
 action varchar(20) NOT NULL CHECK(action IN ('done','working','snooze','help','stop')),
 expires_at timestamptz NOT NULL,
 used_at timestamptz,
 acknowledgement varchar(200),
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(user_id,outbox_id) REFERENCES public.notification_outbox(user_id,id) ON DELETE CASCADE
);
CREATE INDEX messaging_callbacks_owner ON public.messaging_callback_tokens(user_id,outbox_id);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['notification_delivery_attempts','messaging_callback_tokens'] LOOP
 EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON public.%I FROM anon,authenticated',t);
 EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated,service_role',t);
 EXECUTE format('CREATE POLICY delivery_server_owner ON public.%I FOR ALL TO authenticated USING(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection()) WITH CHECK(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())',t);
 END LOOP;
END $$;
