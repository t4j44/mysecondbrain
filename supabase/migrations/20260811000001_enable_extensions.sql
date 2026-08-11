-- ============================================================================
-- Migration: 0001_enable_extensions.sql
-- Description: Enable required PostgreSQL extensions for Taj's Second Brain
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- Create extensions schema if not exists
CREATE SCHEMA IF NOT EXISTS extensions;
GRANT USAGE ON SCHEMA extensions TO public;

-- 1. pgcrypto: Required for cryptographic database support, random UUID generation, and hashing algorithms
CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA extensions;

-- 2. uuid-ossp: Required for standardized UUID generation (e.g. uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;

-- 3. vector (pgvector): Required for high-performance vector embedding storage and similarity search (RAG pipeline)
CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA extensions;

-- 4. citext: Required for case-insensitive text matching without needing redundant lower() calls (e.g. email, tags, organization names, slugs)
CREATE EXTENSION IF NOT EXISTS "citext" WITH SCHEMA extensions;

-- 5. pg_trgm: Required for trigram index generation to enable fast fuzzy keyword and similarity searches
CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA extensions;

