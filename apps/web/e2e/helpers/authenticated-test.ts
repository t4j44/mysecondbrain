import { test as base, expect } from '@playwright/test';
import { getPrimaryE2EUser } from './credentials';
import { loginViaUi } from './ui';

// A logout/refresh in one test must not invalidate another test's saved session.
// Every test receives its own empty context and signs in independently.
export const test = base.extend({
  storageState: async ({}, use) => {
    await use({ cookies: [], origins: [] });
  },
  page: async ({ page }, use) => {
    const user = getPrimaryE2EUser();
    if (!user) throw new Error('Authenticated staging test requires its synthetic account.');
    await loginViaUi(page, user);
    await use(page);
  },
});

export { expect };
