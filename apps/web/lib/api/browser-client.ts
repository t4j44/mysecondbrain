'use client';

import { FastApiClient } from './client';
import { createClient } from '@/lib/supabase/client';
import { env } from '@/lib/env';

/**
 * Browser-side API client singleton instance
 * Automatically attaches current browser session JWT as Bearer authorization header
 */
const sessionToken = async () => {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
};
export const api = new FastApiClient(sessionToken);
export const oauthApi = new FastApiClient(sessionToken, env.NEXT_PUBLIC_API_BASE_URL.replace(/\/api\/v1\/?$/, ''));
