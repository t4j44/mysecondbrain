-- ============================================================================
-- Migration: 0022_network_relationship_intelligence.sql
-- Description: Turn the Network domain from contact storage into queryable
--              relationship intelligence.
--
--              1. `public.person_organization_roles` — a person can belong to
--                 many organizations, with a role, a relationship type, a
--                 primary flag and a start/end window. `people.organization_id`
--                 could only ever express one affiliation and no history.
--              2. `public.commitments` — promises become first-class rows with
--                 a direction, a status and a due date, so "what did they
--                 promise me", "what do I owe them" and "what is overdue" are
--                 index-backed queries. `interactions.commitments TEXT[]` is a
--                 free-text bag that cannot answer any of them.
--
--              Both legacy fields are BACKFILLED and then DEPRECATED IN PLACE.
--              Nothing is dropped and nothing is discarded by this migration.
--
-- Author: Agent — Senior CRM / Relationship Graph Data Engineer (G5.5)
-- Notes: Migrated commitment rows carry direction 'unspecified' because the
--        legacy TEXT[] never recorded who owed whom. They are NOT guessed into
--        'owed_to_me' / 'owed_by_me'; the counterparty stays reachable through
--        `interaction_id`, and the source array is left intact for re-reading.
-- ============================================================================

-- 1. Person ↔ Organization roles (multi-organization affiliation with history)
CREATE TABLE IF NOT EXISTS public.person_organization_roles (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.people(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    role TEXT,
    relationship_type TEXT NOT NULL DEFAULT 'contact',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    source TEXT NOT NULL DEFAULT 'manual',
    confidence NUMERIC NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_person_organization_roles_window CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at)
);

DROP TRIGGER IF EXISTS trg_person_organization_roles_updated_at ON public.person_organization_roles;
CREATE TRIGGER trg_person_organization_roles_updated_at
    BEFORE UPDATE ON public.person_organization_roles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- One live affiliation row per (person, organization, role). Re-running an
-- importer cannot fan a single real-world role out into duplicates.
CREATE UNIQUE INDEX IF NOT EXISTS uq_person_organization_roles_live
    ON public.person_organization_roles (user_id, person_id, organization_id, COALESCE(role, ''))
 WHERE deleted_at IS NULL
   AND ended_at IS NULL;


-- 2. Commitments (first-class promises, in both directions)
CREATE TABLE IF NOT EXISTS public.commitments (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    from_person_id UUID REFERENCES public.people(id) ON DELETE SET NULL,
    to_person_id UUID REFERENCES public.people(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    venture_id UUID REFERENCES public.ventures(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    interaction_id UUID REFERENCES public.interactions(id) ON DELETE SET NULL,
    meeting_id UUID REFERENCES public.meetings(id) ON DELETE SET NULL,
    -- owed_to_me: they promised me. owed_by_me: I owe them.
    -- unspecified: direction genuinely unknown (legacy import) — never guessed.
    direction TEXT NOT NULL DEFAULT 'unspecified' CHECK (direction IN ('owed_to_me', 'owed_by_me', 'unspecified')),
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'completed', 'cancelled')),
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    source TEXT NOT NULL DEFAULT 'manual',
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_commitments_updated_at ON public.commitments;
CREATE TRIGGER trg_commitments_updated_at
    BEFORE UPDATE ON public.commitments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- 3. Indexes for the relationship queries this gate must answer
CREATE INDEX IF NOT EXISTS idx_person_org_roles_person ON public.person_organization_roles(user_id, person_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_person_org_roles_org ON public.person_organization_roles(user_id, organization_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_person_org_roles_current ON public.person_organization_roles(user_id, organization_id) WHERE deleted_at IS NULL AND ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_commitments_user_status ON public.commitments(user_id, status, due_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_overdue ON public.commitments(user_id, due_at) WHERE deleted_at IS NULL AND status = 'open' AND due_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_from_person ON public.commitments(user_id, from_person_id) WHERE deleted_at IS NULL AND from_person_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_to_person ON public.commitments(user_id, to_person_id) WHERE deleted_at IS NULL AND to_person_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_organization ON public.commitments(user_id, organization_id) WHERE deleted_at IS NULL AND organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_venture ON public.commitments(user_id, venture_id) WHERE deleted_at IS NULL AND venture_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_commitments_interaction ON public.commitments(user_id, interaction_id) WHERE deleted_at IS NULL AND interaction_id IS NOT NULL;


-- 4. Row Level Security (G2 intentional owner form: identity must be present)
DO $$
DECLARE
    t TEXT;
    tables TEXT[] := ARRAY['person_organization_roles', 'commitments'];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON public.%I TO authenticated;', t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_SELECT_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_SELECT_%I" ON public.%I FOR SELECT USING (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_INSERT_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_INSERT_%I" ON public.%I FOR INSERT WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_UPDATE_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_UPDATE_%I" ON public.%I FOR UPDATE USING (auth.uid() IS NOT NULL AND user_id = auth.uid()) WITH CHECK (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);

        EXECUTE format('DROP POLICY IF EXISTS "Policy_DELETE_%I" ON public.%I;', t, t);
        EXECUTE format('CREATE POLICY "Policy_DELETE_%I" ON public.%I FOR DELETE USING (auth.uid() IS NOT NULL AND user_id = auth.uid());', t, t);
    END LOOP;
END $$;


-- 5. Cross-tenant integrity: a role may only ever join a person and an
--    organization that belong to the same owner as the role row itself.
CREATE OR REPLACE FUNCTION public.validate_person_organization_role_ownership()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.people p WHERE p.id = NEW.person_id AND p.user_id = NEW.user_id
    ) THEN
        RAISE EXCEPTION 'person_organization_roles.person_id % does not belong to user %', NEW.person_id, NEW.user_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.organizations o WHERE o.id = NEW.organization_id AND o.user_id = NEW.user_id
    ) THEN
        RAISE EXCEPTION 'person_organization_roles.organization_id % does not belong to user %', NEW.organization_id, NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DROP TRIGGER IF EXISTS trg_validate_person_organization_role ON public.person_organization_roles;
CREATE TRIGGER trg_validate_person_organization_role
    BEFORE INSERT OR UPDATE ON public.person_organization_roles
    FOR EACH ROW EXECUTE FUNCTION public.validate_person_organization_role_ownership();


-- 6. Backfill: every existing people.organization_id becomes a primary role.
--    people.role is carried across so no information is lost.
INSERT INTO public.person_organization_roles (
    user_id, person_id, organization_id, role, relationship_type, is_primary, started_at, source, confidence
)
SELECT p.user_id,
       p.id,
       p.organization_id,
       p.role,
       p.relationship_type::text,
       true,
       p.created_at,
       'migrated:people.organization_id',
       1.0
  FROM public.people p
  JOIN public.organizations o
    ON o.id = p.organization_id
   AND o.user_id = p.user_id
 WHERE p.organization_id IS NOT NULL
   AND NOT EXISTS (
       SELECT 1 FROM public.person_organization_roles r
        WHERE r.user_id = p.user_id
          AND r.person_id = p.id
          AND r.organization_id = p.organization_id
   );


-- 7. Backfill: every interactions.commitments[] entry becomes a commitment row.
--    Direction is 'unspecified' — the array never recorded who owed whom, and
--    this migration does not invent one. The counterparty remains reachable
--    through interaction_id, and the source array is left in place.
INSERT INTO public.commitments (
    user_id, from_person_id, to_person_id, organization_id, venture_id, project_id,
    interaction_id, meeting_id, direction, description, status, source
)
SELECT i.user_id,
       NULL,
       NULL,
       (SELECT p.organization_id FROM public.people p WHERE p.id = i.person_id AND p.user_id = i.user_id),
       i.venture_id,
       i.project_id,
       i.id,
       i.meeting_id,
       'unspecified',
       btrim(c.description),
       'open',
       'migrated:interactions.commitments'
  FROM public.interactions i
 CROSS JOIN LATERAL unnest(i.commitments) AS c(description)
 WHERE i.commitments IS NOT NULL
   AND btrim(COALESCE(c.description, '')) <> ''
   AND NOT EXISTS (
       SELECT 1 FROM public.commitments existing
        WHERE existing.interaction_id = i.id
          AND existing.description = btrim(c.description)
   );


-- 8. Deprecate the legacy fields IN PLACE. They are retained so historical
--    reads keep working and so nothing written before 0022 is lost.
COMMENT ON COLUMN public.people.organization_id IS
    'DEPRECATED as of migration 0022. Superseded by public.person_organization_roles, which supports multiple organizations, roles and history. Retained (not dropped) for backward compatibility; treat person_organization_roles as authoritative.';

COMMENT ON COLUMN public.interactions.commitments IS
    'DEPRECATED as of migration 0022. Superseded by public.commitments, which is queryable by direction, status and due date. Retained (not dropped) for backward compatibility; treat public.commitments as authoritative.';

COMMENT ON TABLE public.person_organization_roles IS
    'Authoritative person-to-organization affiliation. A person may hold many roles across many organizations; ended_at retains historical affiliations.';

COMMENT ON TABLE public.commitments IS
    'Authoritative first-class commitments. direction owed_to_me = they promised me; owed_by_me = I owe them; unspecified = legacy import with no recorded direction.';
