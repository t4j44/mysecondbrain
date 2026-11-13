import { test as base, expect } from '../fixtures';
import { getPrimaryE2EUser } from './credentials';
import { loginViaUi } from './ui';

// A logout or token refresh in one test must not revoke another test's session.
// Reuse #39's isolated-login approach, without persisting browser state to disk.
export const test = base.extend({
  storageState: async ({}, use) => { await use({ cookies: [], origins: [] }); },
  page: async ({ page }, use) => {
    const user = getPrimaryE2EUser();
    if (!user) throw new Error('Authenticated staging test requires its synthetic account.');
    await loginViaUi(page, user);
    await use(page);
  },
});
export { expect };
