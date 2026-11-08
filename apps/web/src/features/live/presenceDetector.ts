// apps/web/src/features/live/presenceDetector.ts - Phat hien nguoi, mat va tay tren trinh duyet (T105).
// Chi dung de quyet dinh khi nao bat dau/ket thuc mot doan ky hieu; nhan dien van chay o API. MediaPipe Tasks
// (WASM + model) phuc vu cung origin tu /mediapipe/ nen khop CSP 'self'.
import type { HandLandmarker, NormalizedLandmark, PoseLandmarker } from '@mediapipe/tasks-vision';

export interface PresenceFrame {
  person: boolean;
  face: boolean;
  hands: number;
  /** Do dich chuyen trung binh cua tay so voi khung truoc, toa do chuan hoa 0..1. */
  motion: number;
}

export interface PresenceDetector {
  detect(video: HTMLVideoElement, nowMs: number): PresenceFrame;
  close(): void;
}

export type PresenceDetectorFactory = () => Promise<PresenceDetector>;

const ASSET_ROOT = '/mediapipe';
// Diem pose cua mui va hai mat (BlazePose): du de xac nhan khuon mat nhin vao camera
const FACE_POINTS = [0, 2, 5];
// Co tay, ngon cai va ngon tro: dai dien chuyen dong ban tay
const HAND_POINTS = [0, 4, 8];
const VISIBLE = 0.5;

const inFrame = (point: NormalizedLandmark) => point.x >= 0 && point.x <= 1 && point.y >= 0 && point.y <= 1;

function handPoints(hands: NormalizedLandmark[][]): { x: number; y: number }[] {
  return hands.flatMap(hand => HAND_POINTS.map(index => hand[index]).filter(point => point !== undefined))
    .map(point => ({ x: point.x, y: point.y }));
}

/** Tinh chuyen dong: so luong tay thay doi duoc coi la chuyen dong ro rang. */
export function handMotion(previous: { x: number; y: number }[] | null, current: { x: number; y: number }[]): number {
  if (!current.length) return 0;
  if (!previous || previous.length !== current.length) return 1;
  let total = 0;
  current.forEach((point, index) => {
    const before = previous[index]!;
    total += Math.hypot(point.x - before.x, point.y - before.y);
  });
  return total / current.length;
}

class MediaPipePresenceDetector implements PresenceDetector {
  private previousHands: { x: number; y: number }[] | null = null;
  private lastTimestamp = -1;

  constructor(private readonly hands: HandLandmarker, private readonly pose: PoseLandmarker) {}

  detect(video: HTMLVideoElement, nowMs: number): PresenceFrame {
    // detectForVideo yeu cau timestamp tang dan
    const timestamp = Math.max(Math.round(nowMs), this.lastTimestamp + 1);
    this.lastTimestamp = timestamp;
    const handResult = this.hands.detectForVideo(video, timestamp);
    const poseResult = this.pose.detectForVideo(video, timestamp);
    const body = poseResult.landmarks[0];
    const face = !!body && FACE_POINTS.every(index => {
      const point = body[index];
      return point !== undefined && (point.visibility ?? 1) >= VISIBLE && inFrame(point);
    });
    const points = handPoints(handResult.landmarks);
    const motion = handMotion(this.previousHands, points);
    this.previousHands = points.length ? points : null;
    return { person: !!body || handResult.landmarks.length > 0, face, hands: handResult.landmarks.length, motion };
  }

  close() { this.hands.close(); this.pose.close(); }
}

/** Ban stub cho kiem thu trinh duyet: window.__VISIGN_PRESENCE_STUB__ tra ve PresenceFrame theo thoi gian. */
type PresenceStub = (nowMs: number) => PresenceFrame;
declare global { interface Window { __VISIGN_PRESENCE_STUB__?: PresenceStub } }

export const createPresenceDetector: PresenceDetectorFactory = async () => {
  const stub = typeof window !== 'undefined' ? window.__VISIGN_PRESENCE_STUB__ : undefined;
  if (stub) return { detect: (_video, nowMs) => stub(nowMs), close: () => {} };
  const { FilesetResolver, HandLandmarker, PoseLandmarker } = await import('@mediapipe/tasks-vision');
  const fileset = await FilesetResolver.forVisionTasks(`${ASSET_ROOT}/wasm`);
  const [hands, pose] = await Promise.all([
    HandLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: `${ASSET_ROOT}/models/hand_landmarker.task`, delegate: 'CPU' },
      runningMode: 'VIDEO', numHands: 2,
    }),
    PoseLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: `${ASSET_ROOT}/models/pose_landmarker_lite.task`, delegate: 'CPU' },
      runningMode: 'VIDEO', numPoses: 1,
    }),
  ]);
  return new MediaPipePresenceDetector(hands, pose);
};
