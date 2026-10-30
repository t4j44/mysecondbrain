-- Only explicitly reviewed snapshots may be served through the public API.
CREATE TABLE public.portfolio_publications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    draft_id uuid NOT NULL REFERENCES public.content_items(id) ON DELETE CASCADE,
    token_hash varchar(64) NOT NULL UNIQUE,
    snapshot jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz
);
CREATE INDEX portfolio_publications_owner ON public.portfolio_publications(user_id);
ALTER TABLE public.portfolio_publications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_publications FORCE ROW LEVEL SECURITY;
CREATE POLICY portfolio_publications_owner ON public.portfolio_publications TO authenticated
    USING (auth.uid() IS NOT NULL AND user_id = auth.uid())
    WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid() AND EXISTS (
        SELECT 1 FROM public.content_items c WHERE c.id = draft_id AND c.user_id = auth.uid()
    ));
GRANT SELECT, INSERT, UPDATE, DELETE ON public.portfolio_publications TO authenticated;
REVOKE ALL ON public.portfolio_publications FROM anon;

CREATE TABLE public.beta_feedback (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    outcome varchar(32) NOT NULL CHECK (outcome IN ('useful', 'not_useful', 'incorrect', 'bug')),
    note text,
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.beta_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.beta_feedback FORCE ROW LEVEL SECURITY;
CREATE POLICY beta_feedback_owner ON public.beta_feedback TO authenticated
    USING (auth.uid() IS NOT NULL AND user_id = auth.uid())
    WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid());
GRANT SELECT, INSERT, UPDATE, DELETE ON public.beta_feedback TO authenticated;
REVOKE ALL ON public.beta_feedback FROM anon;
