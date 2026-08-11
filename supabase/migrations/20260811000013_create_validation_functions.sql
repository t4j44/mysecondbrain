-- ============================================================================
-- Migration: 0013_create_validation_functions.sql
-- Description: Implement ownership validation functions and cross-user defense triggers
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Validate Project to Venture Ownership
CREATE OR REPLACE FUNCTION public.validate_project_venture_ownership()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    IF NEW.venture_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM public.ventures WHERE id = NEW.venture_id AND user_id = NEW.user_id
        ) THEN
            RAISE EXCEPTION 'Cross-user or non-existent venture reference forbidden.' USING ERRCODE = 'P0001';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_project_venture ON public.projects;
CREATE TRIGGER trg_validate_project_venture
    BEFORE INSERT OR UPDATE OF venture_id, user_id ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.validate_project_venture_ownership();


-- 2. Validate Task Relationships (Venture, Project, Person compatibility)
CREATE OR REPLACE FUNCTION public.validate_task_relationships()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
    proj_venture_id UUID;
BEGIN
    -- Validate Venture Ownership
    IF NEW.venture_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.ventures WHERE id = NEW.venture_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Task venture must belong to the same user.' USING ERRCODE = 'P0001';
    END IF;

    -- Validate Project Ownership & Venture Compatibility
    IF NEW.project_id IS NOT NULL THEN
        SELECT venture_id INTO proj_venture_id FROM public.projects WHERE id = NEW.project_id AND user_id = NEW.user_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Task project must belong to the same user.' USING ERRCODE = 'P0001';
        END IF;
        IF NEW.venture_id IS NOT NULL AND proj_venture_id IS NOT NULL AND NEW.venture_id <> proj_venture_id THEN
            RAISE EXCEPTION 'Task venture and project venture must be logically compatible.' USING ERRCODE = 'P0001';
        END IF;
    END IF;

    -- Validate Person Ownership
    IF NEW.person_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.people WHERE id = NEW.person_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Task cannot reference another users person.' USING ERRCODE = 'P0001';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_task_relationships ON public.tasks;
CREATE TRIGGER trg_validate_task_relationships
    BEFORE INSERT OR UPDATE OF venture_id, project_id, person_id, user_id ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.validate_task_relationships();


-- 3. Validate Person to Organization Ownership
CREATE OR REPLACE FUNCTION public.validate_person_organization_ownership()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    IF NEW.organization_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.organizations WHERE id = NEW.organization_id AND user_id = NEW.user_id
    ) THEN
        RAISE EXCEPTION 'Person organization must belong to the same user.' USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_person_org ON public.people;
CREATE TRIGGER trg_validate_person_org
    BEFORE INSERT OR UPDATE OF organization_id, user_id ON public.people
    FOR EACH ROW EXECUTE FUNCTION public.validate_person_organization_ownership();


-- 4. Validate Memory Links Ownership
CREATE OR REPLACE FUNCTION public.validate_memory_links()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.memories WHERE id = NEW.memory_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Memory must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    IF TG_TABLE_NAME = 'memory_people' AND NOT EXISTS (SELECT 1 FROM public.people WHERE id = NEW.person_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Memory linked person must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    IF TG_TABLE_NAME = 'memory_projects' AND NOT EXISTS (SELECT 1 FROM public.projects WHERE id = NEW.project_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Memory linked project must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    IF TG_TABLE_NAME = 'memory_ventures' AND NOT EXISTS (SELECT 1 FROM public.ventures WHERE id = NEW.venture_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Memory linked venture must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_memory_people ON public.memory_people;
CREATE TRIGGER trg_validate_memory_people
    BEFORE INSERT OR UPDATE ON public.memory_people
    FOR EACH ROW EXECUTE FUNCTION public.validate_memory_links();

DROP TRIGGER IF EXISTS trg_validate_memory_projects ON public.memory_projects;
CREATE TRIGGER trg_validate_memory_projects
    BEFORE INSERT OR UPDATE ON public.memory_projects
    FOR EACH ROW EXECUTE FUNCTION public.validate_memory_links();

DROP TRIGGER IF EXISTS trg_validate_memory_ventures ON public.memory_ventures;
CREATE TRIGGER trg_validate_memory_ventures
    BEFORE INSERT OR UPDATE ON public.memory_ventures
    FOR EACH ROW EXECUTE FUNCTION public.validate_memory_links();


-- 5. Validate Document Links & Chunks Ownership
CREATE OR REPLACE FUNCTION public.validate_document_links()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.documents WHERE id = NEW.document_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Document must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_document_links ON public.document_links;
CREATE TRIGGER trg_validate_document_links
    BEFORE INSERT OR UPDATE ON public.document_links
    FOR EACH ROW EXECUTE FUNCTION public.validate_document_links();

DROP TRIGGER IF EXISTS trg_validate_document_chunks ON public.document_chunks;
CREATE TRIGGER trg_validate_document_chunks
    BEFORE INSERT OR UPDATE ON public.document_chunks
    FOR EACH ROW EXECUTE FUNCTION public.validate_document_links();


-- 6. Validate Interaction Participants Ownership
CREATE OR REPLACE FUNCTION public.validate_interaction_participants()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.interactions WHERE id = NEW.interaction_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Interaction must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.people WHERE id = NEW.person_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Participant person must belong to the user.' USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_interaction_participants ON public.interaction_participants;
CREATE TRIGGER trg_validate_interaction_participants
    BEFORE INSERT OR UPDATE ON public.interaction_participants
    FOR EACH ROW EXECUTE FUNCTION public.validate_interaction_participants();
