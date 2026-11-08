// apps/web/tests/browser/liveHelpers.ts - Gia lap nguoi/mat/tay cho kiem thu dich truc tiep (T106).
// Camera gia cua Chromium khong co nguoi nen thay bo phat hien bang stub; MediaRecorder van ghi WebM that.
import { expect, type Page } from '@playwright/test';

type Scene = 'none' | 'partial' | 'ready';

declare global {
  interface Window {
    __visignScene?: Scene;
    __visignSignUntil?: number;
  }
}

/** Phai goi truoc page.goto. Mac dinh: khong co nguoi. */
export async function installPresenceStub(page: Page, scene: Scene = 'none') {
  await page.addInitScript(initial => {
    window.__visignScene = initial;
    window.__VISIGN_PRESENCE_STUB__ = now => {
      const scene = window.__visignScene ?? 'none';
      const signing = scene === 'ready' && now < (window.__visignSignUntil ?? 0);
      return {
        person: scene !== 'none', face: scene === 'ready', hands: scene === 'ready' ? 2 : 0,
        motion: signing ? .05 : 0,
      };
    };
  }, scene);
}

export async function setScene(page: Page, scene: Scene) {
  await page.evaluate(value => { window.__visignScene = value; }, scene);
}

/** Bat camera va cho bo phat hien san sang. */
export async function startLive(page: Page, scene: Scene = 'ready') {
  await page.getByRole('button', { name: 'Bật camera' }).click();
  await expect(page.getByRole('status')).not.toHaveText(/Đang tắt|Đang khởi động/, { timeout: 30_000 });
  await setScene(page, scene);
  if (scene === 'ready') await expect(page.getByRole('status')).toHaveText('Sẵn sàng');
}

/** Gia lap mot ky hieu: tay chuyen dong trong moveMs roi dung yen. */
export async function signOnce(page: Page, moveMs = 1200) {
  await expect(page.getByRole('status')).toHaveText('Sẵn sàng');
  await page.evaluate(ms => { window.__visignSignUntil = performance.now() + ms; }, moveMs);
  await expect(page.getByRole('status')).toHaveText('Đang ghi ký hiệu');
}
