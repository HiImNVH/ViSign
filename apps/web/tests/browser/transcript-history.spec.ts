import { expect, test, type Page } from '@playwright/test';
import { installPresenceStub, signOnce, startLive } from './liveHelpers';

test.beforeEach(async ({ page }) => { await installPresenceStub(page); });

const historyKey = 'visign.translation-history.v1';
const model = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1',
  meanings: ['Xin chào', 'Cảm ơn'], acceptanceThreshold: .7,
  macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};

async function recordAndSubmit(page: Page, first = false) {
  if (first) await startLive(page);
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText(/Đã dịch|Không nhận diện được/);
}

function mockPredictions(page: Page) {
  const postUrls: string[] = [];
  let uploads = 0;
  page.on('request', request => {
    if (request.method() === 'POST') postUrls.push(request.url());
  });
  return {
    postUrls,
    get uploads() { return uploads; },
    async register() {
      await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
      await page.route('**/api/v1/predictions', route => {
        uploads++;
        expect(route.request().method()).toBe('POST');
        expect(route.request().postDataBuffer()?.length ?? 0).toBeGreaterThan(100);
        expect(route.request().headers()['content-type']).toContain('multipart/form-data');
        return route.fulfill({ status: 200, json: {
          requestId: `123e4567-e89b-42d3-a456-42661417400${uploads}`,
          text: uploads === 1 ? 'Xin chào' : uploads === 2 ? 'Cảm ơn' : 'Không nhận diện được',
          classLabel: uploads === 3 ? null : 'LABEL',
          confidence: uploads === 3 ? .45 : .93,
          accepted: uploads !== 3, modelVersion: model.modelVersion, processingTimeMs: 12,
        } });
      });
    },
  };
}

test('T104 two accepted clips form a transcript; rejected clip is excluded; history is local and clearable', async ({ page }) => {
  const mock = mockPredictions(page);
  await mock.register();
  await page.goto('/');

  await recordAndSubmit(page, true);
  const transcript = page.getByRole('region', { name: 'Bản dịch trực tiếp' });
  await expect(transcript).toContainText('Xin chào');
  await recordAndSubmit(page);
  await expect(transcript.locator('.transcript-text')).toHaveText('Xin chào Cảm ơn');
  await expect(transcript.locator('[aria-live]')).toHaveText('Cảm ơn');
  await recordAndSubmit(page);
  await expect(page.getByRole('region', { name: 'Kết quả nhận diện' })).toContainText('Chưa nhận diện được');
  await expect(transcript.locator('.transcript-text')).toHaveText('Xin chào Cảm ơn');
  await expect(transcript.locator('[aria-live]')).toHaveText('Cảm ơn');
  expect(mock.uploads).toBe(3);

  const stored = await page.evaluate(key => localStorage.getItem(key), historyKey);
  expect(stored).not.toBeNull();
  const parsed = JSON.parse(stored!);
  expect(parsed.schemaVersion).toBe(1);
  expect(parsed.entries).toHaveLength(2);
  expect(parsed.entries.map((item: { text: string }) => item.text)).toEqual(['Xin chào', 'Cảm ơn']);
  for (const entry of parsed.entries) {
    expect(Object.keys(entry).sort()).toEqual(['confidence', 'createdAt', 'modelVersion', 'requestId', 'text']);
  }
  expect(stored).not.toMatch(/video|landmark|frame|classLabel|data:video/i);
  expect(mock.postUrls).toHaveLength(3);
  expect(mock.postUrls.every(url => new URL(url).pathname === '/api/v1/predictions')).toBe(true);

  for (const size of [page.viewportSize()!, { width: 320, height: 180 }]) {
    await page.setViewportSize(size);
    expect(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight
      && document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  await page.reload();
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Lịch sử' }).click();
  const dialog = page.getByRole('dialog', { name: 'Lịch sử bản dịch' });
  await expect(dialog).toContainText('Xin chào');
  await expect(dialog).toContainText('Cảm ơn');
  await expect(dialog.locator('li')).toHaveCount(2);
  await expect(dialog).toContainText('Chỉ lưu trên thiết bị này trong 24 giờ');
  await dialog.getByRole('button', { name: 'Xoá toàn bộ lịch sử' }).click();
  await expect(dialog).toContainText('Xác nhận');
  await dialog.getByRole('button', { name: 'Xác nhận xoá' }).click();
  await expect(dialog).toContainText('Chưa có bản dịch được lưu.');
  expect(await page.evaluate(key => localStorage.getItem(key), historyKey)).toBeNull();
  expect(mock.uploads).toBe(3);
  expect(mock.postUrls).toHaveLength(3);
});

test('T104 stored metadata expires on reload at 24 hours', async ({ page }) => {
  const mock = mockPredictions(page);
  await mock.register();
  await page.clock.install({ time: new Date('2026-11-08T00:00:00.000Z') });
  await page.goto('/');
  await recordAndSubmit(page, true);
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' })).toContainText('Xin chào');
  const stored = await page.evaluate(key => localStorage.getItem(key), historyKey);
  expect(stored).not.toBeNull();
  const createdAt = JSON.parse(stored!).entries[0].createdAt as string;

  await page.clock.setSystemTime(new Date(Date.parse(createdAt) + 24 * 60 * 60 * 1000));
  await page.reload();
  expect(await page.evaluate(key => localStorage.getItem(key), historyKey)).toBeNull();
  await page.getByRole('button', { name: 'Lịch sử' }).click();
  await expect(page.getByRole('dialog', { name: 'Lịch sử bản dịch' })).toContainText('Chưa có bản dịch được lưu.');
  expect(mock.uploads).toBe(1);
  expect(mock.postUrls).toHaveLength(1);
});

test('FE-T090-02 another tab refreshes open history on append and on clear', async ({ page, context }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Lịch sử' }).click();
  const history = page.getByRole('dialog', { name: 'Lịch sử bản dịch' });
  await expect(history).toContainText('Chưa có bản dịch được lưu.');
  const other = await context.newPage();
  await other.goto('/');
  await other.evaluate(key => localStorage.setItem(key, JSON.stringify({ schemaVersion: 1,
    entries: [{ requestId: '123e4567-e89b-42d3-a456-426614174001', text: 'Từ tab thứ hai',
      confidence: .9, modelVersion: 'pilot-v1', createdAt: new Date().toISOString() }],
  })), historyKey);
  await expect(history).toContainText('Từ tab thứ hai');
  await other.evaluate(key => localStorage.removeItem(key), historyKey);
  await expect(history).toContainText('Chưa có bản dịch được lưu.');
  await expect(history.locator('li')).toHaveCount(0);
  await other.close();
});

test('FE-T090-05 1200 valid entries stay stored while history renders 50 at a time', async ({ page }) => {
  await page.addInitScript(key => {
    const entries = Array.from({ length: 1200 }, (_, n) => ({
      requestId: `123e4567-e89b-42d3-a456-${(n + 1).toString(16).padStart(12, '0')}`,
      text: `Ký hiệu ${n}`, confidence: .93, modelVersion: 'pilot-v1', createdAt: new Date().toISOString(),
    }));
    localStorage.setItem(key, JSON.stringify({ schemaVersion: 1, entries }));
  }, historyKey);
  await page.goto('/');
  await page.getByRole('button', { name: 'Lịch sử' }).click();
  const history = page.getByRole('dialog', { name: 'Lịch sử bản dịch' });
  await expect(history.locator('li')).toHaveCount(50);
  await expect(history).toContainText('Ký hiệu 1199');
  await expect(history).not.toContainText('Ký hiệu 0 ');
  await history.getByRole('button', { name: 'Xem thêm bản dịch cũ' }).click();
  await expect(history.locator('li')).toHaveCount(100);
  const evidence = await page.evaluate(key => {
    const raw = localStorage.getItem(key)!;
    return { entries: JSON.parse(raw).entries.length, bytes: new Blob([raw]).size,
      rendered: document.querySelectorAll('.history-entries li').length };
  }, historyKey);
  expect(evidence.entries).toBe(1200);
  expect(evidence.rendered).toBe(100);
  expect(evidence.bytes).toBeLessThan(500_000);
});
