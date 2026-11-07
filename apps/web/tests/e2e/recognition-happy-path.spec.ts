// apps/web/tests/e2e/recognition-happy-path.spec.ts - T032: camera gia -> WebM that -> FastAPI fixture that.
import { expect, test } from '@playwright/test';
import { BACKENDS } from '../../playwright.e2e.config';
import { captureClip, collectPageErrors, collectPredictionPosts, useBackend } from './helpers';

test('T032 happy path: one explicit upload of a real camera WebM returns the fixture translation', async ({ page }) => {
  const errors = collectPageErrors(page);
  const posts = collectPredictionPosts(page);
  await useBackend(page, BACKENDS.accepted);
  await page.goto('/');

  await captureClip(page);
  expect(posts).toHaveLength(0); // quay xong chua tu dong gui

  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/v1/predictions'));
  await page.getByRole('button', { name: 'Gửi nhận diện' }).click();
  const response = await responsePromise;

  // Response that tu FastAPI: request ID header trung voi body, khong co landmark/frame
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.accepted).toBe(true);
  expect(response.headers()['x-request-id']).toBe(body.requestId);
  expect(Object.keys(body)).not.toContain('landmarks');

  // Request la multipart chua clip WebM do MediaRecorder tao
  expect(posts).toHaveLength(1);
  const [upload] = posts;
  if (!upload) throw new Error('Expected one prediction upload');
  expect(upload.headers()['content-type']).toContain('multipart/form-data');
  // Chu ky EBML 1A 45 DF A3 o dau file WebM do MediaRecorder tao
  expect(upload.postDataBuffer()?.includes(Buffer.from([0x1a, 0x45, 0xdf, 0xa3]))).toBe(true);

  const result = page.getByRole('region', { name: 'Văn bản dịch' });
  await expect(result).toContainText('Cảm ơn');
  await expect(result.getByRole('note')).toContainText('chưa sẵn sàng demo');
  await expect(page.locator('.transcript-text')).toHaveText('Cảm ơn');
  expect(errors).toEqual([]);
});
