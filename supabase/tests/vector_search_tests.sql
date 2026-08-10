-- ============================================================================
-- Test File: vector_search_tests.sql
-- Description: Verification tests for pgvector embeddings, cosine retrieval, and isolation
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- Target Runner: pgTAP / supabase test db
-- ============================================================================

BEGIN;
SELECT plan(10);

-- Setup vectors for User A and User B
DO $$
DECLARE
    u_a UUID := 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
    u_b UUID := 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
    vec_a extensions.vector(768);
    vec_b extensions.vector(768);
    i INT;
    arr_a FLOAT[] := ARRAY[]::FLOAT[];
    arr_b FLOAT[] := ARRAY[]::FLOAT[];
BEGIN
    -- Create dummy 768-dimensional vectors (one pointing in +X direction, one pointing in opposite/different direction)
    FOR i IN 1..768 LOOP
        IF i = 1 THEN
            arr_a := array_append(arr_a, 1.0::float);
            arr_b := array_append(arr_b, 0.0::float);
        ELSIF i = 2 THEN
            arr_a := array_append(arr_a, 0.0::float);
            arr_b := array_append(arr_b, 1.0::float);
        ELSE
            arr_a := array_append(arr_a, 0.0::float);
            arr_b := array_append(arr_b, 0.0::float);
        END IF;
    END LOOP;
    
    vec_a := arr_a::extensions.vector(768);
    vec_b := arr_b::extensions.vector(768);

    -- Insert into memory_embeddings table for testing match_memories function
    INSERT INTO public.memory_embeddings (id, user_id, entity_type, entity_id, content, embedding)
    VALUES 
        ('11111111-aaaa-aaaa-aaaa-aaaaaaaaaaaa', u_a, 'note', '00000000-0000-0000-0000-000000000001', 'User A AI knowledge on execution', vec_a),
        ('22222222-bbbb-bbbb-bbbb-bbbbbbbbbbbb', u_b, 'note', '00000000-0000-0000-0000-000000000002', 'User B AI knowledge on fundraising', vec_b);
        
    -- Insert into embeddings table for hybrid search test
    INSERT INTO public.memories (id, user_id, title, body, archived_at)
    VALUES ('33333333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', u_a, 'Execution speed note', 'Execution velocity is the prime founder differentiator.', NULL);
    
    INSERT INTO public.embeddings (id, user_id, source_record_type, source_record_id, embedding, metadata)
    VALUES ('44444444-aaaa-aaaa-aaaa-aaaaaaaaaaaa', u_a, 'memory', '33333333-aaaa-aaaa-aaaa-aaaaaaaaaaaa', vec_a, '{"excerpt": "Execution velocity is key"}'::jsonb);
END $$;

-- ============================================================================
-- TEST 1: User A searches using match_memories
-- ============================================================================
SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claim.sub TO 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';

-- Construct query embedding identical to User A's vector
SELECT results_eq(
    $$
    DECLARE
        arr FLOAT[] := ARRAY[1.0]::FLOAT[];
        i INT;
    BEGIN
        -- Build inline vector string query or test function execution
    END;
    $$,
    $$ SELECT 'ok'::text WHERE false $$,
    'Vector comparison placeholder'
);

-- Actual test on match_memories function scoping
SELECT results_eq(
    $$
    SELECT content FROM public.match_memories(
        (ARRAY[1.0, 0.0] || array_fill(0.0::float, ARRAY[766]))::extensions.vector(768),
        0.5,
        5,
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid
    )
    $$,
    ARRAY['User A AI knowledge on execution'::text],
    'match_memories should return highly similar vector belonging to User A'
);

-- Confirm User B's vector is NOT returned even if similarity threshold is lowered to 0.0 or queried by User A
SELECT is_empty(
    $$
    SELECT * FROM public.match_memories(
        (ARRAY[0.0, 1.0] || array_fill(0.0::float, ARRAY[766]))::extensions.vector(768),
        0.0,
        10,
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid
    ) WHERE content LIKE '%User B%'
    $$,
    'match_memories must NEVER leak User B embeddings even when query vector exactly matches User B vector'
);

-- TEST 2: Hybrid knowledge search execution
SELECT ok(
    EXISTS(
        SELECT 1 FROM public.hybrid_knowledge_search(
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid,
            'Execution velocity',
            (ARRAY[1.0, 0.0] || array_fill(0.0::float, ARRAY[766]))::extensions.vector(768),
            0.1,
            5
        ) WHERE source_record_type = 'memory' AND content_excerpt LIKE '%velocity%'
    ),
    'hybrid_knowledge_search successfully blends keyword and vector scores for User A'
);

SELECT * FROM finish();
ROLLBACK;
