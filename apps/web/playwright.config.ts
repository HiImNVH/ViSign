// apps/web/playwright.config.ts - Kiem tra ban build voi may chu rieng de tranh nham ung dung.
import { defineConfig } from '@playwright/test';
import { cameraFixture } from './tests/browser/cameraFixture';

export default defineConfig({
  testDir: './tests',
  testMatch: ['browser/**/*.spec.ts', 'accessibility/**/*.spec.ts'],
  forbidOnly: Boolean(process.env.CI),
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    browserName: 'chromium',
    ...(process.env.VISIGN_BROWSER_CHANNEL ? { channel: process.env.VISIGN_BROWSER_CHANNEL } : {}),
    trace: 'retain-on-failure',
    permissions: ['camera'],
    launchOptions: { args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', `--use-file-for-fake-video-capture=${cameraFixture()}`] },
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { viewport: { width: 320, height: 640 }, isMobile: true, hasTouch: true } },
    { name: 'landscape', use: { viewport: { width: 640, height: 360 }, isMobile: true, hasTouch: true } },
  ],
  webServer: {
    command: 'npm run preview -- --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
  },
});
