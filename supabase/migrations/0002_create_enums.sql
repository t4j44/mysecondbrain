-- ============================================================================
-- Migration: 0002_create_enums.sql
-- Description: Implement state machine and categorization enums for stable domain values
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

DO $$
BEGIN
    -- Venture Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'venture_status') THEN
        CREATE TYPE venture_status AS ENUM ('active', 'paused', 'completed', 'archived', 'exited');
    END IF;

    -- Project Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
        CREATE TYPE project_status AS ENUM ('planned', 'active', 'blocked', 'paused', 'completed', 'archived', 'on_hold');
    END IF;

    -- Task Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
        CREATE TYPE task_status AS ENUM ('backlog', 'todo', 'in_progress', 'blocked', 'completed', 'cancelled', 'archived', 'done');
    END IF;

    -- Task Priority
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
        CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
    END IF;

    -- Idea Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'idea_status') THEN
        CREATE TYPE idea_status AS ENUM ('captured', 'draft', 'exploring', 'validating', 'prioritized', 'building', 'executing', 'paused', 'rejected', 'completed', 'archived');
    END IF;

    -- Interaction Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interaction_type') THEN
        CREATE TYPE interaction_type AS ENUM ('meeting', 'call', 'email', 'chat', 'event', 'note', 'social_touch');
    END IF;

    -- Relationship Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relationship_type') THEN
        CREATE TYPE relationship_type AS ENUM ('mentor', 'investor', 'peer', 'collaborator', 'lead', 'contact', 'customer', 'advisor', 'team');
    END IF;

    -- Meeting Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meeting_status') THEN
        CREATE TYPE meeting_status AS ENUM ('scheduled', 'in_progress', 'completed', 'cancelled', 'rescheduled');
    END IF;

    -- Document Processing Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_processing_status') THEN
        CREATE TYPE document_processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
    END IF;

    -- Content Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_status') THEN
        CREATE TYPE content_status AS ENUM ('draft', 'review', 'published', 'archived', 'scheduled');
    END IF;

    -- Integration Provider
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integration_provider') THEN
        CREATE TYPE integration_provider AS ENUM ('google_drive', 'google_calendar', 'gmail', 'github', 'linkedin', 'custom');
    END IF;

    -- Integration Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integration_status') THEN
        CREATE TYPE integration_status AS ENUM ('connected', 'disconnected', 'syncing', 'error', 'revoked');
    END IF;

    -- Sync Job Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sync_job_type') THEN
        CREATE TYPE sync_job_type AS ENUM ('calendar_sync', 'drive_backup', 'contacts_sync', 'export', 'incremental_backup');
    END IF;

    -- Sync Job Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sync_job_status') THEN
        CREATE TYPE sync_job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'retrying');
    END IF;

    -- Export Job Type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'export_job_type') THEN
        CREATE TYPE export_job_type AS ENUM ('markdown', 'json', 'full_archive', 'backup', 'portfolio');
    END IF;

    -- Export Job Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'export_job_status') THEN
        CREATE TYPE export_job_status AS ENUM ('queued', 'processing', 'completed', 'failed', 'expired');
    END IF;

    -- AI Message Role
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ai_message_role') THEN
        CREATE TYPE ai_message_role AS ENUM ('system', 'user', 'assistant', 'tool', 'function');
    END IF;

    -- AI Message Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ai_message_status') THEN
        CREATE TYPE ai_message_status AS ENUM ('pending', 'streaming', 'completed', 'error');
    END IF;

    -- Visibility Status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visibility_status') THEN
        CREATE TYPE visibility_status AS ENUM ('private', 'shared', 'public', 'unlisted');
    END IF;

    -- KPI Category
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'kpi_category') THEN
        CREATE TYPE kpi_category AS ENUM ('founder', 'network', 'learning', 'venture', 'personal');
    END IF;

    -- KPI Period
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'kpi_period') THEN
        CREATE TYPE kpi_period AS ENUM ('daily', 'weekly', 'monthly', 'quarterly', 'yearly');
    END IF;
END $$;
