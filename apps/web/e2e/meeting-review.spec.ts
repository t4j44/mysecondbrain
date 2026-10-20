import { test, expect } from '@playwright/test';
import { createClient } from '@supabase/supabase-js';
import { getPrimaryE2EUser, getSecondaryE2EUser } from './helpers/credentials';

// Synthetic accounts only. Never retain OAuth/JWTs in browser traces.
test.use({ trace: 'off' });
test('owner notes/export persist and user B is denied on real isolated staging', async ({ page, request }) => {
  const owner = getPrimaryE2EUser(); const other = getSecondaryE2EUser();
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  const stagingRef = process.env.BETA_SUPABASE_PROJECT_REF;
  const productionRef = process.env.PRODUCTION_SUPABASE_PROJECT_REF;
  if (!owner || !other || !supabaseUrl || !key || !base || !stagingRef || !productionRef || stagingRef === productionRef || new URL(supabaseUrl).hostname !== `${stagingRef}.supabase.co`) throw new Error('BLOCKED: isolated staging identity and two synthetic users are required.');
  const login = async (credentials: { email: string; password: string }) => {
    const client = createClient(supabaseUrl, key, { auth: { persistSession: false, autoRefreshToken: false } });
    const result = await client.auth.signInWithPassword(credentials);
    if (result.error || !result.data.session) throw new Error('Staging synthetic account sign-in failed.');
    return { Authorization: `Bearer ${result.data.session.access_token}` };
  };
  const headers = await login(owner); const foreign = await login(other);
  const created = await request.post(`${base}/meetings/captures`, { headers, data: { request_id: crypto.randomUUID(), title: 'Synthetic staging meeting notes', meeting_date: new Date().toISOString(), timezone: 'Asia/Dhaka', recording_permission: true, provider_terms_accepted: true, non_sensitive_recording: true } });
  expect(created.status()).toBe(201);
  const meeting = await created.json(); const path = `${base}/meetings/${meeting.id}`;
  try {
    await page.goto(`/meetings/${meeting.id}`);
    await expect(page.getByRole('heading', { name: 'Synthetic staging meeting notes', exact: true })).toBeVisible();
    await page.getByLabel('Meeting notes').fill('# Synthetic owner notes\nNo real meeting or provider inference is represented.');
    await page.getByRole('button', { name: 'Save notes', exact: true }).click();
    await expect(page.getByText('Notes saved.', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByLabel('Meeting notes')).toHaveValue('# Synthetic owner notes\nNo real meeting or provider inference is represented.');
    const exported = await request.get(`${path}/export/markdown?kind=notes`, { headers });
    expect(exported.status()).toBe(200); expect(await exported.text()).toContain('Synthetic owner notes');
    expect(exported.headers()['cache-control']).toBe('no-store');
    expect((await request.put(`${path}/notes`, { headers, data: { expected_version: 0, markdown: 'Stale write' } })).status()).toBe(409);
    for (const suffix of ['', '/notes', '/export/markdown', '/recording']) {
      expect((await request.get(path + suffix, { headers: foreign })).status()).toBe(404);
      expect((await request.get(path + suffix)).status()).toBe(401);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  } finally {
    expect((await request.delete(path, { headers })).status()).toBe(204);
    expect((await request.get(path + '/notes', { headers })).status()).toBe(404);
  }
});
