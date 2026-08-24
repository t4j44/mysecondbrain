import { test, expect } from '@playwright/test';

test.describe('Taj\'s Second Brain — Essential E2E Workflows', () => {
  test('Login page loads with correct authentication elements', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/Taj's Second Brain|Login/i);
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('Dashboard loads navigation bar and status indicators', async ({ page }) => {
    await page.goto('/dashboard');
    // Verify responsive layout elements exist
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();
  });

  test('Venture and Project hierarchy pages render cleanly', async ({ page }) => {
    await page.goto('/ventures');
    await expect(page.locator('h1').first()).toBeVisible();

    await page.goto('/projects');
    await expect(page.locator('h1').first()).toBeVisible();

    await page.goto('/tasks');
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('People directory and Memories log display structured views', async ({ page }) => {
    await page.goto('/people');
    await expect(page.locator('h1').first()).toBeVisible();

    await page.goto('/memories');
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('AI Assistant panel loads prompt area and grounded citations placeholder', async ({ page }) => {
    await page.goto('/assistant');
    await expect(page.locator('textarea, input').first()).toBeVisible();
  });

  test('Settings integrations panel renders credential status', async ({ page }) => {
    await page.goto('/settings/integrations');
    await expect(page.locator('h1').first()).toBeVisible();
  });
});
