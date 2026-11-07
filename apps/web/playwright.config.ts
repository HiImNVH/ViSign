// apps/web/playwright.config.ts
// Cau hinh Playwright voi camera gia lap cho E2E va accessibility test.
import { defineConfig } from '@playwright/test';

const devServerUrl = 'http://127.0.0.1:5173';

export default defineConfig({
  testDir: './tests',
  testMatch: ['browser/**/*.spec.ts', 'accessibility/**/*.spec.ts'],
  workers: 1,
  use: {
    baseURL: devServerUrl,
    permissions: ['camera'],
    viewport: { width: 1440, height: 900 },
    launchOptions: {
      ...(process.env.VISIGN_BROWSER_CHANNEL ? { channel: process.env.VISIGN_BROWSER_CHANNEL } : {}),
      args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
    },
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev -- --port 5173 --strictPort',
    url: devServerUrl,
    reuseExistingServer: !process.env.CI,
  },
});
