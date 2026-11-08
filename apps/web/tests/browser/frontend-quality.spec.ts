// T088: reproducible FE audit on the production camera flow with synthetic video/API responses.
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { expect, test, type Page } from '@playwright/test';
import { installPresenceStub, signOnce, startLive } from './liveHelpers';

test.beforeEach(async ({ page }) => { await installPresenceStub(page); });

const model = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1',
  meanings: ['Xin chào', 'Cảm ơn', 'Giấy tờ', 'Bệnh viện', 'Trường học',
    'Gia đình', 'Thời tiết', 'Hôm nay', 'Ngày mai', 'Giúp đỡ'],
  acceptanceThreshold: .7, macroF1: null, perMeaningRecall: null, evaluatedAt: null,
  demoReady: false,
};

const screenshots = resolve(import.meta.dirname, '../../../../docs/evidence/checkpoints/CP7/T088-screenshots');

async function saveEvidence(page: Page, name: string) {
  if (process.env.VISIGN_CAPTURE_T088 !== '1') return;
  mkdirSync(screenshots, { recursive: true });
  await page.screenshot({ path: join(screenshots, `${name}.jpg`), type: 'jpeg', quality: 66,
    animations: 'disabled' });
}

async function recordClip(page: Page) {
  await startLive(page);
  await signOnce(page);
}

async function assertCameraLayout(page: Page) {
  const camera = await page.locator('.camera-viewport').boundingBox();
  const controls = await page.locator('.capture-controls').boundingBox();
  const translation = await page.getByRole('region', { name: 'Văn bản dịch' }).boundingBox();
  const transcript = await page.getByRole('region', { name: 'Bản dịch trực tiếp' }).boundingBox();
  const status = await page.getByRole('status').boundingBox();
  if (!camera || !controls || !translation || !transcript || !status) throw new Error('Missing layout regions');
  // All controls and the full accepted-result panel must be visible, with no page scroll.
  expect(translation.y).toBeGreaterThanOrEqual(camera.y);
  expect(translation.y + translation.height).toBeLessThanOrEqual(controls.y + 1);
  expect(controls.y + controls.height).toBeLessThanOrEqual(camera.y + camera.height + 1);
  expect(controls.x).toBeGreaterThanOrEqual(camera.x);
  expect(controls.x + controls.width).toBeLessThanOrEqual(camera.x + camera.width + 1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1
    && document.documentElement.scrollHeight <= innerHeight + 1)).toBe(true);
  // These two top overlays must not hide one another after a successful recognition.
  const horizontalOverlap = transcript.x < status.x + status.width && status.x < transcript.x + transcript.width;
  const verticalOverlap = transcript.y < status.y + status.height && status.y < transcript.y + transcript.height;
  expect(horizontalOverlap && verticalOverlap, 'Transcript obscures camera status').toBe(false);
  const buttons = await page.locator('.capture-controls button:visible').all();
  for (const button of buttons) {
    const rect = await button.boundingBox();
    expect(rect?.height ?? 0).toBeGreaterThanOrEqual(44);
  }
}

test('T088 accepted flow: overlays, 10 meanings and camera controls fit responsive viewports', async ({ page }, info) => {
  let uploads = 0;
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
  await page.route('**/api/v1/predictions', route => {
    uploads++;
    return route.fulfill({ status: 200, json: {
      requestId: '123e4567-e89b-42d3-a456-426614174000',
      text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: .93, accepted: true,
      modelVersion: model.modelVersion, processingTimeMs: 12,
    } });
  });
  await page.goto('/');
  await recordClip(page);
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Xin chào');
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng', { timeout: 5000 });
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' })).toContainText('Xin chào');
  expect(uploads).toBe(1);
  const initial = page.viewportSize()!;
  await assertCameraLayout(page);
  await saveEvidence(page, `accepted-${info.project.name}`);
  for (const size of [{ width: 768, height: 1024 }, { width: 320, height: 180 }]) {
    await page.setViewportSize(size);
    await assertCameraLayout(page);
  }
  await page.setViewportSize(initial);
});

test('T088 permission denial and populated history pass axe after state changes', async ({ page, context }, info) => {
  await page.addInitScript(() => localStorage.setItem('visign.translation-history.v1', JSON.stringify({
    schemaVersion: 1,
    entries: [{ requestId: '123e4567-e89b-42d3-a456-426614174000',
      text: 'Xin chào', confidence: .93, modelVersion: 'pilot-v1', createdAt: new Date().toISOString() }],
  })));
  await context.clearPermissions();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Browser.setPermission', { permission: { name: 'camera' }, setting: 'denied',
    origin: 'http://127.0.0.1:4173' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera' }).click();
  await expect(page.getByRole('alert')).toContainText('Chưa có quyền sử dụng camera');
  await expect(page.getByRole('button', { name: 'Thử lại' })).toBeFocused();
  const denial = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(denial.violations).toEqual([]);
  await saveEvidence(page, `permission-${info.project.name}`);
  await page.getByRole('button', { name: 'Lịch sử' }).click();
  const dialog = page.getByRole('dialog', { name: 'Lịch sử bản dịch' });
  await expect(dialog).toContainText('Xin chào');
  const historyAudit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(historyAudit.violations).toEqual([]);
  await saveEvidence(page, `history-${info.project.name}`);
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Lịch sử' })).toBeFocused();
});

test('T088 submission busy and recoverable API error pass axe', async ({ page }, info) => {
  let release!: () => void;
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
  await page.route('**/api/v1/predictions', async route => {
    await new Promise<void>(resolve => { release = resolve; });
    await route.fulfill({ status: 503, json: { code: 'SERVICE_BUSY', message: 'internal details', requestId: 'x' } });
  });
  await page.goto('/');
  await recordClip(page);
  await expect(page.getByRole('status')).toHaveText('Đang dịch');
  const pendingAudit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(pendingAudit.violations).toEqual([]);
  release();
  await expect(page.getByRole('alert')).toContainText('Dịch vụ đang bận');
  await expect(page.getByRole('status')).toHaveText('Lỗi');
  const errorAudit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(errorAudit.violations).toEqual([]);
  await saveEvidence(page, `api-error-${info.project.name}`);
});
