import { expect, test } from '@playwright/test';

test('camera and persistent history share desktop space without mobile overflow', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Lịch sử', exact: true })).toHaveCount(0);
  const brand = page.getByRole('heading', { name: 'ViSign', level: 1 });
  await expect(brand).toHaveCSS('font-size', page.viewportSize()!.width <= 380 ? '30px' : '38px');
  await expect(brand).toHaveCSS('color', 'rgb(17, 17, 17)');
  await expect(brand.locator('.brand-i')).toHaveCount(2);
  for (const letter of await brand.locator('.brand-i').all()) {
    await expect(letter).toHaveCSS('color', 'rgb(22, 132, 71)');
  }
  await expect(page.getByText('Ngôn ngữ ký hiệu Việt Nam', { exact: true })).toHaveCount(0);
  const footer = page.locator('.app-footer');
  await expect(footer).toHaveText('© 2026 ViSign · 5HVT | Hackathon · Bản thử nghiệm');
  await expect(footer).toBeVisible();
  const footerBox = (await footer.boundingBox())!;
  expect(footerBox.y + footerBox.height).toBeGreaterThan(page.viewportSize()!.height - 40);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const initial = page.viewportSize()!;
  const sidebar = page.getByRole('complementary', { name: 'Lịch sử bản dịch' });
  if (initial.width >= 1024 && initial.height >= 480) {
    await expect(sidebar).toBeVisible();
    const history = (await sidebar.boundingBox())!;
    const camera = (await page.locator('.camera-viewport').boundingBox())!;
    expect(camera.x + camera.width).toBeLessThan(history.x);
    expect(Math.abs(camera.y - history.y)).toBeLessThan(1);
    expect(Math.abs(camera.height - history.height)).toBeLessThan(1);
  } else await expect(sidebar).toBeHidden();
  await page.setViewportSize({ width: 375, height: 812 });
  await expect(sidebar).toBeHidden();
  await expect(page.getByRole('button', { name: 'Lịch sử', exact: true })).toHaveCount(0);
  await expect(footer).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('sidebar keeps bounded pagination and clear-confirmation focus', async ({ page }) => {
  await page.addInitScript(() => {
    const now = Date.now();
    localStorage.setItem('visign.translation-history.v1', JSON.stringify({ schemaVersion: 1,
      entries: Array.from({ length: 120 }, (_, n) => ({ requestId: `123e4567-e89b-42d3-a456-${(n + 1).toString(16).padStart(12, '0')}`,
        text: `Ký hiệu ${n}`, confidence: .93, modelVersion: 'fixture', createdAt: new Date(now - (120 - n) * 1000).toISOString() })),
    }));
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/');
  const sidebar = page.getByRole('complementary', { name: 'Lịch sử bản dịch' });
  await expect(sidebar.locator('li')).toHaveCount(50);
  await expect(sidebar.locator('li strong').first()).toHaveText('Ký hiệu 119');
  await expect(sidebar.locator('li strong').last()).toHaveText('Ký hiệu 70');
  await expect(sidebar.locator('.history-retention, .history-disclosure')).toHaveCount(0);
  await expect(sidebar).not.toContainText('Độ tin cậy');
  await expect(sidebar).not.toContainText('fixture');
  const first = sidebar.locator('li').first();
  const word = (await first.locator('strong').boundingBox())!;
  const timestamp = (await first.locator('time').boundingBox())!;
  const entryButton = first.locator('.history-entry-button');
  const row = (await entryButton.boundingBox())!;
  const rightPadding = await entryButton.evaluate(element => parseFloat(getComputedStyle(element).paddingRight));
  expect(timestamp.y).toBeGreaterThanOrEqual(word.y + word.height);
  expect(Math.abs(timestamp.x + timestamp.width - (row.x + row.width - rightPadding))).toBeLessThan(2);
  await sidebar.getByRole('button', { name: 'Xem thêm bản dịch cũ' }).click();
  await expect(sidebar.locator('li')).toHaveCount(100);
  await expect(sidebar.locator('li strong').first()).toHaveText('Ký hiệu 119');
  await expect(sidebar.locator('li strong').last()).toHaveText('Ký hiệu 20');
  expect(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight)).toBe(true);
  await sidebar.getByRole('button', { name: 'Xoá toàn bộ lịch sử' }).click();
  await expect(sidebar.getByRole('button', { name: 'Xác nhận xoá' })).toBeFocused();
  await sidebar.getByRole('button', { name: 'Xác nhận xoá' }).click();
  await expect(sidebar).toContainText('Chưa có bản dịch được lưu.');
  await expect(sidebar.getByRole('heading')).toBeFocused();
});
