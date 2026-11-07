// apps/web/tests/browser/cameraFixture.ts - Tao Y4M tong hop lap lai duoc, khong chua hinh anh ca nhan.
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

export function cameraFixture() {
  const directory = resolve(import.meta.dirname, '../../.local/browser-fixtures');
  mkdirSync(directory, { recursive: true });
  const path = resolve(directory, 'camera.y4m');
  const width = 320, height = 240, frames = 30;
  const payload: Buffer[] = [Buffer.from(`YUV4MPEG2 W${width} H${height} F30:1 Ip A1:1 C420jpeg\n`)];
  for (let index = 0; index < frames; index += 1) {
    const frame = Buffer.alloc(width * height * 3 / 2, 128);
    frame.fill(60 + index * 4, 0, width * height);
    payload.push(Buffer.from('FRAME\n'), frame);
  }
  writeFileSync(path, Buffer.concat(payload));
  return path;
}
