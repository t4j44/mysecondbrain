ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS conversion_metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
