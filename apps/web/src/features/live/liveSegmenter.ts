// apps/web/src/features/live/liveSegmenter.ts - Tu cat tung ky hieu tu luong khung hinh (T105).
// Ham thuan, khong phu thuoc DOM: nhan PresenceFrame theo thoi gian, tra ve hanh dong start/stop/discard.
import type { PresenceFrame } from './presenceDetector';

export type Presence = 'none' | 'partial' | 'ready';
export type SegmentAction = 'start' | 'stop' | 'discard' | null;

export const segmenterConfig = {
  /** Chuyen dong toi thieu cua tay de bat dau mot ky hieu. */
  startMotion: 0.012,
  /** Duoi muc nay coi nhu tay dung yen. */
  stillMotion: 0.006,
  /** Tay dung yen (hoac roi khung) lien tuc bao lau thi ket thuc doan. */
  stillMs: 700,
  /** Doan ngan hon bi bo, khong gui (API yeu cau toi thieu 300 ms). */
  minMs: 500,
  /** Cat cung truoc gioi han ghi 5 s cua camera. */
  maxMs: 4500,
} as const;

export function presenceOf(frame: PresenceFrame): Presence {
  if (!frame.person) return 'none';
  return frame.face && frame.hands > 0 ? 'ready' : 'partial';
}

export class LiveSegmenter {
  private recording = false;
  private startedAt = 0;
  private lastActiveAt = 0;

  constructor(private readonly config: typeof segmenterConfig = segmenterConfig) {}

  get isRecording() { return this.recording; }

  reset() { this.recording = false; }

  step(frame: PresenceFrame, nowMs: number): { presence: Presence; action: SegmentAction } {
    const presence = presenceOf(frame);
    const { startMotion, stillMotion, stillMs, minMs, maxMs } = this.config;
    if (!this.recording) {
      if (presence === 'ready' && frame.motion >= startMotion) {
        this.recording = true;
        this.startedAt = nowMs;
        this.lastActiveAt = nowMs;
        return { presence, action: 'start' };
      }
      return { presence, action: null };
    }
    if (frame.hands > 0 && frame.motion >= stillMotion) this.lastActiveAt = nowMs;
    const elapsed = nowMs - this.startedAt;
    if (elapsed >= maxMs) { this.recording = false; return { presence, action: 'stop' }; }
    if (nowMs - this.lastActiveAt >= stillMs) {
      this.recording = false;
      // Do dai co ich la phan co chuyen dong, khong tinh khoang dung yen cuoi doan
      return { presence, action: this.lastActiveAt - this.startedAt >= minMs ? 'stop' : 'discard' };
    }
    return { presence, action: null };
  }
}
