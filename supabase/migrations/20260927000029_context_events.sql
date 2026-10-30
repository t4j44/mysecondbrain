-- V1.5: preserve original context, event time and temporal graph provenance.
ALTER TABLE public.projects ADD CONSTRAINT projects_owner_identity UNIQUE(user_id, id);
ALTER TABLE public.ventures ADD CONSTRAINT ventures_owner_identity UNIQUE(user_id, id);
ALTER TABLE public.jobs ADD CONSTRAINT jobs_owner_identity UNIQUE(user_id, id);
CREATE TABLE public.context_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 event_type text NOT NULL CHECK(length(event_type) BETWEEN 1 AND 80),
 title text NOT NULL CHECK(length(title) BETWEEN 1 AND 500), summary text,
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(), timezone text NOT NULL DEFAULT 'UTC',
 source_type text NOT NULL, source_provider text, source_external_id text,
 idempotency_key text, raw_text text CHECK(length(raw_text) <= 64000),
 raw_payload jsonb NOT NULL DEFAULT '{}' CHECK(octet_length(raw_payload::text) <= 128000),
 extraction_version text, person_id uuid, venture_id uuid, project_id uuid,
 privacy_class text NOT NULL DEFAULT 'private' CHECK(privacy_class IN ('private','restricted')),
 metadata jsonb NOT NULL DEFAULT '{}', deleted_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT context_events_owner_identity UNIQUE(user_id,id),
 CONSTRAINT context_events_replay UNIQUE(user_id,idempotency_key),
 FOREIGN KEY(user_id,person_id) REFERENCES public.people(user_id,id) ON DELETE CASCADE,
 FOREIGN KEY(user_id,project_id) REFERENCES public.projects(user_id,id) ON DELETE CASCADE,
 FOREIGN KEY(user_id,venture_id) REFERENCES public.ventures(user_id,id) ON DELETE CASCADE
);
CREATE TRIGGER context_events_updated BEFORE UPDATE ON public.context_events
 FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE INDEX context_events_time ON public.context_events(user_id,occurred_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX context_events_type_time ON public.context_events(user_id,event_type,occurred_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX context_events_person_time ON public.context_events(user_id,person_id,occurred_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX context_events_project_time ON public.context_events(user_id,project_id,occurred_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX context_events_venture_time ON public.context_events(user_id,venture_id,occurred_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX context_events_source ON public.context_events(user_id,source_type,source_external_id);

ALTER TABLE public.entity_edges
 ADD COLUMN occurred_at timestamptz,
 ADD COLUMN valid_from timestamptz,
 ADD COLUMN valid_to timestamptz,
 ADD COLUMN source_event_id uuid,
 ADD COLUMN recorded_at timestamptz NOT NULL DEFAULT now(),
 ADD COLUMN confidence numeric NOT NULL DEFAULT 1 CHECK(confidence BETWEEN 0 AND 1),
 ADD CONSTRAINT entity_edge_window CHECK(valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
 ADD CONSTRAINT entity_edge_event_owner FOREIGN KEY(user_id,source_event_id)
   REFERENCES public.context_events(user_id,id) ON DELETE CASCADE;
-- Existing edges remain current. recorded_at is their original persistence time.
UPDATE public.entity_edges SET recorded_at=created_at;
ALTER TABLE public.entity_edges DROP CONSTRAINT uq_entity_edge;
CREATE UNIQUE INDEX uq_entity_edge_current ON public.entity_edges
 (user_id,source_entity_type,source_entity_id,target_entity_type,target_entity_id,relationship_type)
 WHERE valid_to IS NULL;
CREATE INDEX entity_edges_event ON public.entity_edges(user_id,source_event_id);

CREATE TABLE public.context_media (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 event_id uuid, draft_id uuid, request_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('business_card','moment')),
 storage_path text NOT NULL CHECK(split_part(storage_path,'/',1)=user_id::text),
 thumbnail_path text NOT NULL CHECK(split_part(thumbnail_path,'/',1)=user_id::text),
 mime_type text NOT NULL CHECK(mime_type IN ('image/webp','image/jpeg')),
 size_bytes integer NOT NULL CHECK(size_bytes BETWEEN 1 AND 2097152),
 width integer NOT NULL CHECK(width BETWEEN 1 AND 1600),
 height integer NOT NULL CHECK(height BETWEEN 1 AND 1600),
 thumbnail_bytes integer NOT NULL CHECK(thumbnail_bytes > 0),
 content_hash text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT context_media_replay UNIQUE(user_id,request_id),
 FOREIGN KEY(user_id,event_id) REFERENCES public.context_events(user_id,id) ON DELETE CASCADE,
 FOREIGN KEY(user_id,draft_id) REFERENCES public.jobs(user_id,id) ON DELETE CASCADE
);
CREATE INDEX context_media_event ON public.context_media(user_id,event_id);
CREATE INDEX context_media_draft ON public.context_media(user_id,draft_id);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['context_events','context_media'] LOOP
 EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated,service_role',t);
 EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
 EXECUTE format('CREATE POLICY owner_access ON public.%I TO authenticated USING(user_id=auth.uid()) WITH CHECK(user_id=auth.uid())',t);
 EXECUTE format('CREATE POLICY account_active_guard ON public.%I AS RESTRICTIVE TO authenticated USING(public.account_active(auth.uid())) WITH CHECK(public.account_active(auth.uid()))',t);
 END LOOP;
END $$;
