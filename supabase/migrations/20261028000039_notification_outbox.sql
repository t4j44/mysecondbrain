-- Durable transport state only. No trigger performs an external send.
CREATE TABLE public.notification_outbox (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 commitment_id uuid NOT NULL,
 commitment_revision integer NOT NULL CHECK(commitment_revision > 0),
 connection_id uuid NOT NULL,
 connection_revision integer NOT NULL CHECK(connection_revision > 0),
 preferences_version integer NOT NULL CHECK(preferences_version > 0),
 channel varchar(30) NOT NULL DEFAULT 'telegram' CHECK(channel = 'telegram'),
 slot varchar(30) NOT NULL DEFAULT 'explicit_check_in' CHECK(slot = 'explicit_check_in'),
 status varchar(20) NOT NULL DEFAULT 'queued'
  CHECK(status IN ('queued','leased','dispatching','delivered','uncertain','cancelled','failed')),
 scheduled_at timestamptz NOT NULL,
 available_at timestamptz NOT NULL,
 lease_token uuid,
 lease_until timestamptz,
 dispatch_started_at timestamptz,
 delivered_at timestamptz,
 provider_message_id varchar(100),
 error_code varchar(50),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,commitment_id,commitment_revision,channel,slot),
 FOREIGN KEY(user_id,commitment_id) REFERENCES public.commitments(user_id,id) ON DELETE CASCADE,
 FOREIGN KEY(user_id,connection_id) REFERENCES public.messaging_connections(user_id,id) ON DELETE CASCADE,
 CHECK(status NOT IN ('leased','dispatching') OR (lease_token IS NOT NULL AND lease_until IS NOT NULL)),
 CHECK(status != 'dispatching' OR dispatch_started_at IS NOT NULL),
 CHECK(status != 'delivered' OR (delivered_at IS NOT NULL AND provider_message_id IS NOT NULL))
);
CREATE INDEX notification_outbox_due ON public.notification_outbox(status,available_at);
CREATE INDEX notification_outbox_owner_usage ON public.notification_outbox(user_id,dispatch_started_at);
ALTER TABLE public.notification_outbox ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.notification_outbox FROM anon,authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.notification_outbox TO authenticated,service_role;
CREATE POLICY notification_outbox_server_owner ON public.notification_outbox FOR ALL TO authenticated
 USING(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())
 WITH CHECK(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection());
