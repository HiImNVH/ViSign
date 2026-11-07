// apps/web/tests/browser/smoke.spec.ts - Xac nhan entrypoint va CSS trong ban build.
import { expect, test } from '@playwright/test';

test('loads the Vietnamese application shell without runtime errors', async ({ page }) => {
  const runtimeErrors: string[] = [];
  page.on('pageerror', (error) => runtimeErrors.push(error.message));

  const response = await page.goto('/');
  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('ViSign');
  await expect(page.locator('html')).toHaveAttribute('lang', 'vi');
  await expect(page.getByRole('heading', { name: 'ViSign', level: 1 })).toBeVisible();
  await expect(page.getByRole('main')).toHaveCSS('box-sizing', 'border-box');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(runtimeErrors).toEqual([]);
});
