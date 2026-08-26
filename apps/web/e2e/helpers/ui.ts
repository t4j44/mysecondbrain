import { expect, type Locator, type Page } from '@playwright/test';
import type { E2EUser } from './credentials';

export function uniqueId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export async function loginViaUi(page: Page, user: E2EUser): Promise<void> {
  await page.goto('/login');
  await expect(page.getByLabel(/email address/i)).toBeVisible();
  await page.getByLabel(/email address/i).fill(user.email);
  await page.getByLabel(/security passkey/i).fill(user.password);
  await page.getByRole('button', { name: /initialize session/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

export async function logoutViaUi(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'User account options' }).click();
  await page.getByRole('button', { name: /lock terminal \/\/ sign out/i }).click();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByLabel(/email address/i)).toBeVisible();
}

export function cardByName(page: Page, testId: string, name: string): Locator {
  return page.getByTestId(testId).filter({ hasText: name });
}

export async function confirmDestructive(page: Page, confirmName: RegExp | string): Promise<void> {
  const dialog = page.getByRole('alertdialog');
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: confirmName }).click();
  await expect(dialog).not.toBeVisible();
}
