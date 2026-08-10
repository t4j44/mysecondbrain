-- ============================================================================
-- Test File: schema_tests.sql
-- Description: Schema verification tests for tables, constraints, enums, triggers
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- Target Runner: pgTAP / supabase test db
-- ============================================================================

BEGIN;

-- Load pgTAP if available in test environment
SELECT plan(25);

-- 1. Verify Extension installation
SELECT has_extension('uuid-ossp', 'Extension uuid-ossp should be enabled');
SELECT has_extension('vector', 'Extension pgvector should be enabled');
SELECT has_extension('citext', 'Extension citext should be enabled');
SELECT has_extension('pg_trgm', 'Extension pg_trgm should be enabled');

-- 2. Verify Core Domain Tables exist in public schema
SELECT has_table('public', 'profiles', 'profiles table should exist');
SELECT has_table('public', 'ventures', 'ventures table should exist');
SELECT has_table('public', 'projects', 'projects table should exist');
SELECT has_table('public', 'tasks', 'tasks table should exist');
SELECT has_table('public', 'people', 'people CRM table should exist');
SELECT has_table('public', 'interactions', 'interactions table should exist');
SELECT has_table('public', 'memories', 'memories table should exist');
SELECT has_table('public', 'documents', 'documents table should exist');
SELECT has_table('public', 'embeddings', 'embeddings vector table should exist');
SELECT has_table('public', 'memory_embeddings', 'memory_embeddings table should exist');
SELECT has_table('public', 'audit_logs', 'audit_logs table should exist');

-- 3. Verify Primary Keys and User Ownership Foreign Keys
SELECT col_is_pk('public', 'ventures', ARRAY['id'], 'ventures table should have id primary key');
SELECT has_fk('public', 'ventures', 'user_id', 'ventures must reference auth.users');
SELECT has_fk('public', 'tasks', 'user_id', 'tasks must reference auth.users');
SELECT has_fk('public', 'embeddings', 'user_id', 'embeddings must reference auth.users');

-- 4. Verify Unique Constraints
SELECT has_unique('public', 'ventures', 'uq_ventures_user_slug', 'Ventures must have unique user_id + slug');
SELECT has_unique('public', 'organizations', 'uq_organizations_user_name', 'Organizations must have unique user_id + name');

-- 5. Verify Timestamp and Completion Triggers
SELECT has_trigger('public', 'tasks', 'trg_tasks_updated_at', 'Tasks should have set_updated_at trigger');
SELECT has_trigger('public', 'tasks', 'trg_handle_task_completion', 'Tasks should have auto completion timestamp trigger');
SELECT has_trigger('public', 'projects', 'trg_validate_project_venture', 'Projects should have cross-user ownership validation trigger');

-- 6. Verify Search Functions exist
SELECT has_function('public', 'match_memories', 'match_memories function must exist for v1 contract');
SELECT has_function('public', 'hybrid_knowledge_search', 'hybrid_knowledge_search function must exist');

SELECT * FROM finish();
ROLLBACK;
