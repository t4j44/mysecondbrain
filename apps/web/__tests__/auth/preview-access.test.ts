// @vitest-environment node
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { BrowserContext } from '@playwright/test';
import { configurePreviewAccess, previewCredential, tokenProvider, VERIFIED_PREVIEW_ORIGIN } from '../../e2e/helpers/preview-access';

const env = { PLAYWRIGHT_TEST_BASE_URL: VERIFIED_PREVIEW_ORIGIN, VERCEL_OIDC_TOKEN: 'synthetic-preview-identity' };
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('preview credential containment', () => {
  it.each(['https://example.com', VERIFIED_PREVIEW_ORIGIN + '.attacker.invalid', VERIFIED_PREVIEW_ORIGIN + '/path', 'http://localhost:3000'])('rejects a token attached to an unverified target %s', target => {
    expect(() => previewCredential({ ...env, PLAYWRIGHT_TEST_BASE_URL: target })).toThrow(/verified deployment/);
  });
  it('requires credentials for the pinned hosted target but permits local testing without them', async () => {
    const context = { route: vi.fn() } as unknown as BrowserContext;
    await expect(configurePreviewAccess(context, { PLAYWRIGHT_TEST_BASE_URL: VERIFIED_PREVIEW_ORIGIN })).rejects.toThrow(/short-lived/);
    await configurePreviewAccess(context, {});
    expect(context.route).not.toHaveBeenCalled();
  });
  it('scopes the header to the immutable origin and never follows redirects with it', async () => {
    const context = { route: vi.fn() } as unknown as BrowserContext;
    await configurePreviewAccess(context, env);
    const [matches, handler] = vi.mocked(context.route).mock.calls[0] as unknown as [(url: URL) => boolean, (route: unknown) => Promise<void>];
    expect(matches(new URL(VERIFIED_PREVIEW_ORIGIN + '/login'))).toBe(true);
    for (const url of ['https://rpkjmdrralzxhdsgceal.supabase.co/auth/v1/token', 'https://second-brain-api-staging.onrender.com/api/v1/me', VERIFIED_PREVIEW_ORIGIN + '.attacker.invalid', 'https://external.invalid']) expect(matches(new URL(url))).toBe(false);
    const response = { dispose: vi.fn() };
    const route = { request: () => ({ headers: () => ({ accept: 'text/html' }) }), fetch: vi.fn().mockResolvedValue(response), fulfill: vi.fn(), abort: vi.fn() };
    await handler(route);
    expect(route.fetch).toHaveBeenCalledWith(expect.objectContaining({ maxRedirects: 0, headers: { accept: 'text/html', 'x-vercel-trusted-oidc-idp-token': env.VERCEL_OIDC_TOKEN } }));
    expect(route.fulfill).toHaveBeenCalledWith({ response });
    expect(response.dispose).toHaveBeenCalled();
    await configurePreviewAccess(context, env);
    expect(context.route).toHaveBeenCalledTimes(1);
  });
  it('aborts a network failure without propagating an error containing headers', async () => {
    const context = { route: vi.fn() } as unknown as BrowserContext;
    await configurePreviewAccess(context, env);
    const handler = vi.mocked(context.route).mock.calls[0][1] as (route: unknown) => Promise<void>;
    const route = { request: () => ({ headers: () => ({}) }), fetch: vi.fn().mockRejectedValue(new Error(env.VERCEL_OIDC_TOKEN)), abort: vi.fn() };
    await expect(handler(route)).resolves.toBeUndefined();
    expect(route.abort).toHaveBeenCalledWith('failed');
  });
  it('refreshes GitHub identity during long suites and does not follow identity-endpoint redirects', async () => {
    vi.useFakeTimers();
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ value: 'synthetic-short-lived' }) });
    vi.stubGlobal('fetch', fetch);
    const getToken = tokenProvider({ ACTIONS_ID_TOKEN_REQUEST_URL: 'https://issuer.invalid/token?scope=test', ACTIONS_ID_TOKEN_REQUEST_TOKEN: 'synthetic-runner-credential' });
    await Promise.all([getToken(), getToken()]);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith(new URL('https://issuer.invalid/token?scope=test&audience=https%3A%2F%2Fgithub.com%2Ft4j44'), expect.objectContaining({ redirect: 'error' }));
    vi.advanceTimersByTime(61_000);
    await getToken();
    expect(fetch).toHaveBeenCalledTimes(2);
  });
  it('sanitizes issuer errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('synthetic-private-header')));
    await expect(tokenProvider({ ACTIONS_ID_TOKEN_REQUEST_URL: 'https://issuer.invalid/token' })()).rejects.toThrow('Unable to obtain short-lived preview identity.');
  });
});
