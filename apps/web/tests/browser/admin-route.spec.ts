import { expect, test } from '@playwright/test';

test('T082 opens the internal admin route directly and keeps credentials in memory', async ({ page }) => {
  const runtimeErrors: string[] = [];
  page.on('pageerror', error => runtimeErrors.push(error.message));
  await page.route('**/api/admin/pilot', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ phase: 'idle', runId: null, sampleTotal: 0, accepted: 0 }),
  }));

  const response = await page.goto('/admin/train-model');
  expect(response?.status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Kiểm tra clip và huấn luyện pilot' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Chạy preflight' })).toHaveCount(0);

  await page.getByLabel('Mã admin').fill('test-secret');
  await page.getByRole('button', { name: 'Kết nối' }).click();
  await expect(page.getByText('Chưa có lần chạy pilot')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Chạy preflight' })).toBeVisible();
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([]);
  expect(page.url()).not.toContain('test-secret');
  expect(runtimeErrors).toEqual([]);
});
