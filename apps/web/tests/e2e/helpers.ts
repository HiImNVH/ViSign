// apps/web/tests/e2e/helpers.ts - Tien ich E2E: dich truc tiep voi camera gia (WebM that) va backend FastAPI that.
import { type Page, type Request } from '@playwright/test';
import { installPresenceStub, signOnce, startLive } from '../browser/liveHelpers';

/** Chuyen moi request /api/v1/* toi mot backend FastAPI that; response la response that, khong gia lap. */
export async function useBackend(page: Page, port: number): Promise<void> {
  await page.route('**/api/v1/**', route => {
    const target = new URL(route.request().url());
    target.host = `127.0.0.1:${port}`;
    return route.continue({ url: target.toString() });
  });
}

/** Dich truc tiep: gia lap nguoi dang ky hieu (stub phat hien), camera gia ghi WebM that va tu gui. */
export async function signLive(page: Page, first = true): Promise<void> {
  if (first) await startLive(page);
  await signOnce(page);
}

export { installPresenceStub };

export function collectPredictionPosts(page: Page): Request[] {
  const posts: Request[] = [];
  page.on('request', request => {
    if (request.method() === 'POST' && request.url().endsWith('/api/v1/predictions')) posts.push(request);
  });
  return posts;
}

export function collectPageErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  return errors;
}

/** Than multipart voi mot "clip" khong phai WebM, de backend that tra loi dinh dang. */
export function corruptMultipart(): { contentType: string; body: Buffer } {
  const boundary = '----visign-e2e-corrupt';
  const body = Buffer.concat([
    Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="clip"; filename="clip.webm"\r\n`),
    Buffer.from('Content-Type: video/webm\r\n\r\n'),
    Buffer.from('day khong phai video webm'),
    Buffer.from(`\r\n--${boundary}--\r\n`),
  ]);
  return { contentType: `multipart/form-data; boundary=${boundary}`, body };
}
