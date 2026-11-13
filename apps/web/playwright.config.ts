import { defineConfig, devices } from '@playwright/test';
import {
  hasSupabasePublicConfig,
} from './e2e/helpers/credentials';

const canBootWeb = hasSupabasePublicConfig();
const hostedRun = Boolean(process.env.PLAYWRIGHT_TEST_BASE_URL);

export default defineConfig({
  globalSetup: hostedRun ? './e2e/hosted-preflight.ts' : undefined,
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: hostedRun ? 0 : process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 2,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: hostedRun ? [['./e2e/safe-reporter.ts']] : [['list'], ['html', { open: 'never' }], ['junit', { outputFile: 'test-results/e2e-results.xml' }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000',
    trace: hostedRun ? 'off' : 'retain-on-failure',
    screenshot: hostedRun ? 'off' : 'only-on-failure',
    video: 'off',
    serviceWorkers: 'block',
  },
  webServer: canBootWeb && !process.env.PLAYWRIGHT_TEST_BASE_URL
    ? {
        command: 'pnpm exec next dev --port 3000',
        url: 'http://localhost:3000',
        // Cursor/agent shells often set CI=1 while a local Next server already occupies 3000.
        reuseExistingServer: process.env.PLAYWRIGHT_FORCE_WEBSERVER !== '1',
        timeout: 120_000,
      }
    : undefined,
  projects: [
    {
      name: 'unauthenticated',
      testMatch: /unauthenticated\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
        storageState: { cookies: [], origins: [] },
      },
    },
    {
      name: 'chromium',
      testMatch: /meeting-review\.spec\.ts|v15-context\.spec\.ts|beta-journey\.spec\.ts|core-lifecycle\.spec\.ts|negative\.authenticated\.spec\.ts|cross-tenant\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
      },
    },
    {
      name: 'mobile-chrome',
      testMatch: /meeting-review\.spec\.ts|v15-context\.spec\.ts|beta-journey\.spec\.ts|core-lifecycle\.spec\.ts|negative\.authenticated\.spec\.ts/,
      use: {
        ...devices['Pixel 5'],
      },
    },
  ],
});
