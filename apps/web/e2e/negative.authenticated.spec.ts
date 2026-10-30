import { test, expect } from '@playwright/test';
import { getPrimaryE2EUser, hasSupabasePublicConfig } from './helpers/credentials';
import { uniqueId } from './helpers/ui';

const hasAuth = Boolean(getPrimaryE2EUser()) && hasSupabasePublicConfig();

test.describe('Authenticated negatives', () => {
  test.skip(
    !hasAuth,
    'CORE E2E BLOCKED: E2E_EMAIL/E2E_PASSWORD and/or NEXT_PUBLIC_SUPABASE_* are not set. Credentials and keys were not invented.'
  );

  test('invalid person id shows contact-not-found error UI', async ({ page }) => {
    await page.goto('/people/00000000-0000-0000-0000-000000000001');
    await expect(page.getByText('Contact not found')).toBeVisible();
    await expect(
      page.getByText(/record not found|unavailable|not found/i).first()
    ).toBeVisible();
    await expect(page.getByRole('button', { name: /retry operator protocol/i })).toBeVisible();
  });

  test('people create form requires a name', async ({ page }) => {
    await page.goto('/people/new');
    await page.getByRole('button', { name: 'Create Contact' }).click();
    const nameInput = page.locator('input[required]').first();
    const valid = await nameInput.evaluate((el) => (el as HTMLInputElement).checkValidity());
    expect(valid).toBe(false);
    await expect(page).toHaveURL(/\/people\/new/);
  });

  test('API 500 on ventures list surfaces error UI', async ({ page }) => {
    await page.route('**/api/v1/ventures**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'INTERNAL',
              message: 'QA injected server failure',
            },
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto('/ventures');
    await expect(page.getByText('OPERATIONAL COMMUNICATION FAILURE')).toBeVisible();
    await expect(page.getByText(/QA injected server failure|Server error \(500\)/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /retry operator protocol/i })).toBeVisible();
  });

  test('people search empty state for unmatched query', async ({ page }) => {
    const missing = uniqueId('zzz-no-such-person');
    await page.goto('/people');
    await page.getByTestId('people-search').fill(missing);
    await expect(page.getByText(/no matches|no contacts yet/i)).toBeVisible();
  });
});
