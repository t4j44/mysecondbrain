import fs from 'fs';
import path from 'path';
import { test as setup, expect } from '@playwright/test';
import { AUTH_STATE_PATH, getPrimaryE2EUser } from './helpers/credentials';
import { loginViaUi } from './helpers/ui';

setup('authenticate primary operator', async ({ page }) => {
  const user = getPrimaryE2EUser();
  setup.skip(
    !user,
    'CORE E2E BLOCKED: E2E_EMAIL and E2E_PASSWORD are not set. Credentials were not invented.'
  );
  if (!user) return;

  fs.mkdirSync(path.dirname(AUTH_STATE_PATH), { recursive: true });
  await loginViaUi(page, user);
  await expect(page.getByRole('button', { name: 'User account options' })).toBeVisible();
  await page.context().storageState({ path: AUTH_STATE_PATH });
});
