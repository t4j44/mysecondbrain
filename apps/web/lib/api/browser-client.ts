'use client';

import { FastApiClient } from './client';
import { createClient } from '@/lib/supabase/client';

/**
 * Browser-side API client singleton instance
 * Automatically attaches current browser session JWT as Bearer authorization header
 */
export const api = new FastApiClient(async () => {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
});
