// apps/web/tests/e2e/recognition-happy-path.spec.ts - T032 (dich truc tiep): camera gia -> WebM that -> FastAPI that.
import { expect, test } from '@playwright/test';
import { BACKENDS } from '../../playwright.e2e.config';
import { collectPageErrors, collectPredictionPosts, installPresenceStub, signLive, useBackend } from './helpers';

test('T032 happy path: each live sign uploads one real camera WebM and joins the fixture translation', async ({ page }) => {
  const errors = collectPageErrors(page);
  const posts = collectPredictionPosts(page);
  await installPresenceStub(page);
  await useBackend(page, BACKENDS.accepted);
  await page.goto('/');

  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/v1/predictions'));
  await signLive(page);
  const response = await responsePromise;

  // Response that tu FastAPI: request ID header trung voi body, khong co landmark/frame
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.accepted).toBe(true);
  expect(response.headers()['x-request-id']).toBe(body.requestId);
  expect(Object.keys(body)).not.toContain('landmarks');

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

  // Ky hieu tiep theo khong can bam gi them
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng', { timeout: 5000 });
  await signLive(page, false);
  await expect(page.locator('.transcript-text')).toHaveText('Cảm ơn Cảm ơn');
  expect(posts).toHaveLength(2);
  expect(errors).toEqual([]);
});
