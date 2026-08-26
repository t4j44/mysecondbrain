import { test, expect } from '@playwright/test';
import { hasSupabasePublicConfig } from './helpers/credentials';

test.describe('Unauthenticated and public form negatives', () => {
  test.skip(
    !hasSupabasePublicConfig(),
    'CORE E2E BLOCKED: NEXT_PUBLIC_SUPABASE_URL and publishable/anon key are missing from local env. Next middleware cannot boot. Keys were not invented.'
  );
  test.use({ storageState: { cookies: [], origins: [] } });

  test('unauthenticated visitor is redirected from protected venture route to login', async ({
    page,
  }) => {
    await page.goto('/ventures');
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByLabel(/email address/i)).toBeVisible();
    await expect(page.getByLabel(/security passkey/i)).toBeVisible();
  });

  test('login form validation rejects invalid email', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email address/i).fill('not-an-email');
    await page.getByLabel(/security passkey/i).fill('x');
    await page.getByRole('button', { name: /initialize session/i }).click();
    await expect(page.getByText('Please enter a valid email address.')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page exposes email, password, and submit controls', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/Taj's Second Brain|Login/i);
    await expect(page.getByLabel(/email address/i)).toBeVisible();
    await expect(page.getByLabel(/security passkey/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /initialize session/i })).toBeVisible();
  });
});
