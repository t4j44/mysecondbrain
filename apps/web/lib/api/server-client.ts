import { FastApiClient } from './client';
import { createClient } from '@/lib/supabase/server';

/**
 * Server-side API client generator
 * Safely reads session tokens from Next.js server HTTP-only cookies
 */
export function createServerApi(): FastApiClient {
  return new FastApiClient(async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  });
}
