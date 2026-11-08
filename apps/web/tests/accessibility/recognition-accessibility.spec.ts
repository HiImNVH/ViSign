// T063 (cap nhat cho dich truc tiep T106): ban phim, focus, thong bao trang thai va axe WCAG A/AA.
import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { installPresenceStub, setScene, signOnce, startLive } from '../browser/liveHelpers';

const model = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1',
  meanings: ['Xin chào'], acceptanceThreshold: .7,
  macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
const audit = (page: Page) => new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();

test.beforeEach(async ({ page }) => {
  await installPresenceStub(page);
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
});

test('T063 keyboard starts, pauses, resumes and stops live translation with status announcements', async ({ page }) => {
  await page.route('**/api/v1/predictions', route => route.fulfill({ status: 200, json: {
    requestId: '123e4567-e89b-42d3-a456-426614174000', text: 'Xin chào', classLabel: 'XIN_CHAO',
    confidence: .95, accepted: true, modelVersion: model.modelVersion, processingTimeMs: 10 } }));
  await page.goto('/');
  const status = page.getByRole('status');
  await expect(status).toHaveAttribute('aria-atomic', 'true');
  await expect(status).toHaveText('Đang tắt');
  await page.getByRole('button', { name: 'Bật camera' }).focus();
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByRole('button', { name: 'Hướng dẫn' })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Bật camera' })).toBeFocused();
  await page.keyboard.press('Space');
  await expect(status).not.toHaveText(/Đang tắt|Đang khởi động/, { timeout: 30_000 });
  await setScene(page, 'ready');
  await expect(status).toHaveText('Sẵn sàng');
  await expect(page.getByRole('button', { name: 'Tạm dừng' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(status).toHaveText('Tạm dừng');
  await expect(page.getByRole('button', { name: 'Tiếp tục' })).toBeFocused();
  await page.keyboard.press('Enter');
  await signOnce(page);
  await expect(status).toHaveText('Đã dịch');
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toHaveAttribute('aria-live', 'polite');
  await expect(page.getByRole('region', { name: 'Bản dịch trực tiếp' }).locator('[aria-live="polite"]')).toHaveText('Xin chào');
  await page.getByRole('button', { name: 'Tắt camera' }).focus();
  await page.keyboard.press('Enter');
  await expect(status).toHaveText('Đang tắt');
  await expect(page.getByRole('button', { name: 'Bật camera' })).toBeFocused();
});

test('T063 camera region describes privacy and passes axe in off, help and permission error', async ({ page, context }) => {
  await page.goto('/');
  const region = page.getByRole('region', { name: 'Dịch ký hiệu trực tiếp bằng camera' });
  await expect(region).toHaveAttribute('aria-describedby', 'camera-privacy');
  await expect(page.locator('#camera-privacy')).toContainText('tự ghi từng đoạn ký hiệu');
  expect((await audit(page)).violations).toEqual([]);
  await page.getByRole('button', { name: 'Hướng dẫn' }).click();
  const dialog = page.getByRole('dialog', { name: 'Dịch ký hiệu trực tiếp' });
  await expect(dialog.getByRole('button', { name: 'Đóng hướng dẫn' })).toBeFocused();
  expect((await audit(page)).violations).toEqual([]);
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: 'Đóng hướng dẫn' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Hướng dẫn' })).toBeFocused();
  await context.clearPermissions();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Browser.setPermission', { permission: { name: 'camera' }, setting: 'denied', origin: 'http://127.0.0.1:4173' });
  await page.getByRole('button', { name: 'Bật camera' }).click();
  await expect(page.getByRole('alert')).toContainText('Chưa có quyền sử dụng camera');
  await expect(page.getByRole('button', { name: 'Thử lại' })).toBeFocused();
  expect((await audit(page)).violations).toEqual([]);
});

test('T063 waiting, ready and partial-presence states pass axe and expose detection chips', async ({ page }) => {
  await page.goto('/');
  await startLive(page, 'partial');
  await expect(page.getByRole('status')).toHaveText('Chưa thấy đủ mặt và tay');
  const chips = page.getByRole('list', { name: 'Trạng thái phát hiện' });
  await expect(chips).toContainText('Người: có');
  await expect(chips).toContainText('Tay: chưa có');
  expect((await audit(page)).violations).toEqual([]);
  await setScene(page, 'ready');
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng');
  expect((await audit(page)).violations).toEqual([]);
});

for (const accepted of [true, false]) {
  test(`T063 ${accepted ? 'accepted' : 'rejected'} live results are announced and pass axe`, async ({ page }) => {
    await page.route('**/api/v1/predictions', route => route.fulfill({ status: 200, json: {
      requestId: '123e4567-e89b-42d3-a456-426614174000', text: accepted ? 'Xin chào' : 'Không nhận diện được',
      classLabel: accepted ? 'XIN_CHAO' : null, confidence: accepted ? .95 : .2,
      accepted, modelVersion: model.modelVersion, processingTimeMs: 10 } }));
    await page.goto('/');
    await startLive(page);
    await signOnce(page);
    const result = page.getByRole('region', { name: accepted ? 'Văn bản dịch' : 'Kết quả nhận diện' });
    await expect(result).toBeVisible();
    await expect(page.getByRole('status')).toHaveText(accepted ? 'Đã dịch' : 'Không nhận diện được');
    await expect(result).toHaveAttribute('aria-live', 'polite');
    // The last result stays readable after the status returns to listening.
    await expect(page.getByRole('status')).toHaveText('Sẵn sàng', { timeout: 5000 });
    await expect(result).toBeVisible();
    expect((await audit(page)).violations).toEqual([]);
  });
}

test('T063 focused control outline fits inside a compact landscape viewport', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 180 });
  await page.goto('/');
  const button = page.getByRole('button', { name: 'Bật camera' });
  await button.focus();
  await expect(button).toBeFocused();
  const camera = await page.locator('.camera-viewport').boundingBox();
  const focus = await button.boundingBox();
  expect(camera).not.toBeNull();
  expect(focus).not.toBeNull();
  // A 3px focus outline plus 4px offset must remain inside the clipped viewport.
  expect(focus!.y + focus!.height + 7).toBeLessThanOrEqual(camera!.y + camera!.height);
  expect(focus!.x).toBeGreaterThanOrEqual(camera!.x + 7);
  expect(focus!.x + focus!.width + 7).toBeLessThanOrEqual(camera!.x + camera!.width);
});
