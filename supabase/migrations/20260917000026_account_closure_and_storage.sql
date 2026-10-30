-- Receipt survives Auth deletion so old JWTs remain blocked.
CREATE TABLE public.account_closures (
 user_id uuid PRIMARY KEY, status varchar(30) NOT NULL DEFAULT 'pending',
 error_code varchar(100), requested_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.account_closures ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.account_closures FROM anon, authenticated;
GRANT ALL ON public.account_closures TO service_role;
CREATE FUNCTION public.account_active(owner uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
 SELECT NOT EXISTS (SELECT 1 FROM public.account_closures WHERE user_id = owner)
$$;
REVOKE ALL ON FUNCTION public.account_active(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.account_active(uuid) TO authenticated, service_role;
DO $$ DECLARE t text; BEGIN
 FOR t IN SELECT c.table_name FROM information_schema.columns c
 JOIN information_schema.tables b USING(table_schema, table_name)
 WHERE c.table_schema='public' AND c.column_name='user_id'
 AND b.table_type='BASE TABLE' AND c.table_name NOT IN ('account_closures', 'integration_tokens')
 LOOP
 EXECUTE format('CREATE POLICY account_active_guard ON public.%I AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_active(auth.uid())) WITH CHECK (public.account_active(auth.uid()))', t);
 END LOOP;
END $$;
CREATE POLICY account_active_guard ON public.profiles AS RESTRICTIVE FOR ALL TO authenticated
 USING (public.account_active(auth.uid())) WITH CHECK (public.account_active(auth.uid()));
-- Plain PostgreSQL has no Supabase Storage. Real staging HTTP tests remain required.
DO $$ BEGIN
IF to_regclass('storage.objects') IS NOT NULL THEN
 INSERT INTO storage.buckets(id, name, public) VALUES('brain-documents','brain-documents',false)
 ON CONFLICT(id) DO UPDATE SET public=false;
 EXECUTE $p$CREATE POLICY brain_private_owner ON storage.objects FOR ALL TO authenticated
 USING (bucket_id='brain-documents' AND split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid()))
 WITH CHECK (bucket_id='brain-documents' AND split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid()))$p$;
 EXECUTE $p$CREATE POLICY brain_private_guard ON storage.objects AS RESTRICTIVE FOR ALL TO authenticated
 USING (bucket_id <> 'brain-documents' OR (split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid())))
 WITH CHECK (bucket_id <> 'brain-documents' OR (split_part(name,'/',1)=auth.uid()::text AND public.account_active(auth.uid())))$p$;
 EXECUTE $p$CREATE POLICY brain_private_anon_guard ON storage.objects AS RESTRICTIVE FOR ALL TO anon
 USING (bucket_id <> 'brain-documents') WITH CHECK (bucket_id <> 'brain-documents')$p$;
END IF;
END $$;
