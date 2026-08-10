-- ============================================================================
-- Migration: 0016_create_search_functions.sql
-- Description: Implement user-scoped semantic, keyword, and hybrid search SQL functions
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- 1. Match Memories (Strict alignment with database_schema.md v1.0 contract)
CREATE OR REPLACE FUNCTION public.match_memories(
    query_embedding extensions.vector(768),
    match_threshold float,
    match_count int,
    p_user_id uuid
)
RETURNS TABLE (
    id uuid,
    entity_type text,
    entity_id uuid,
    content text,
    similarity float,
    metadata jsonb
)
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, extensions
AS $$
BEGIN
    RETURN QUERY
    SELECT
        me.id,
        me.entity_type,
        me.entity_id,
        me.content,
        1 - (me.embedding <=> query_embedding) AS similarity,
        me.metadata
    FROM public.memory_embeddings me
    WHERE me.user_id = p_user_id
      AND 1 - (me.embedding <=> query_embedding) > match_threshold
    ORDER BY me.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- 2. Search People CRM by Text (Fuzzy keyword on name, company, role, notes)
CREATE OR REPLACE FUNCTION public.search_people_by_text(
    p_user_id uuid,
    search_query text,
    relationship_filter text DEFAULT NULL,
    limit_val int DEFAULT 20,
    offset_val int DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    name text,
    role text,
    company text,
    relationship_type text,
    relevance_score float,
    last_interaction_at timestamptz
)
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, extensions
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.role,
        p.company,
        p.relationship_type::text,
        GREATEST(
            extensions.similarity(p.name, search_query),
            extensions.similarity(COALESCE(p.company, ''), search_query),
            extensions.similarity(COALESCE(p.notes, ''), search_query)
        )::float AS relevance_score,
        p.last_interaction_at
    FROM public.people p
    WHERE p.user_id = p_user_id
      AND p.archived_at IS NULL
      AND (relationship_filter IS NULL OR p.relationship_type::text = relationship_filter)
      AND (
          p.name ILIKE '%' || search_query || '%' OR
          COALESCE(p.company, '') ILIKE '%' || search_query || '%' OR
          COALESCE(p.notes, '') ILIKE '%' || search_query || '%' OR
          search_query = ANY(p.tags)
      )
    ORDER BY relevance_score DESC, p.last_interaction_at DESC NULLS LAST
    LIMIT limit_val OFFSET offset_val;
END;
$$;


-- 3. Search Tasks by Text & Status
CREATE OR REPLACE FUNCTION public.search_tasks_by_text(
    p_user_id uuid,
    search_query text,
    status_filter text DEFAULT NULL,
    priority_filter text DEFAULT NULL,
    limit_val int DEFAULT 20
)
RETURNS TABLE (
    id uuid,
    title text,
    status text,
    priority text,
    due_date timestamptz,
    relevance_score float
)
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, extensions
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.title,
        t.status::text,
        t.priority::text,
        t.due_date,
        extensions.similarity(t.title, search_query)::float AS relevance_score
    FROM public.tasks t
    WHERE t.user_id = p_user_id
      AND t.archived_at IS NULL
      AND (status_filter IS NULL OR t.status::text = status_filter)
      AND (priority_filter IS NULL OR t.priority::text = priority_filter)
      AND (t.title ILIKE '%' || search_query || '%' OR COALESCE(t.description, '') ILIKE '%' || search_query || '%')
    ORDER BY relevance_score DESC, t.due_date ASC NULLS LAST
    LIMIT limit_val;
END;
$$;


-- 4. Match Document Chunks (pgvector cosine similarity for uploaded files)
CREATE OR REPLACE FUNCTION public.match_document_chunks(
    p_user_id uuid,
    query_embedding extensions.vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    chunk_id uuid,
    document_id uuid,
    document_title text,
    chunk_index int,
    chunk_text text,
    similarity float
)
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, extensions
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id AS chunk_id,
        dc.document_id,
        d.title AS document_title,
        dc.chunk_index,
        dc.chunk_text,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM public.embeddings e
    JOIN public.document_chunks dc ON dc.id = e.document_chunk_id
    JOIN public.documents d ON d.id = dc.document_id
    WHERE e.user_id = p_user_id
      AND e.source_record_type = 'document_chunk'
      AND d.archived_at IS NULL
      AND 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- 5. Hybrid Knowledge Search (Combined pg_trgm keyword & pgvector cosine similarity)
CREATE OR REPLACE FUNCTION public.hybrid_knowledge_search(
    p_user_id uuid,
    query_text text,
    query_embedding extensions.vector(768),
    match_threshold float DEFAULT 0.4,
    top_k int DEFAULT 10
)
RETURNS TABLE (
    source_record_type text,
    source_record_id uuid,
    content_excerpt text,
    semantic_score float,
    keyword_score float,
    combined_score float,
    metadata jsonb
)
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, extensions
AS $$
BEGIN
    RETURN QUERY
    WITH semantic_matches AS (
        SELECT
            e.source_record_type,
            e.source_record_id,
            e.metadata->>'excerpt' AS excerpt,
            1 - (e.embedding <=> query_embedding) AS s_score,
            e.metadata
        FROM public.embeddings e
        WHERE e.user_id = p_user_id
          AND 1 - (e.embedding <=> query_embedding) > match_threshold
    ),
    keyword_matches AS (
        SELECT
            'memory'::text AS type_lbl,
            m.id AS rec_id,
            m.body AS excerpt,
            extensions.similarity(m.body, query_text)::float AS k_score
        FROM public.memories m
        WHERE m.user_id = p_user_id AND m.archived_at IS NULL AND m.body ILIKE '%' || query_text || '%'
        UNION ALL
        SELECT
            'interaction'::text AS type_lbl,
            i.id AS rec_id,
            COALESCE(i.summary, i.detailed_notes, i.title) AS excerpt,
            extensions.similarity(COALESCE(i.summary, i.title), query_text)::float AS k_score
        FROM public.interactions i
        WHERE i.user_id = p_user_id AND (i.title ILIKE '%' || query_text || '%' OR COALESCE(i.summary, '') ILIKE '%' || query_text || '%')
    )
    SELECT
        COALESCE(sm.source_record_type, km.type_lbl) AS source_record_type,
        COALESCE(sm.source_record_id, km.rec_id) AS source_record_id,
        COALESCE(sm.excerpt, km.excerpt) AS content_excerpt,
        COALESCE(sm.s_score, 0.0)::float AS semantic_score,
        COALESCE(km.k_score, 0.0)::float AS keyword_score,
        ((COALESCE(sm.s_score, 0.0) * 0.7) + (COALESCE(km.k_score, 0.0) * 0.3))::float AS combined_score,
        COALESCE(sm.metadata, '{}'::jsonb) AS metadata
    FROM semantic_matches sm
    FULL OUTER JOIN keyword_matches km
      ON sm.source_record_type = km.type_lbl AND sm.source_record_id = km.rec_id
    ORDER BY ((COALESCE(sm.s_score, 0.0) * 0.7) + (COALESCE(km.k_score, 0.0) * 0.3)) DESC
    LIMIT top_k;
END;
$$;
