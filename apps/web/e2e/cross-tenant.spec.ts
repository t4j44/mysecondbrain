import { test, expect } from '@playwright/test';
import { getPrimaryE2EUser, getSecondaryE2EUser, hasSupabasePublicConfig } from './helpers/credentials';
import { cardByName, loginViaUi, uniqueId } from './helpers/ui';

const userA = getPrimaryE2EUser();
const userB = getSecondaryE2EUser();

test.describe('Cross-tenant isolation', () => {
  test.skip(
    !userA || !userB || !hasSupabasePublicConfig(),
    'CROSS-TENANT BLOCKED: E2E_EMAIL_B/E2E_PASSWORD_B and/or NEXT_PUBLIC_SUPABASE_* are not set. A second operator was not invented.'
  );

  test('User B cannot see User A venture', async ({ browser }) => {
    if (!userA || !userB) return;

    const ventureName = uniqueId('QA-Tenant-A-Venture');

    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    await loginViaUi(pageA, userA);
    await pageA.goto('/ventures');
    await pageA.getByTestId('venture-create').click();
    await pageA.getByPlaceholder('Venture name *').fill(ventureName);
    await pageA.getByRole('button', { name: 'Create Venture' }).click();
    await expect(cardByName(pageA, 'venture-card', ventureName)).toBeVisible();
    await contextA.close();

    const contextB = await browser.newContext({ storageState: undefined });
    const pageB = await contextB.newPage();
    await loginViaUi(pageB, userB);
    await pageB.goto('/ventures');
    await expect(cardByName(pageB, 'venture-card', ventureName)).toHaveCount(0);
    await contextB.close();
  });
});
