// apps/web/tests/e2e/recognition-negative-paths.spec.ts - T047: cac luong loi voi camera gia va backend that.
import { expect, test } from '@playwright/test';
import { BACKENDS, E2E_WEB_PORT } from '../../playwright.e2e.config';
import { captureClip, collectPageErrors, collectPredictionPosts, corruptMultipart, useBackend } from './helpers';

test('T047 denied camera permission shows recoverable guidance and never uploads', async ({ page, context }) => {
  const posts = collectPredictionPosts(page);
  await useBackend(page, BACKENDS.accepted);
  await context.clearPermissions();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Browser.setPermission', {
    permission: { name: 'camera' }, setting: 'denied', origin: `http://127.0.0.1:${E2E_WEB_PORT}`,
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Chưa có quyền sử dụng camera');
  await expect(page.getByRole('button', { name: 'Thử lại', exact: true })).toBeVisible();
  expect(posts).toHaveLength(0);
});

test('T047 low-confidence fixture is rejected, not translated, and not added to the transcript', async ({ page }) => {
  const errors = collectPageErrors(page);
  await useBackend(page, BACKENDS.lowConfidence);
  await page.goto('/');
  await captureClip(page);
  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/v1/predictions'));
  await page.getByRole('button', { name: 'Gửi nhận diện' }).click();
  const body = await (await responsePromise).json();
  expect(body.accepted).toBe(false);
  expect(body.classLabel).toBeNull();
  await expect(page.getByText('Chưa nhận diện được ký hiệu. Hãy quay một ký hiệu mới.')).toBeVisible();
  await expect(page.locator('.transcript-text')).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('T047 corrupt clip gets a stable Vietnamese error from the real API, then an explicit retry succeeds', async ({ page }) => {
  const posts = collectPredictionPosts(page);
  await useBackend(page, BACKENDS.accepted);
  let corruptOnce = true;
  await page.route('**/api/v1/predictions', route => {
    const target = new URL(route.request().url());
    target.host = `127.0.0.1:${BACKENDS.accepted}`;
    if (!corruptOnce) return route.continue({ url: target.toString() });
    corruptOnce = false;
    const { contentType, body } = corruptMultipart();
    return route.continue({
      url: target.toString(), postData: body,
      headers: { ...route.request().headers(), 'content-type': contentType },
    });
  });
  await page.goto('/');
  await captureClip(page);

  const first = page.waitForResponse(response => response.url().endsWith('/api/v1/predictions'));
  await page.getByRole('button', { name: 'Gửi nhận diện' }).click();
  const firstResponse = await first;
  expect([415, 422]).toContain(firstResponse.status());
  const envelope = await firstResponse.json();
  const alert = page.getByRole('alert');
  await expect(alert).toBeVisible();
  await expect(alert).not.toContainText(envelope.message); // khong render message tho cua server
  await expect(alert).not.toContainText(envelope.code);

  const second = page.waitForResponse(response => response.url().endsWith('/api/v1/predictions'));
  await page.getByRole('button', { name: 'Gửi nhận diện' }).click(); // chi gui lai khi nguoi dung chu dong
  expect((await second).status()).toBe(200);
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Cảm ơn');
  expect(posts).toHaveLength(2);
});

test('T047 service busy (control response) offers an explicit retry that reaches the real backend', async ({ page }) => {
  // FastAPI fixture xu ly qua nhanh de tao tranh chap that; 503 SERVICE_BUSY la phan hoi dieu khien theo contract.
  await useBackend(page, BACKENDS.accepted);
  let busyOnce = true;
  await page.route('**/api/v1/predictions', route => {
    if (busyOnce) {
      busyOnce = false;
      return route.fulfill({
        status: 503,
        headers: { 'Retry-After': '3', 'X-Request-ID': '6f1e3c1a-2b4d-4e5f-8a9b-0c1d2e3f4a5b' },
        json: { code: 'SERVICE_BUSY', message: 'raw server text', requestId: '6f1e3c1a-2b4d-4e5f-8a9b-0c1d2e3f4a5b' },
      });
    }
    const target = new URL(route.request().url());
    target.host = `127.0.0.1:${BACKENDS.accepted}`;
    return route.continue({ url: target.toString() });
  });
  await page.goto('/');
  await captureClip(page);
  await page.getByRole('button', { name: 'Gửi nhận diện' }).click();
  await expect(page.getByRole('alert')).toContainText('Dịch vụ đang bận');
  await expect(page.getByRole('alert')).not.toContainText('raw server text');
  const retried = page.waitForResponse(response => response.url().endsWith('/api/v1/predictions'));
  await page.getByRole('button', { name: 'Gửi nhận diện' }).click();
  expect((await retried).status()).toBe(200);
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Cảm ơn');
});

test('T047 degraded backend (no artifact) blocks upload and shows recoverable guidance', async ({ page }) => {
  const posts = collectPredictionPosts(page);
  await useBackend(page, BACKENDS.degraded);
  const modelInfo = page.waitForResponse(response => response.url().endsWith('/api/v1/model-info'));
  await page.goto('/');
  expect((await modelInfo).status()).toBe(503);
  await captureClip(page);
  await expect(page.getByText('Chưa kết nối được dịch vụ nhận diện. Bạn vẫn có thể quay ký hiệu.')).toBeVisible();
  expect(posts).toHaveLength(0);
});
