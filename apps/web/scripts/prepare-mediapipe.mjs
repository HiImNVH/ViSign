// apps/web/scripts/prepare-mediapipe.mjs - Chuan bi tai nguyen MediaPipe cho che do dich truc tiep (T105).
// Chep WASM tu @mediapipe/tasks-vision va tai hai model phat hien (tay, pose lite) co kiem SHA-256 vao
// public/mediapipe/ de phuc vu cung origin (CSP 'self'). Thu muc nay khong commit; chay lai an toan.
import { createHash } from 'node:crypto';
import { copyFile, mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const target = join(root, 'public', 'mediapipe');
const wasmSource = join(root, 'node_modules', '@mediapipe', 'tasks-vision', 'wasm');
const wasmFiles = ['vision_wasm_internal.js', 'vision_wasm_internal.wasm',
  'vision_wasm_nosimd_internal.js', 'vision_wasm_nosimd_internal.wasm'];
const models = [
  {
    name: 'hand_landmarker.task',
    url: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
    sha256: 'fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1',
  },
  {
    name: 'pose_landmarker_lite.task',
    url: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
    sha256: '59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a',
  },
];

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const exists = path => stat(path).then(() => true, () => false);

await mkdir(join(target, 'wasm'), { recursive: true });
await mkdir(join(target, 'models'), { recursive: true });
for (const file of wasmFiles) await copyFile(join(wasmSource, file), join(target, 'wasm', file));

for (const model of models) {
  const path = join(target, 'models', model.name);
  if (await exists(path) && sha256(await readFile(path)) === model.sha256) continue;
  const response = await fetch(model.url);
  if (!response.ok) throw new Error(`Khong tai duoc ${model.name}: HTTP ${response.status}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  const digest = sha256(bytes);
  if (digest !== model.sha256) throw new Error(`Sai SHA-256 cho ${model.name}: ${digest}`);
  await writeFile(path, bytes);
}
console.log('MediaPipe assets ready in public/mediapipe');
