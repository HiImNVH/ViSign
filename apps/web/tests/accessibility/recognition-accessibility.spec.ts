import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const model = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1',
  meanings: ['Xin chào'], acceptanceThreshold: .7,
  macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};

test('T063 keyboard can control capture and gets submission status without an automatic upload', async ({ page }) => {
  let uploads = 0;
  let finishRequest!: () => void;
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
  await page.route('**/api/v1/predictions', async route => {
    uploads++;
    await new Promise<void>(resolve => { finishRequest = resolve; });
    await route.fulfill({ status: 200, json: { requestId: '123e4567-e89b-42d3-a456-426614174000',
      text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: .95,
      accepted: true, modelVersion: model.modelVersion, processingTimeMs: 10 } });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera' }).focus();
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByRole('button', { name: 'Hướng dẫn' })).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByRole('button', { name: 'Lịch sử' })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Hướng dẫn' })).toBeFocused();
  await page.keyboard.press('Tab');
  const enable = page.getByRole('button', { name: 'Bật camera' });
  await expect(enable).toBeFocused();
  await page.keyboard.press('Space');
  await expect(page.getByRole('status')).toHaveText('Camera sẵn sàng');
  await expect(page.getByLabel('Hình ảnh xem trước từ camera')).toBeVisible();
  const record = page.getByRole('button', { name: 'Quay ký hiệu' });
  await expect(record).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('status')).toHaveText('Đang quay ký hiệu');
  const stop = page.getByRole('button', { name: 'Kết thúc' });
  await expect(stop).toBeFocused();
  await page.waitForTimeout(500);
  await page.keyboard.press('Space');
  await expect(page.getByRole('status')).toHaveText('Đã quay xong');
  const focusedControl = page.locator('.capture-controls button:focus');
  await expect(focusedControl).toHaveCount(1);
  await expect(focusedControl).toBeEnabled();
  expect(uploads).toBe(0);
  await page.keyboard.press(await page.getByRole('button', { name: 'Hủy đoạn quay' }).evaluate(
    button => button === document.activeElement) ? 'Shift+Tab' : 'Tab');
  await expect(page.getByRole('button', { name: 'Gửi nhận diện' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect.poll(() => uploads).toBe(1);
  await expect(page.getByRole('status')).toHaveText('Đang nhận diện…');
  finishRequest();
  await expect(page.getByRole('region', { name: 'Văn bản dịch' })).toContainText('Xin chào');
  await expect(page.getByRole('status')).toHaveText('Đã quay xong');
  expect(uploads).toBe(1);
});

test('T063 metadata reconnect restores keyboard focus when retry disappears', async ({ page }) => {
  let metadataCalls = 0;
  await page.route('**/api/v1/model-info', route => {
    metadataCalls++;
    return metadataCalls === 1
      ? route.fulfill({ status: 503, json: { code: 'MODEL_NOT_READY', message: 'private', requestId: 'x' } })
      : route.fulfill({ status: 200, json: model });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Bật camera' }).click();
  await page.getByRole('button', { name: 'Quay ký hiệu' }).click();
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Kết thúc' }).click();
  await expect(page.getByRole('button', { name: 'Thử kết nối lại' })).toBeVisible();
  await page.getByRole('button', { name: 'Thử kết nối lại' }).click();
  await expect(page.getByRole('button', { name: 'Gửi nhận diện' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Quay lại' })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Gửi nhận diện' })).toBeFocused();
});

test('T063 history confirmation, cancellation and clearing keep focus inside dialog', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('visign.translation-history.v1', JSON.stringify({
    schemaVersion: 1,
    entries: [{ requestId: '123e4567-e89b-42d3-a456-426614174000', text: 'Xin chào',
      confidence: .95, modelVersion: 'pilot-v1', createdAt: new Date().toISOString() }],
  })));
  await page.goto('/');
  const trigger = page.getByRole('button', { name: 'Lịch sử' });
  await trigger.focus();
  await page.keyboard.press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Lịch sử bản dịch' });
  await expect(dialog).toBeVisible();
  const clear = dialog.getByRole('button', { name: 'Xoá toàn bộ lịch sử' });
  await clear.focus();
  await page.keyboard.press('Enter');
  const confirm = dialog.getByRole('button', { name: 'Xác nhận xoá' });
  await expect(confirm).toBeFocused();
  await page.keyboard.press('Tab');
  const keep = dialog.getByRole('button', { name: 'Giữ lại' });
  await expect(keep).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(clear).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(confirm).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(dialog).toContainText('Chưa có bản dịch được lưu.');
  await expect(dialog.getByRole('button', { name: 'Đóng lịch sử' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
});

test('T063 exposes camera guidance and passes WCAG axe checks in idle, help and permission error', async ({ page, context }) => {
  await page.goto('/');
  await expect(page.getByRole('region', { name: 'Nhận diện ký hiệu bằng camera' }))
    .toHaveAttribute('aria-describedby', 'camera-privacy');
  await expect(page.getByLabel('Hình ảnh xem trước từ camera')).toHaveAttribute('autoplay', '');
  const idleAudit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(idleAudit.violations).toEqual([]);
  await page.getByRole('button', { name: 'Hướng dẫn' }).click();
  const dialog = page.getByRole('dialog', { name: 'Quay một ký hiệu rõ ràng' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Đóng hướng dẫn' })).toBeFocused();
  const dialogAudit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(dialogAudit.violations).toEqual([]);
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
});

for (const accepted of [true, false]) {
  test(`T063 ${accepted ? 'accepted' : 'rejected'} results remain accessible and announced`, async ({ page }) => {
    await page.route('**/api/v1/model-info', route => route.fulfill({ status: 200, json: model }));
    await page.route('**/api/v1/predictions', route => route.fulfill({ status: 200, json: {
      requestId: '123e4567-e89b-42d3-a456-426614174000', text: accepted ? 'Xin chào' : 'Không nhận diện được',
      classLabel: accepted ? 'XIN_CHAO' : null, confidence: accepted ? .95 : .2,
      accepted, modelVersion: model.modelVersion, processingTimeMs: 10,
    } }));
    await page.goto('/');
    await page.getByRole('button', { name: 'Bật camera' }).click();
    await page.getByRole('button', { name: 'Quay ký hiệu' }).click();
    await page.waitForTimeout(500);
    await page.getByRole('button', { name: 'Kết thúc' }).click();
    await page.getByRole('button', { name: 'Gửi nhận diện' }).click();
    const result = page.getByRole('region', { name: accepted ? 'Văn bản dịch' : 'Kết quả nhận diện' });
    await expect(result).toBeVisible();
    await expect(result).toHaveAttribute('aria-live', 'polite');
    await expect(result).toContainText(accepted ? 'Xin chào' : 'Chưa nhận diện được ký hiệu');
    const audit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    expect(audit.violations).toEqual([]);
    if (!accepted) {
      const retry = result.getByRole('button', { name: 'Quay lại' });
      await expect(retry).toBeFocused();
      await retry.press('Enter');
      await expect(page.getByRole('status')).toHaveText('Đang quay ký hiệu');
    }
  });
}

test('T063 focused camera control outline fits inside a compact landscape viewport', async ({ page }) => {
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
