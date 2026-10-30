-- Additive processing metadata. Meetings and all CRM records stay canonical.
CREATE TABLE public.usage_counters (
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 metric text NOT NULL, period_start timestamptz NOT NULL,
 quantity integer NOT NULL DEFAULT 0 CHECK(quantity >= 0),
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,metric,period_start), UNIQUE(user_id,metric,period_start)
);
ALTER TABLE public.meetings ADD CONSTRAINT meetings_owner_identity UNIQUE(user_id,id);
CREATE TABLE public.meeting_captures (
 meeting_id uuid PRIMARY KEY REFERENCES public.meetings(id) ON DELETE CASCADE,
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 request_id uuid NOT NULL, state varchar(40) NOT NULL DEFAULT 'draft'
 CHECK(state IN ('draft','recording','uploading','uploaded','transcribing','extracting','awaiting_review','completed','failed')),
 audio_path text CHECK(audio_path IS NULL OR split_part(audio_path,'/',1)=user_id::text),
 audio_mime text, audio_checksum text,
 duration_seconds integer NOT NULL DEFAULT 0 CHECK(duration_seconds>=0),
 charged_seconds integer NOT NULL DEFAULT 0 CHECK(charged_seconds>=0),
 live_seconds integer NOT NULL DEFAULT 0 CHECK(live_seconds>=0),
 period_start timestamptz NOT NULL, retained_until timestamptz, audio_deleted_at timestamptz,
 consent_at timestamptz NOT NULL, data_mode text NOT NULL,
 transcript_segments jsonb NOT NULL DEFAULT '[]', intelligence jsonb NOT NULL DEFAULT '{}',
 speaker_mappings jsonb NOT NULL DEFAULT '{}', receipt jsonb NOT NULL DEFAULT '{}',
 confirmed_at timestamptz, error_code varchar(80),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,request_id),
 FOREIGN KEY(user_id,meeting_id) REFERENCES public.meetings(user_id,id) ON DELETE CASCADE
);
CREATE INDEX meeting_audio_expiry ON public.meeting_captures(retained_until) WHERE audio_deleted_at IS NULL;
-- RLS still runs as authenticated. Only the owning application DB login may write
-- provider/billing state; PostgREST's authenticator login cannot forge usage/receipts.
-- Production DATABASE_URL must use the existing postgres server login.
CREATE FUNCTION public.meeting_server_connection() RETURNS boolean
 LANGUAGE sql STABLE SECURITY INVOKER SET search_path='' AS $$
 SELECT session_user = 'postgres'
$$;
REVOKE ALL ON FUNCTION public.meeting_server_connection() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.meeting_server_connection() TO authenticated,service_role;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['usage_counters','meeting_captures'] LOOP
 EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
 EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated,service_role',t);
 EXECUTE format('CREATE POLICY owner_read ON public.%I FOR SELECT TO authenticated USING(user_id=auth.uid() AND public.account_active(auth.uid()))',t);
 EXECUTE format('CREATE POLICY server_insert ON public.%I FOR INSERT TO authenticated WITH CHECK(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())',t);
 EXECUTE format('CREATE POLICY server_update ON public.%I FOR UPDATE TO authenticated USING(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection()) WITH CHECK(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())',t);
 EXECUTE format('CREATE POLICY server_delete ON public.%I FOR DELETE TO authenticated USING(user_id=auth.uid() AND public.account_active(auth.uid()) AND public.meeting_server_connection())',t);
 END LOOP;
END $$;
DO $$ BEGIN
 IF to_regclass('storage.objects') IS NOT NULL THEN
 INSERT INTO storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 VALUES('meeting-audio','meeting-audio',false,52428800,ARRAY['audio/webm','audio/mpeg','audio/mp3','audio/mp4','audio/m4a','audio/x-m4a','audio/wav','audio/aac','audio/ogg','audio/flac','audio/opus'])
 ON CONFLICT(id) DO UPDATE SET public=false,file_size_limit=52428800,allowed_mime_types=EXCLUDED.allowed_mime_types;
 -- No client UPDATE/upsert: a finalized source must never be replaced.
 EXECUTE $p$CREATE POLICY meeting_audio_read ON storage.objects FOR SELECT TO authenticated
 USING(bucket_id='meeting-audio' AND split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid()))$p$;
 EXECUTE $p$CREATE POLICY meeting_audio_insert ON storage.objects FOR INSERT TO authenticated
 WITH CHECK(bucket_id='meeting-audio' AND split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid()))$p$;
 EXECUTE $p$CREATE POLICY meeting_audio_guard ON storage.objects AS RESTRICTIVE FOR ALL TO authenticated
 USING(bucket_id<>'meeting-audio' OR (split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid())))
 WITH CHECK(bucket_id<>'meeting-audio' OR (split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid())))$p$;
 EXECUTE $p$CREATE POLICY meeting_audio_anon_guard ON storage.objects AS RESTRICTIVE FOR ALL TO anon
 USING(bucket_id<>'meeting-audio') WITH CHECK(bucket_id<>'meeting-audio')$p$;
 EXECUTE $p$CREATE POLICY meeting_audio_no_replace ON storage.objects AS RESTRICTIVE FOR UPDATE TO authenticated
 USING(bucket_id<>'meeting-audio' AND auth.uid() IS NOT NULL) WITH CHECK(bucket_id<>'meeting-audio' AND auth.uid() IS NOT NULL)$p$;
 END IF;
END $$;
