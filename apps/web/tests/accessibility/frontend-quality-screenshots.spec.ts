// apps/web/tests/accessibility/frontend-quality-screenshots.spec.ts - T088: chup man hinh cac trang thai de audit UX.
// Chi chay khi dat VISIGN_CAPTURE_SCREENSHOTS=<thu muc dich>; lan chay thuong bo qua de khong ghi file.
import { resolve } from 'node:path';
import { expect, test, type Page } from '@playwright/test';
import { installPresenceStub, signOnce, startLive } from '../browser/liveHelpers';

const outDir = process.env.VISIGN_CAPTURE_SCREENSHOTS;
const metadata = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1', meanings: ['Cảm ơn', 'Sốt'],
  acceptanceThreshold: .7, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};

async function snap(page: Page, state: string) {
  const project = test.info().project.name;
  await page.screenshot({ path: resolve(outDir!, `${project}-${state}.jpg`), type: 'jpeg', quality: 70 });
}

async function setup(page: Page, accepted: boolean | 'busy') {
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: metadata }));
  await page.route('**/api/v1/predictions', route => {
    const requestId = crypto.randomUUID();
    if (accepted === 'busy') return route.fulfill({ status: 503, headers: { 'Retry-After': '3' },
      json: { code: 'SERVICE_BUSY', message: 'busy', requestId } });
    return route.fulfill({ status: 200, json: { requestId, text: accepted ? 'Cảm ơn' : 'Không nhận diện được',
      classLabel: accepted ? 'CAM_ON_HN_1' : null, confidence: accepted ? .93 : .41, accepted,
      modelVersion: metadata.modelVersion, processingTimeMs: 120 } });
  });
}

async function record(page: Page) {
  await startLive(page);
  await signOnce(page);
}

test.describe('T088 frontend quality screenshots', () => {
  test.skip(!outDir, 'Đặt VISIGN_CAPTURE_SCREENSHOTS để chụp ảnh audit');
  test.beforeEach(async ({ page }) => { await installPresenceStub(page); });

  test('luồng accepted + lịch sử', async ({ page }) => {
    await setup(page, true);
    await page.goto('/');
    await snap(page, '1-idle');
    await record(page);
    await snap(page, '2-recording');
    await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Cảm ơn');
    await snap(page, '3-accepted');
    await page.getByRole('button', { name: 'Lịch sử', exact: true }).click();
    await page.waitForTimeout(300);
    await snap(page, '4-history');
  });

  test('rejected', async ({ page }) => {
    await setup(page, false);
    await page.goto('/');
    await record(page);
    await expect(page.getByText('Chưa nhận diện được ký hiệu. Hãy quay một ký hiệu mới.')).toBeVisible();
    await snap(page, '5-rejected');
  });

  test('lỗi dịch vụ bận', async ({ page }) => {
    await setup(page, 'busy');
    await page.goto('/');
    await record(page);
    await expect(page.getByRole('alert')).toContainText('Dịch vụ đang bận');
    await snap(page, '6-busy');
  });
});
