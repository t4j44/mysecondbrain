-- ============================================================================
-- Migration: 0003_create_profiles_and_triggers.sql
-- Description: Create core profiles table and common timestamp triggers
-- Author: Agent 2 — Senior Supabase & PostgreSQL Engineer
-- ============================================================================

-- Reusable timestamp trigger function
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
ALTER FUNCTION public.set_updated_at() OWNER TO postgres;

-- Create User Profiles table connected to auth.users
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email extensions.citext NOT NULL UNIQUE,
    display_name TEXT,
    full_name TEXT,
    avatar_path TEXT,
    avatar_url TEXT,
    headline TEXT,
    bio TEXT,
    timezone TEXT DEFAULT 'UTC',
    locale TEXT DEFAULT 'en-US',
    current_mission TEXT,
    onboarding_completed BOOLEAN DEFAULT false,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger for profiles updated_at
DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Secure function to automatically create a profile upon signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, auth, extensions
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name, full_name, avatar_url, current_mission, onboarding_completed, created_at, updated_at)
    VALUES (
        NEW.id,
        COALESCE(NEW.email::extensions.citext, ('user_' || NEW.id || '@example.com')::extensions.citext),
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NULL),
        COALESCE(NEW.raw_user_meta_data->>'current_mission', 'Building my second brain'),
        false,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION public.handle_new_user() OWNER TO postgres;

-- Attach trigger to auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
