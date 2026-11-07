// apps/web/tests/browser/camera.spec.ts - Kiem tra MediaRecorder that voi camera Y4M va khong upload.
import { expect, test, type Page } from '@playwright/test';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RecognitionOverlay } from '../../src/features/recognition/RecognitionOverlay';

async function expectInCameraLayout(page: Page) {
  const camera = await page.locator('.camera-viewport').boundingBox();
  const actions = await page.getByRole('group', { name: 'Điều khiển camera' }).boundingBox();
  if (!camera || !actions) throw new Error('Missing camera layout');
  expect(camera.width).toBeGreaterThan((page.viewportSize()?.width ?? 0) * .90);
  expect(camera.height).toBeGreaterThan((page.viewportSize()?.height ?? 0) * .70);
  expect(actions.y).toBeGreaterThanOrEqual(camera.y);
  expect(actions.y + actions.height).toBeLessThanOrEqual(camera.y + camera.height);
  expect(actions.x).toBeGreaterThanOrEqual(camera.x);
  expect(actions.x + actions.width).toBeLessThanOrEqual(camera.x + camera.width);
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toHaveCount(0);
  await expect(page.getByText('Chưa có bản dịch.')).toHaveCount(0);
  await expect(page.getByText('Một ký hiệu, một lần quay.')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth && document.documentElement.scrollHeight <= innerHeight)).toBe(true);
}

test('explicitly records and discards a real WebM clip, then releases camera', async ({ page }, testInfo) => {
  const outbound: string[] = [];
  const runtimeErrors: string[] = [];
  page.on('pageerror', error => runtimeErrors.push(error.message));
  page.on('request', request => { if (request.method() !== 'GET' || new URL(request.url()).pathname.startsWith('/api/')) outbound.push(request.url()); });
  await page.goto('/');
  await expectInCameraLayout(page);
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await expectInCameraLayout(page);
  const preview = page.getByLabel('Hình ảnh xem trước từ camera');
  await expect.poll(() => preview.evaluate(video => (video as HTMLVideoElement).videoWidth)).toBeGreaterThan(0);
  await expect.poll(() => preview.evaluate(video => (video as HTMLVideoElement).currentTime)).toBeGreaterThan(0);
  const track = await preview.evaluateHandle(video => ((video as HTMLVideoElement).srcObject as MediaStream).getVideoTracks()[0]!);
  await expect(page.getByRole('button', { name: 'Kết thúc', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Quay ký hiệu', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Đang quay ký hiệu');
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Kết thúc', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Đã quay xong');
  await expectInCameraLayout(page);
  await page.screenshot({ path: testInfo.outputPath('camera-captured.png'), fullPage: true });
  await page.getByRole('button', { name: 'Hủy đoạn quay', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await page.getByRole('button', { name: 'Quay ký hiệu', exact: true }).click();
  await page.getByRole('button', { name: 'Hủy đoạn quay', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await page.getByRole('button', { name: 'Tắt camera', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera chưa bật');
  await expectInCameraLayout(page);
  expect(await track.evaluate(track => track.readyState)).toBe('ended');
  expect(await preview.evaluate(video => (video as HTMLVideoElement).srcObject)).toBeNull();
  expect(outbound).toEqual([]);
  expect(runtimeErrors).toEqual([]);
});

test('an open help dialog keeps focus when the camera disconnects', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await page.getByRole('button', { name: 'Hướng dẫn', exact: true }).click();
  await page.locator('video').evaluate(video => {
    ((video as HTMLVideoElement).srcObject as MediaStream).getVideoTracks()[0]!.dispatchEvent(new Event('ended'));
  });
  await expect(page.getByRole('button', { name: 'Đóng hướng dẫn' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Hướng dẫn', exact: true })).toBeFocused();
  await expect(page.getByRole('alert')).toContainText('Camera đã mất kết nối');
  await expectInCameraLayout(page);
});

test('accepted presentation and controls fit a zoom-sized viewport', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await page.getByRole('button', { name: 'Quay ký hiệu', exact: true }).click();
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Kết thúc', exact: true }).click();
  await page.getByRole('button', { name: 'Quay lại', exact: true }).waitFor();
  const markup = renderToStaticMarkup(createElement(RecognitionOverlay, { result: { clip: new Blob(['fixture']), accepted: true, text: 'Giấy tờ (giấy)', classLabel: 'GIAY_TO_HCM_1', confidence: .92 } }));
  await page.evaluate(markup => document.querySelector('.camera-dock')!.insertAdjacentHTML('afterbegin', markup), markup);
  for (const viewport of [page.viewportSize()!, { width: 320, height: 180 }]) {
    await page.setViewportSize(viewport);
    await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Độ tin cậy 92%');
    const camera = (await page.locator('.camera-viewport').boundingBox())!;
    const controls = (await page.locator('.capture-controls').boundingBox())!;
    const translation = (await page.locator('.translation-panel').boundingBox())!;
    expect(translation.y).toBeGreaterThanOrEqual(camera.y);
    expect(translation.y + translation.height).toBeLessThanOrEqual(controls.y);
    expect(controls.y + controls.height).toBeLessThanOrEqual(camera.y + camera.height);
    expect(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight && document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});

test('automatic recording stop preserves focus on a surviving control', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await page.getByRole('button', { name: 'Quay ký hiệu', exact: true }).click();
  const cameraOff = page.getByRole('button', { name: 'Tắt camera', exact: true });
  await cameraOff.focus();
  await expect(page.getByRole('status')).toHaveText('Đã quay xong', { timeout: 8000 });
  await expect(cameraOff).toBeFocused();
});

test('help supports Escape, focus restoration and reduced motion', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const help = page.getByRole('button', { name: 'Hướng dẫn', exact: true });
  await help.click();
  const dialog = page.getByRole('dialog', { name: 'Quay một ký hiệu rõ ràng' });
  await expect(dialog).toBeVisible();
  const close = page.getByRole('button', { name: 'Đóng hướng dẫn' });
  await expect(close).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(help).toBeFocused();
  await expect(help).toHaveCSS('transition-duration', '0s');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('denied camera permission shows a recoverable error', async ({ page, context }) => {
  await context.clearPermissions();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Browser.setPermission', { permission: { name: 'camera' }, setting: 'denied', origin: 'http://127.0.0.1:4173' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Chưa có quyền sử dụng camera');
  await expect(page.getByRole('button', { name: 'Thử lại', exact: true })).toBeFocused();
  await expectInCameraLayout(page);
});
