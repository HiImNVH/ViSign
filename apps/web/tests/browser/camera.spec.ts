// apps/web/tests/browser/camera.spec.ts - Dich truc tiep (T105-T106) voi camera gia va WebM that.
// Bo phat hien nguoi/mat/tay duoc thay bang stub (liveHelpers); MediaRecorder, upload multipart va giao dien la that.
import { expect, test, type Page } from '@playwright/test';
import { installPresenceStub, setScene, signOnce, startLive } from './liveHelpers';

const metadata = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1',
  meanings: ['GIAY_TO', 'NHAN'], acceptanceThreshold: .5,
  macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
const reply = (text: string, accepted = true) => ({
  requestId: crypto.randomUUID(), text: accepted ? text : 'Không nhận diện được', classLabel: accepted ? 'NHAN_HCM_1' : null,
  confidence: accepted ? .82 : .3, accepted, modelVersion: metadata.modelVersion, processingTimeMs: 20,
});

async function expectInCameraLayout(page: Page) {
  const camera = await page.locator('.camera-viewport').boundingBox();
  const actions = await page.getByRole('group', { name: 'Điều khiển dịch trực tiếp' }).boundingBox();
  if (!camera || !actions) throw new Error('Missing camera layout');
  expect(actions.y).toBeGreaterThanOrEqual(camera.y);
  expect(actions.y + actions.height).toBeLessThanOrEqual(camera.y + camera.height + 1);
  expect(actions.x).toBeGreaterThanOrEqual(camera.x);
  expect(actions.x + actions.width).toBeLessThanOrEqual(camera.x + camera.width + 1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  for (const button of await page.locator('.capture-controls button:visible').all()) {
    expect((await button.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(44);
  }
}

test.beforeEach(async ({ page }) => {
  await installPresenceStub(page);
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: metadata }));
});

test('signs are recorded as real WebM, uploaded automatically and joined into the transcript', async ({ page }) => {
  const bodies: number[] = [];
  const words = ['Nhận', 'Giấy tờ (giấy)'];
  await page.route('**/api/v1/predictions', route => {
    const request = route.request();
    expect(request.headers()['content-type']).toContain('multipart/form-data');
    const body = request.postDataBuffer() ?? Buffer.alloc(0);
    expect(body.includes(Buffer.from('name="clip"'))).toBe(true);
    expect(body.includes(Buffer.from([0x1a, 0x45, 0xdf, 0xa3]))).toBe(true); // EBML/WebM
    bodies.push(body.length);
    return route.fulfill({ status: 200, json: reply(words[bodies.length - 1] ?? 'Nhận') });
  });
  await page.goto('/');
  await expect(page.getByRole('status')).toHaveText('Đang tắt');
  await startLive(page);
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText('Đã dịch');
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Nhận');
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng', { timeout: 5000 });
  await signOnce(page);
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' })).toContainText('Nhận Giấy tờ (giấy)');
  expect(bodies).toHaveLength(2);
  expect(Math.min(...bodies)).toBeGreaterThan(1000);
  await page.getByRole('button', { name: 'Tắt camera' }).click();
  await expect(page.getByRole('status')).toHaveText('Đang tắt');
  await expect(page.getByRole('button', { name: 'Bật camera' })).toBeFocused();
});

test('no person, partial presence and stillness never record or upload', async ({ page }) => {
  let uploads = 0;
  await page.route('**/api/v1/predictions', route => { uploads++; return route.abort(); });
  await page.goto('/');
  await startLive(page, 'none');
  await expect(page.getByRole('status')).toHaveText('Không phát hiện người');
  await setScene(page, 'partial');
  await expect(page.getByRole('status')).toHaveText('Chưa thấy đủ mặt và tay');
  await expect(page.getByRole('list', { name: 'Trạng thái phát hiện' })).toContainText('Mặt: chưa có');
  await setScene(page, 'ready');
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng');
  await page.waitForTimeout(1500);
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng');
  expect(uploads).toBe(0);
  await expectInCameraLayout(page);
});

test('a rejected sign is announced without changing the transcript', async ({ page }) => {
  await page.route('**/api/v1/predictions', route => route.fulfill({ status: 200, json: reply('', false) }));
  await page.goto('/');
  await startLive(page);
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText('Không nhận diện được');
  await expect(page.getByRole('region', { name: 'Kết quả nhận diện' })).toContainText('Chưa nhận diện được ký hiệu');
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveCount(0);
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng', { timeout: 5000 });
});

test('a busy service shows safe guidance, then resumes listening without resending', async ({ page }) => {
  let uploads = 0;
  await page.route('**/api/v1/predictions', route => {
    uploads++;
    return route.fulfill({ status: 503, headers: { 'Retry-After': '2' },
      json: { code: 'SERVICE_BUSY', message: 'internal detail', requestId: crypto.randomUUID() } });
  });
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto('/');
  await startLive(page);
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText('Lỗi');
  await expect(page.getByRole('alert')).toContainText('Dịch vụ đang bận');
  await expect(page.getByText('internal detail')).toHaveCount(0);
  await expectInCameraLayout(page);
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng', { timeout: 6000 });
  expect(uploads).toBe(1);
});

test('a prediction timeout is reported once and the stale answer is ignored', async ({ page }) => {
  let uploads = 0;
  await page.route('**/api/v1/predictions', async route => {
    uploads++;
    await new Promise(resolve => setTimeout(resolve, 20_000));
    await route.fulfill({ status: 200, json: reply('Stale') }).catch(() => {});
  });
  await page.clock.install();
  await page.goto('/');
  await startLive(page);
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText('Đang dịch');
  await page.clock.fastForward(15_001);
  await expect(page.getByRole('alert')).toContainText('Dịch vụ phản hồi quá lâu.');
  expect(uploads).toBe(1);
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveCount(0);
});

test('model metadata outage keeps the camera listening but never records', async ({ page }) => {
  let uploads = 0;
  await page.unroute('**/api/v1/model-info');
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 503,
    json: { code: 'MODEL_NOT_READY', message: 'private', requestId: crypto.randomUUID() } }));
  await page.route('**/api/v1/predictions', route => { uploads++; return route.abort(); });
  await page.goto('/');
  await startLive(page, 'ready');
  await page.evaluate(() => { window.__visignSignUntil = performance.now() + 1500; });
  await page.waitForTimeout(1800);
  await expect(page.getByRole('button', { name: 'Thử kết nối lại' })).toBeVisible();
  expect(uploads).toBe(0);
});

test('pause and resume work from the keyboard and pausing blocks recording', async ({ page }) => {
  let uploads = 0;
  await page.route('**/api/v1/predictions', route => { uploads++; return route.fulfill({ status: 200, json: reply('Nhận') }); });
  await page.goto('/');
  await startLive(page);
  const pause = page.getByRole('button', { name: 'Tạm dừng' });
  await pause.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('status')).toHaveText('Tạm dừng');
  await page.evaluate(() => { window.__visignSignUntil = performance.now() + 1200; });
  await page.waitForTimeout(1500);
  expect(uploads).toBe(0);
  await page.getByRole('button', { name: 'Tiếp tục' }).press('Space');
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText('Đã dịch');
  expect(uploads).toBe(1);
});

test('help supports Escape, focus restoration and reduced motion', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const help = page.getByRole('button', { name: 'Hướng dẫn', exact: true });
  await help.click();
  const dialog = page.getByRole('dialog', { name: 'Dịch ký hiệu trực tiếp' });
  await expect(dialog).toBeVisible();
  await expect(page.getByRole('button', { name: 'Đóng hướng dẫn' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(help).toBeFocused();
  await expect(help).toHaveCSS('transition-duration', '0s');
});

test('denied camera permission shows a recoverable error', async ({ page, context }) => {
  await context.clearPermissions();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Browser.setPermission', { permission: { name: 'camera' }, setting: 'denied', origin: 'http://127.0.0.1:4173' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Lỗi');
  await expect(page.getByRole('alert')).toContainText('Chưa có quyền sử dụng camera');
  await expect(page.getByRole('button', { name: 'Thử lại', exact: true })).toBeFocused();
  await expectInCameraLayout(page);
});

test('T040 live backend translates an automatically captured WebM', async ({ page }) => {
  test.skip(!process.env.VISIGN_LIVE_API_URL, 'Requires real Uvicorn and a preview build with VITE_API_BASE_URL set');
  await page.unroute('**/api/v1/model-info');
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await startLive(page);
  await signOnce(page);
  await expect(page.getByRole('status')).toHaveText(/Đã dịch|Không nhận diện được|Lỗi/, { timeout: 30_000 });
  expect(errors).toEqual([]);
});
