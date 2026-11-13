// @vitest-environment node
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import preflight from '../../e2e/hosted-preflight';
import { VERIFIED_PREVIEW_ORIGIN } from '../../e2e/helpers/preview-access';
beforeEach(() => {
  for (const [key, value] of Object.entries({ PLAYWRIGHT_TEST_BASE_URL: VERIFIED_PREVIEW_ORIGIN,
    VERCEL_OIDC_TOKEN: 'synthetic-only', NEXT_PUBLIC_API_BASE_URL: 'https://second-brain-api-staging.onrender.com/api/v1',
    NEXT_PUBLIC_SUPABASE_URL: 'https://rpkjmdrralzxhdsgceal.supabase.co', E2E_EMAIL: 'a@example.invalid',
    E2E_EMAIL_B: 'b@example.invalid', E2E_PASSWORD: 'synthetic-a', E2E_PASSWORD_B: 'synthetic-b' })) vi.stubEnv(key, value);
});
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
it.each([['E2E_EMAIL_B', ' A@example.invalid '], ['NEXT_PUBLIC_API_BASE_URL', 'https://other.invalid'], ['E2E_PASSWORD_B', '']])('blocks unsafe setting %s before network requests', async (key, value) => {
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch); vi.stubEnv(key, value);
  await expect(preflight()).rejects.toThrow('pinned staging services and two distinct');
  expect(fetch).not.toHaveBeenCalled();
});
it('reports a sanitized protection failure before any test fixtures run', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('synthetic-secret-do-not-report')));
  await expect(preflight()).rejects.toThrow('Protected application login preflight failed');
});
