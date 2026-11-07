// apps/web/src/features/recognition/cameraSession.ts - Quan ly tai nguyen camera va mot doan quay trong bo nho.
import type { CameraError } from '../../content/vi';

export const captureLimits = {
  minimumDurationMs: 300, maximumCaptureMs: 5000, maximumDurationMs: 6000,
  maximumBytes: 10 * 1024 * 1024, chunkIntervalMs: 250, finalizeTimeoutMs: 3000,
} as const;
const webmTypes = ['video/webm;codecs=vp8', 'video/webm;codecs=vp9', 'video/webm'];

export type CameraView =
  | { phase: 'idle' | 'permission' | 'preview' | 'recording' | 'stopping' }
  | { phase: 'captured'; clip: Blob; durationMs: number }
  | { phase: 'error'; error: CameraError };

interface ActiveCapture {
  recorder: MediaRecorder;
  chunks: Blob[];
  bytes: number;
  startedAt: number;
  stoppedAt: number | null;
  dispose: () => void;
}

function permissionError(cause: unknown): CameraError {
  const name = cause instanceof Error || cause instanceof DOMException ? cause.name : '';
  if (name === 'NotAllowedError' || name === 'SecurityError') return 'denied';
  if (name === 'NotFoundError' || name === 'OverconstrainedError') return 'unavailable';
  if (name === 'NotReadableError') return 'busy';
  return 'unknown';
}

export class CameraSession {
  view: CameraView = { phase: 'idle' };
  private generation = 0;
  private stream: MediaStream | null = null;
  private video: HTMLVideoElement | null = null;
  private capture: ActiveCapture | null = null;
  private captureTimer: ReturnType<typeof setTimeout> | undefined;
  private finalizeTimer: ReturnType<typeof setTimeout> | undefined;
  private disposeTracks: () => void = () => {};
  private readonly onChange: (view: CameraView) => void;

  constructor(onChange: (view: CameraView) => void) { this.onChange = onChange; }

  private publish(view: CameraView) { this.view = view; this.onChange(view); }

  async enable(video: HTMLVideoElement | null) {
    if (this.view.phase !== 'idle' && this.view.phase !== 'error') return;
    if (!globalThis.isSecureContext) { this.fail('insecure'); return; }
    if (!navigator.mediaDevices?.getUserMedia || !video) { this.fail('unavailable'); return; }
    this.release();
    const generation = this.generation;
    this.publish({ phase: 'permission' });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
      });
      if (generation !== this.generation) { stream.getTracks().forEach(track => track.stop()); return; }
      await this.attach({ stream, video, generation });
    } catch (cause) {
      if (generation === this.generation) this.fail(permissionError(cause));
    }
  }

  private async attach({ stream, video, generation }: { stream: MediaStream; video: HTMLVideoElement; generation: number }) {
    this.stream = stream;
    const tracks = stream.getVideoTracks();
    if (!tracks.length || tracks.some(track => track.readyState !== 'live')) { this.fail('disconnected'); return; }
    const onEnded = () => { if (generation === this.generation) this.fail('disconnected'); };
    tracks.forEach(track => track.addEventListener('ended', onEnded));
    this.disposeTracks = () => tracks.forEach(track => track.removeEventListener('ended', onEnded));
    this.video = video;
    video.srcObject = stream;
    await video.play();
    if (generation === this.generation) this.publish({ phase: 'preview' });
  }

  record() {
    if (this.view.phase !== 'preview' && this.view.phase !== 'captured') return;
    if (!this.stream || this.capture) return;
    try {
      const mimeType = typeof MediaRecorder !== 'undefined' && typeof MediaRecorder.isTypeSupported === 'function'
        ? webmTypes.find(type => MediaRecorder.isTypeSupported(type)) : undefined;
      if (!mimeType) { this.fail('recordingUnsupported'); return; }
      const recorder = new MediaRecorder(this.stream, { mimeType });
      const capture: ActiveCapture = { recorder, chunks: [], bytes: 0, startedAt: performance.now(), stoppedAt: null, dispose: () => {} };
      this.capture = capture;
      this.listen(capture);
      this.publish({ phase: 'recording' });
      recorder.start(captureLimits.chunkIntervalMs);
      if (this.capture === capture) this.captureTimer = setTimeout(() => this.stop(), captureLimits.maximumCaptureMs);
    } catch { this.fail('recordingFailed'); }
  }

  private listen(capture: ActiveCapture) {
    const { recorder } = capture;
    const onData = (event: BlobEvent) => this.appendChunk(capture, event.data);
    const onStop = () => this.finish(capture);
    const onError = () => { if (this.capture === capture) this.fail('recordingFailed'); };
    recorder.addEventListener('dataavailable', onData);
    recorder.addEventListener('stop', onStop);
    recorder.addEventListener('error', onError);
    capture.dispose = () => {
      recorder.removeEventListener('dataavailable', onData);
      recorder.removeEventListener('stop', onStop);
      recorder.removeEventListener('error', onError);
      capture.chunks.length = 0;
    };
  }

  private appendChunk(capture: ActiveCapture, chunk: Blob) {
    if (this.capture !== capture || !chunk.size) return;
    capture.bytes += chunk.size;
    if (capture.bytes > captureLimits.maximumBytes) { this.fail('tooLarge'); return; }
    capture.chunks.push(chunk);
  }

  stop() {
    const capture = this.capture;
    if (!capture || capture.stoppedAt !== null || capture.recorder.state !== 'recording') return;
    clearTimeout(this.captureTimer);
    capture.stoppedAt = performance.now();
    if (capture.stoppedAt - capture.startedAt > captureLimits.maximumDurationMs) { this.fail('tooLong'); return; }
    this.publish({ phase: 'stopping' });
    this.finalizeTimer = setTimeout(() => {
      if (this.capture === capture) this.fail('recordingFailed');
    }, captureLimits.finalizeTimeoutMs);
    try { capture.recorder.stop(); } catch { this.fail('recordingFailed'); }
  }

  private finish(capture: ActiveCapture) {
    if (this.capture !== capture) return;
    if (capture.stoppedAt === null) { this.fail('recordingFailed'); return; }
    const durationMs = capture.stoppedAt - capture.startedAt;
    if (durationMs < captureLimits.minimumDurationMs) { this.fail('tooShort'); return; }
    if (!capture.bytes) { this.fail('recordingFailed'); return; }
    const clip = new Blob(capture.chunks, { type: capture.recorder.mimeType });
    if (!clip.type.startsWith('video/webm')) { this.fail('recordingUnsupported'); return; }
    this.discardCapture();
    this.publish({ phase: 'captured', clip, durationMs });
  }

  cancel() {
    if (this.view.phase === 'permission') { this.reset(); return; }
    if (!this.stream || this.view.phase === 'error') return;
    if (!this.discardCapture()) { this.fail('recordingFailed'); return; }
    this.publish({ phase: 'preview' });
  }

  reset() { this.release(); this.publish({ phase: 'idle' }); }

  private discardCapture() {
    clearTimeout(this.captureTimer);
    clearTimeout(this.finalizeTimer);
    const capture = this.capture;
    this.capture = null;
    if (!capture) return true;
    capture.dispose();
    if (capture.recorder.state !== 'inactive') {
      try { capture.recorder.stop(); }
      catch { return false; }
    }
    return true;
  }

  release() {
    this.generation += 1;
    this.discardCapture();
    this.disposeTracks(); this.disposeTracks = () => {};
    this.stream?.getTracks().forEach(track => track.stop());
    this.stream = null;
    if (this.video) this.video.srcObject = null;
    this.video = null;
    this.view = { phase: 'idle' };
  }

  private fail(error: CameraError) { this.release(); this.publish({ phase: 'error', error }); }
}
