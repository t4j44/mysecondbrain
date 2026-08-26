import { defineConfig, devices } from '@playwright/test';
import {
  AUTH_STATE_PATH,
  getPrimaryE2EUser,
  hasSupabasePublicConfig,
} from './e2e/helpers/credentials';

const hasAuth = Boolean(getPrimaryE2EUser());
const canBootWeb = hasSupabasePublicConfig();

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 2,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: canBootWeb
    ? {
        command: 'pnpm exec next dev --port 3000',
        url: 'http://localhost:3000',
        // Cursor/agent shells often set CI=1 while a local Next server already occupies 3000.
        reuseExistingServer: process.env.PLAYWRIGHT_FORCE_WEBSERVER !== '1',
        timeout: 120_000,
      }
    : undefined,
  projects: [
    ...(hasAuth
      ? [
          {
            name: 'setup',
            testMatch: /auth\.setup\.ts/,
          },
        ]
      : []),
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
      testMatch: /core-lifecycle\.spec\.ts|negative\.authenticated\.spec\.ts|cross-tenant\.spec\.ts/,
      dependencies: hasAuth ? ['setup'] : [],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
        ...(hasAuth ? { storageState: AUTH_STATE_PATH } : {}),
      },
    },
    {
      name: 'mobile-chrome',
      testMatch: /core-lifecycle\.spec\.ts|negative\.authenticated\.spec\.ts/,
      use: {
        ...devices['Pixel 5'],
        ...(hasAuth ? { storageState: AUTH_STATE_PATH } : {}),
      },
      dependencies: hasAuth ? ['setup'] : [],
    },
  ],
});
