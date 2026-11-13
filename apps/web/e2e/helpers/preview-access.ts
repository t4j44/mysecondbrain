import type { Browser, BrowserContext, BrowserContextOptions } from '@playwright/test';

export const VERIFIED_PREVIEW_ORIGIN = 'https://second-brain-web-staging-enhhoxigx-thenadish-4808s-projects.vercel.app';
const configuredContexts = new WeakSet<BrowserContext>();
type PreviewEnvironment = Record<string, string | undefined>;

export function previewCredential(env: PreviewEnvironment = process.env) {
  const token = env.VERCEL_OIDC_TOKEN;
  const github = env.GITHUB_ACTIONS === 'true' && env.ACTIONS_ID_TOKEN_REQUEST_URL && env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
  if (!token && !github) return null;
  // A token must never be sent to an arbitrary CLI-supplied URL or a branch alias.
  if (env.PLAYWRIGHT_TEST_BASE_URL !== VERIFIED_PREVIEW_ORIGIN) {
    throw new Error('Protected preview target does not match the verified deployment.');
  }
  return { origin: VERIFIED_PREVIEW_ORIGIN, token, github: Boolean(github) };
}

export function tokenProvider(env: PreviewEnvironment) {
  let cached: { value: string; until: number } | undefined;
  let pending: Promise<string> | undefined;
  return async (): Promise<string> => {
    if (env.VERCEL_OIDC_TOKEN) return env.VERCEL_OIDC_TOKEN;
    if (cached && cached.until > Date.now()) return cached.value;
    if (!pending) pending = (async () => {
      try {
        const url = new URL(env.ACTIONS_ID_TOKEN_REQUEST_URL!);
        url.searchParams.set('audience', 'https://github.com/t4j44');
        const response = await fetch(url, { redirect: 'error', signal: AbortSignal.timeout(15_000),
          headers: { Authorization: `Bearer ${env.ACTIONS_ID_TOKEN_REQUEST_TOKEN}` } });
        if (!response.ok) throw new Error();
        const body = await response.json() as { value?: unknown };
        if (typeof body.value !== 'string' || !body.value) throw new Error();
        // Refresh throughout long suites; a one-time token expires mid-run.
        cached = { value: body.value, until: Date.now() + 60_000 };
        return body.value;
      } catch { throw new Error('Unable to obtain short-lived preview identity.'); }
    })();
    try { return await pending; } finally { pending = undefined; }
  };
}

export async function configurePreviewAccess(context: BrowserContext, env: PreviewEnvironment = process.env) {
  if (configuredContexts.has(context)) return;
  const credential = previewCredential(env);
  if (!credential) {
    if (env.PLAYWRIGHT_TEST_BASE_URL === VERIFIED_PREVIEW_ORIGIN) {
      throw new Error('Protected preview access requires a short-lived VERCEL_OIDC_TOKEN.');
    }
    return;
  }
  const getToken = tokenProvider(env);
  await context.route(url => url.origin === credential.origin, async route => {
    // route.continue({headers}) propagates headers across redirects. Fetch one
    // hop and fulfill instead: the browser follows redirects without our token.
    try {
      const response = await route.fetch({
        headers: { ...route.request().headers(), 'x-vercel-trusted-oidc-idp-token': await getToken() },
        maxRedirects: 0,
        timeout: 60_000,
      });
      try { await route.fulfill({ response }); } finally { await response.dispose(); }
    } catch {
      // Playwright's raw network error may include request headers. Never log it.
      await route.abort('failed');
    }
  });
  configuredContexts.add(context);
}

export async function newPreviewContext(browser: Browser, options: BrowserContextOptions = {}) {
  const context = await browser.newContext({
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000',
    serviceWorkers: 'block',
    ...options,
  });
  try { await configurePreviewAccess(context); } catch (error) {
    await context.close();
    throw error;
  }
  return context;
}
