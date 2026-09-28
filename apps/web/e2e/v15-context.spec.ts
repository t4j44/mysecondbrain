import { createHash, randomBytes } from 'node:crypto';
import { test, expect } from '@playwright/test';
import { getPrimaryE2EUser, getSecondaryE2EUser, hasSupabasePublicConfig } from './helpers/credentials';
import { loginViaUi, uniqueId } from './helpers/ui';

test.describe('V1.5 personal context acceptance', () => {
  test.use({trace: 'off'}); // OAuth tokens and private media must not enter trace archives.
  test.skip(!getPrimaryE2EUser() || !hasSupabasePublicConfig(), 'Requires isolated staging and a synthetic test account.');

  test('card plus moment persists, explicit outreach outcome is retrievable, and another user is denied', async ({page, browser}) => {
    test.skip(!getSecondaryE2EUser(), 'Requires the second isolated staging account.');
    const name = uniqueId('SyntheticAhmed').replace(/-/g, '');
    await page.goto('/capture');
    const card = await page.evaluate((label) => {
      const canvas = document.createElement('canvas'); canvas.width = 1200; canvas.height = 700;
      const ctx = canvas.getContext('2d')!; ctx.fillStyle = 'white'; ctx.fillRect(0, 0, 1200, 700);
      ctx.fillStyle = 'black'; ctx.font = '48px Arial';
      [label, 'Synthetic Ventures', 'ahmed@example.com', '+880 1712 345678'].forEach((line, index) => ctx.fillText(line, 50, 100 + index * 100));
      return canvas.toDataURL('image/png').split(',')[1];
    }, name);
    await page.getByLabel('Read a business card').setInputFiles({name:'card.png', mimeType:'image/png', buffer:Buffer.from(card, 'base64')});
    await expect(page.getByText(/Text added\. Check names/)).toBeVisible({timeout:90000});
    await page.getByLabel('Add a moment photo').setInputFiles({name:'moment.png', mimeType:'image/png', buffer:Buffer.from(card, 'base64')});
    await expect(page.getByRole('img', {name:'Moment preview'})).toBeVisible();
    await page.getByLabel('Capture text').fill(`Met ${name} at AI Summit. We discussed Justor fundraising. Reconnect after paying customers. ahmed@example.com +8801712345678`);
    await page.getByRole('button', {name:'Review capture',exact:true}).click();
    await expect(page.getByRole('heading', {name:'Check before saving'})).toBeVisible();
    await page.getByLabel('Person', {exact:true}).fill(name);
    await page.getByLabel('Existing person', {exact:true}).selectOption('new');
    await page.getByLabel('Existing project', {exact:true}).fill('');
    await page.getByLabel('Existing venture', {exact:true}).fill('');
    await page.getByLabel('Phone with country code (+…)').fill('+8801712345678');
    await page.getByLabel('Commitment', {exact:true}).fill('Send synthetic fundraising update');
    await page.getByLabel('Who made the commitment?').selectOption('owed_by_me');
    await page.getByRole('button', {name:'Confirm and save'}).click();
    await expect(page.getByText('Saved. Your context', {exact:false})).toBeVisible();
    await page.getByRole('link', {name:'Open person',exact:true}).click();
    const profileUrl = page.url();
    await expect(page.getByRole('img', {name:'Saved business card'})).toBeVisible();
    await expect(page.getByRole('img', {name:'Saved moment'})).toBeVisible();
    await page.reload();
    await expect(page.getByRole('img', {name:'Saved moment'})).toBeVisible();
    const followup = page.getByRole('article').filter({has:page.getByRole('button', {name:'Draft message'})}).first();
    await followup.getByRole('button', {name:'Draft message'}).click();
    await followup.getByLabel('Follow-up draft').fill('Synthetic reviewed update; no real message will be sent.');
    await page.context().route('https://wa.me/**', route => route.fulfill({body:'Synthetic test: external messaging is not performed.'}));
    await followup.getByRole('button', {name:'Open WhatsApp'}).click();
    await expect(followup.getByText('Did you send it?')).toBeVisible();
    await expect(followup.getByRole('button', {name:'I sent it — record outcome'})).toBeDisabled();
    const outcome = `Synthetic user-confirmed outcome ${name}; no real send performed by this test.`;
    await followup.getByLabel('Outreach outcome').fill(outcome);
    await followup.getByRole('button', {name:'I sent it — record outcome'}).click();
    await expect(page.getByText(outcome, {exact:true}).first()).toBeVisible();
    await page.reload();
    await expect(page.getByText(outcome, {exact:true}).first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    const foreign = await browser.newContext();
    try {
      const other = await foreign.newPage(); await loginViaUi(other, getSecondaryE2EUser()!);
      const deniedProfile = other.waitForResponse(response => response.url().includes('/people/') && [403, 404].includes(response.status()));
      await other.goto(profileUrl);
      await deniedProfile;
      await expect(other.getByRole('img', {name:'Saved moment'})).toHaveCount(0);
      await expect(other.getByText(outcome, {exact:true})).toHaveCount(0);
    } finally { await foreign.close(); }
  });

  test('OAuth consent, scoped MCP read and revocation work through hosted HTTP', async ({page, request}) => {
    const origin = process.env.NEXT_PUBLIC_API_BASE_URL!.replace(/\/api\/v1\/?$/, '');
    const resource = origin + '/mcp';
    const callback = 'https://synthetic-client.invalid/callback';
    const registered = await request.post(origin + '/oauth/register', {data:{client_name:'Synthetic staging acceptance',
      redirect_uris:[callback], token_endpoint_auth_method:'none', grant_types:['authorization_code','refresh_token'], response_types:['code']}});
    expect(registered.status()).toBe(201);
    const client = await registered.json();
    const verifier = randomBytes(32).toString('base64url');
    const authorized = await request.get(origin + '/oauth/authorize', {maxRedirects:0, params:{
      client_id:client.client_id, redirect_uri:callback, response_type:'code', resource,
      code_challenge:createHash('sha256').update(verifier).digest('base64url'), code_challenge_method:'S256', state:'synthetic'}});
    expect(authorized.status()).toBe(302);
    await page.route(callback + '**', route => route.fulfill({body:'Synthetic OAuth return'}));
    await page.goto(authorized.headers().location);
    await page.getByRole('button', {name:'Approve selected access'}).click();
    await page.waitForURL(callback + '**');
    const code = new URL(page.url()).searchParams.get('code')!;
    const issued = await request.post(origin + '/oauth/token', {form:{client_id:client.client_id, code, code_verifier:verifier,
      grant_type:'authorization_code', redirect_uri:callback, resource}});
    expect(issued.status()).toBe(200);
    const token = await issued.json();
    const headers = {Authorization:'Bearer ' + token.access_token, Accept:'application/json, text/event-stream'};
    const rpc = {jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'get_projects',arguments:{limit:1}}};
    const retrieved = await request.post(resource, {headers,data:rpc});
    expect(retrieved.status()).toBe(200);
    const result = await retrieved.json();
    expect(result.error).toBeUndefined();
    expect(result.result.isError).not.toBe(true);
    expect((await request.post(origin + '/oauth/revoke', {form:{client_id:client.client_id,token:token.access_token}})).status()).toBe(200);
    expect((await request.post(resource, {headers,data:rpc})).status()).toBe(401);
  });
});
