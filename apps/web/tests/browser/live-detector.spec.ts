// T105: bo phat hien MediaPipe that (WASM + model cung origin) nap duoc va bao "Khong phat hien nguoi" voi
// camera gia khong co nguoi; khong tu ghi hay gui doan nao.
import { expect, test } from '@playwright/test';

const model = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1',
  meanings: ['GIAY_TO', 'NHAN'], acceptanceThreshold: .5,
  macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};

test('T105 real MediaPipe detector loads and finds no person in the synthetic camera', async ({ page }) => {
  test.setTimeout(90_000);
  let uploads = 0;
  const assetErrors: string[] = [];
  page.on('response', response => {
    if (response.url().includes('/mediapipe/') && !response.ok()) assetErrors.push(`${response.status()} ${response.url()}`);
  });
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
  await page.route('**/api/v1/predictions', route => { uploads++; return route.abort(); });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera' }).click();
  await expect(page.getByRole('status')).toHaveText('Không phát hiện người', { timeout: 60_000 });
  await page.waitForTimeout(1500);
  await expect(page.getByRole('status')).toHaveText('Không phát hiện người');
  expect(assetErrors).toEqual([]);
  expect(uploads).toBe(0);
});
