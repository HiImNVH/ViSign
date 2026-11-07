// apps/web/tests/browser/camera.spec.ts - Kiem tra MediaRecorder that voi camera Y4M va khong upload.
import { expect, test } from '@playwright/test';

test('explicitly records and discards a real WebM clip, then releases camera', async ({ page }, testInfo) => {
  const outbound: string[] = [];
  const runtimeErrors: string[] = [];
  page.on('pageerror', error => runtimeErrors.push(error.message));
  page.on('request', request => { if (request.method() !== 'GET' || new URL(request.url()).pathname.startsWith('/api/')) outbound.push(request.url()); });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
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
  await expect(page.getByText(/đã sẵn sàng và chưa được gửi đi/)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('camera-captured.png'), fullPage: true });
  await page.getByRole('button', { name: 'Hủy đoạn quay', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await page.getByRole('button', { name: 'Quay ký hiệu', exact: true }).click();
  await page.getByRole('button', { name: 'Hủy đoạn quay', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await page.getByRole('button', { name: 'Tắt camera', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Camera chưa bật');
  expect(await track.evaluate(track => track.readyState)).toBe('ended');
  expect(await preview.evaluate(video => (video as HTMLVideoElement).srcObject)).toBeNull();
  expect(outbound).toEqual([]);
  expect(runtimeErrors).toEqual([]);
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
});
