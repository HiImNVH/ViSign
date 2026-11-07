// apps/web/playwright.e2e.config.ts - E2E T032/T047: camera gia + MediaRecorder that + FastAPI that (fixture).
import { resolve } from 'node:path';
import { defineConfig } from '@playwright/test';
import { cameraFixture } from './tests/browser/cameraFixture';

const repoRoot = resolve(import.meta.dirname, '../..');
const artifacts = resolve(repoRoot, 'services/inference-api/tests/fixtures/model-artifacts');
export const E2E_WEB_PORT = 4180;
export const BACKENDS = { accepted: 8100, lowConfidence: 8101, degraded: 8102 } as const;

function backend(port: number, artifact: string | null) {
  return {
    command: `uv run --locked --project ${resolve(repoRoot, 'services/inference-api')} uvicorn visign_api.main:app --host 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}/api/v1/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    // Khong co MODEL_ARTIFACT_PATH -> service degraded, du doan tra 503 MODEL_NOT_READY
    env: artifact ? { MODEL_ARTIFACT_PATH: resolve(artifacts, artifact) } : { MODEL_ARTIFACT_PATH: '' },
  };
}

export default defineConfig({
  testDir: './tests/e2e',
  forbidOnly: Boolean(process.env.CI),
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: `http://127.0.0.1:${E2E_WEB_PORT}`,
    browserName: 'chromium',
    ...(process.env.VISIGN_BROWSER_CHANNEL ? { channel: process.env.VISIGN_BROWSER_CHANNEL } : {}),
    trace: 'retain-on-failure',
    permissions: ['camera'],
    viewport: { width: 1280, height: 800 },
    launchOptions: { args: ['--use-fake-device-for-media-stream', `--use-file-for-fake-video-capture=${cameraFixture()}`] },
  },
  webServer: [
    backend(BACKENDS.accepted, 'fixture'),
    backend(BACKENDS.lowConfidence, 'fixture-low-confidence'),
    backend(BACKENDS.degraded, null),
    {
      // Ban build that, API base tuong doi; tung test chon backend that bang route.continue({ url })
      command: `npm run build && npm run preview -- --port ${E2E_WEB_PORT} --strictPort`,
      url: `http://127.0.0.1:${E2E_WEB_PORT}`,
      reuseExistingServer: false,
      timeout: 180_000,
    },
  ],
});
