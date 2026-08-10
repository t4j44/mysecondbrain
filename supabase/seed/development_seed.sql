-- ============================================================================
-- Seed File: development_seed.sql
-- Description: Development seed data for Taj's Second Brain local development
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- Notice: ALL RECORDS ARE DEVELOPMENT TEST DATA ONLY. NO REAL CREDENTIALS.
-- ============================================================================

-- 1. Create a deterministic development test user in auth.users (UUID: 11111111-1111-1111-1111-111111111111)
DO $$
DECLARE
    test_user_id UUID := '11111111-1111-1111-1111-111111111111';
BEGIN
    -- Insert test user if running in an environment where auth schema is accessible
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
        INSERT INTO auth.users (id, instance_id, email, encrypted_password, email_confirmed_at, raw_user_meta_data, created_at, updated_at, role, aud)
        VALUES (
            test_user_id,
            '00000000-0000-0000-0000-000000000000',
            'taj@dev.local',
            extensions.crypt('DevPassword123!', extensions.gen_salt('bf')),
            NOW(),
            '{"full_name": "Taj (Dev)", "display_name": "Taj", "current_mission": "Building Justor AI & Founder OS"}'::jsonb,
            NOW(),
            NOW(),
            'authenticated',
            'authenticated'
        )
        ON CONFLICT (id) DO NOTHING;
    END IF;

    -- Ensure profile exists (in case trigger did not run or testing outside auth context)
    INSERT INTO public.profiles (id, email, display_name, full_name, current_mission, onboarding_completed)
    VALUES (
        test_user_id,
        'taj@dev.local',
        'Taj',
        'Taj (Dev)',
        'Building Justor AI & Founder OS',
        true
    )
    ON CONFLICT (id) DO UPDATE SET current_mission = 'Building Justor AI & Founder OS';
END $$;

-- 2. Populate Ventures (Justor AI, Zqtion, IEXF, CMOOS, and Custom Projects)
DO $$
DECLARE
    u_id UUID := '11111111-1111-1111-1111-111111111111';
    v_justor UUID;
    v_zqtion UUID;
    p_yousuf UUID;
    proj_os UUID;
    m_meetup UUID;
    k_def UUID;
BEGIN
    -- Ventures
    INSERT INTO public.ventures (id, user_id, name, slug, vision, mission, status, current_priority)
    VALUES 
        (extensions.uuid_generate_v4(), u_id, 'Justor AI', 'justor-ai', 'Legal AI for everyone', 'Democratize legal workflow and accessibility', 'active', 10),
        (extensions.uuid_generate_v4(), u_id, 'Zqtion', 'zqtion', 'Next-gen intelligence suite', 'Build scalable autonomous tools', 'active', 8),
        (extensions.uuid_generate_v4(), u_id, 'IEXF', 'iexf', 'Global founder network & events', 'Unite elite execution founders', 'paused', 6),
        (extensions.uuid_generate_v4(), u_id, 'CMOOS', 'cmoos', 'Chief Marketing Officer Operating System', 'Automate generative branding methodologies', 'active', 7)
    ON CONFLICT (user_id, slug) DO UPDATE SET current_priority = EXCLUDED.current_priority
    RETURNING id INTO v_justor;

    SELECT id INTO v_zqtion FROM public.ventures WHERE user_id = u_id AND slug = 'zqtion' LIMIT 1;

    -- Projects
    INSERT INTO public.projects (id, user_id, venture_id, name, description, status, priority, progress)
    VALUES
        (extensions.uuid_generate_v4(), u_id, v_justor, 'MVP Contract Analyzer', 'Core LLM extraction engine for contract review', 'active', 5, 65),
        (extensions.uuid_generate_v4(), u_id, v_justor, 'Founder OS Web Application', 'Retro-futuristic interface for personal intelligence', 'active', 5, 40)
    RETURNING id INTO proj_os;

    -- CRM Organizations & People
    INSERT INTO public.organizations (user_id, name, industry, location, description)
    VALUES (u_id, 'Mangosteen Studio', 'Technology & Product Design', 'Dhaka', 'Elite product development and design studio')
    ON CONFLICT (user_id, name) DO NOTHING;

    INSERT INTO public.people (id, user_id, name, role, company, industry, location, email, relationship_type, relationship_strength, how_we_met, important_insights, tags)
    VALUES (
        extensions.uuid_generate_v4(), u_id, 'Yousuf Imran', 'Founder / Mentor', 'Mangosteen Studio', 'Tech', 'Dhaka', 'yousuf@dev.local', 'mentor', 9, 'Founder Meetup Dhaka', 
        ARRAY['Focus on customer retention', 'Keep MVP scope minimal and execution speed fast'], ARRAY['mentor', 'founder', 'design']
    )
    RETURNING id INTO p_yousuf;

    -- Tasks
    INSERT INTO public.tasks (user_id, venture_id, project_id, person_id, title, description, status, priority, due_date, estimated_effort)
    VALUES
        (u_id, v_justor, proj_os, NULL, 'Complete product roadmap', 'Finalize engineering milestones for Q3', 'in_progress', 'high', NOW() + interval '2 days', 120),
        (u_id, v_justor, NULL, p_yousuf, 'Follow up investor and mentor feedback', 'Send weekly update deck to Yousuf', 'todo', 'urgent', NOW() + interval '1 day', 45),
        (u_id, v_justor, NULL, NULL, 'Review user feedback from contract test', 'Synthesize onboarding call notes into Jira issues', 'todo', 'medium', NOW() + interval '4 days', 90);

    -- Meetings & Interactions
    INSERT INTO public.meetings (id, user_id, title, start_time, end_time, location, status, summary, action_items)
    VALUES (
        extensions.uuid_generate_v4(), u_id, 'Founder Meetup Dhaka Discussion', NOW() - interval '3 days', NOW() - interval '3 days' + interval '1 hour', 'Dhaka Coffee Studio', 'completed',
        'Discussed startup execution velocity and mental clarity for solo AI product founders.', ARRAY['Share Justor AI progress update', 'Implement feedback loop']
    )
    RETURNING id INTO m_meetup;

    INSERT INTO public.interactions (user_id, person_id, venture_id, meeting_id, interaction_type, title, summary, key_takeaways, next_actions)
    VALUES (
        u_id, p_yousuf, v_justor, m_meetup, 'meeting', 'Mentorship Session on AI Product Execution',
        'Deep dive into product-market fit metrics and reducing operational overhead.',
        ARRAY['Customer retention > initial hype', 'Build automated memory loops'], ARRAY['Send follow up deck by Friday']
    );

    -- Memories & Embeddings
    INSERT INTO public.memories (id, user_id, title, memory_type, body, summary, importance, visibility)
    VALUES (
        extensions.uuid_generate_v4(), u_id, 'Key bottleneck is execution speed', 'insight',
        'When operating multiple ventures like Justor AI and Zqtion, the only true differentiator is rapid iteration and automated knowledge capture. Do not let documentation stall deployment.',
        'Execution velocity over theoretical planning.', 9, 'private'
    );

    -- KPIs
    INSERT INTO public.kpis (user_id, category, metric_name, target_value, current_value, unit, period)
    VALUES 
        (u_id, 'founder', 'Projects Completed', 12, 8, 'count', 'yearly'),
        (u_id, 'founder', 'Users Acquired', 5000, 1500, 'count', 'quarterly'),
        (u_id, 'network', 'Meaningful Connections', 50, 42, 'count', 'monthly');

    INSERT INTO public.kpi_definitions (id, user_id, name, category, target_value, target_period, unit)
    VALUES (extensions.uuid_generate_v4(), u_id, 'Weekly Deep Work Hours', 'founder', 35, 'weekly', 'hours')
    RETURNING id INTO k_def;

    INSERT INTO public.kpi_entries (user_id, definition_id, entry_date, numeric_value, notes)
    VALUES (u_id, k_def, CURRENT_DATE, 38.5, 'Excellent focus during architecture and database implementation sprints.');

    -- AI Conversation Seed
    INSERT INTO public.ai_conversations (user_id, title, mode, provider, model)
    VALUES (u_id, 'Brainstorming Justor AI Go-to-Market', 'coach', 'gemini', 'gemini-3.1-pro');

END $$;
