// apps/web/tests/recognition/cameraSession.test.ts - Kiem tra quyen, vong doi va gioi han camera.
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { CameraSession, captureLimits } from '../../src/features/recognition/cameraSession';

class FakeRecorder extends EventTarget {
  static instances: FakeRecorder[] = [];
  static isTypeSupported = vi.fn(() => true);
  state = 'inactive';
  mimeType = 'video/webm;codecs=vp8';
  start = vi.fn(() => { this.state = 'recording'; });
  stop = vi.fn(() => { this.state = 'inactive'; });
  constructor() { super(); FakeRecorder.instances.push(this); }
  chunk(size = 8) {
    const event = new Event('dataavailable');
    Object.defineProperty(event, 'data', { value: new Blob([new Uint8Array(size)]) });
    this.dispatchEvent(event);
  }
  finish() { this.dispatchEvent(new Event('stop')); }
}

const track = Object.assign(new EventTarget(), {
  readyState: 'live', stop: vi.fn(),
});
const stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
const getUserMedia = vi.fn<() => Promise<MediaStream>>();
let session: CameraSession;
let video: HTMLVideoElement;

beforeEach(() => {
  vi.useFakeTimers();
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  FakeRecorder.instances = [];
  FakeRecorder.isTypeSupported.mockReturnValue(true);
  track.readyState = 'live'; track.stop.mockClear();
  getUserMedia.mockReset().mockResolvedValue(stream);
  vi.stubGlobal('isSecureContext', true);
  vi.stubGlobal('MediaRecorder', FakeRecorder);
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } });
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  video = document.createElement('video');
  session = new CameraSession(vi.fn());
});

afterEach(() => { session.release(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers(); });

async function start() {
  await session.enable(video);
  session.record();
  const recorder = FakeRecorder.instances.at(-1);
  if (!recorder) throw new Error('Recorder not created');
  vi.advanceTimersByTime(500);
  return recorder;
}

test('preview requires explicit permission, requests no audio and does not record', async () => {
  expect(getUserMedia).not.toHaveBeenCalled();
  await session.enable(video);
  expect(getUserMedia).toHaveBeenCalledWith(expect.objectContaining({ audio: false }));
  expect(video.srcObject).toBe(stream);
  expect(session.view.phase).toBe('preview');
  expect(FakeRecorder.instances).toHaveLength(0);
});

test('duplicate enable calls create only one permission request', async () => {
  await Promise.all([session.enable(video), session.enable(video)]);
  expect(getUserMedia).toHaveBeenCalledTimes(1);
});

test('denied permission has stable copy and allows retry', async () => {
  getUserMedia.mockRejectedValueOnce(new DOMException('private detail', 'NotAllowedError'));
  await session.enable(video);
  expect(session.view).toMatchObject({ phase: 'error', error: 'denied' });
  await session.enable(video);
  expect(session.view.phase).toBe('preview');
});

test('a cancelled permission request releases a late stream without attaching it', async () => {
  let resolveStream!: (stream: MediaStream) => void;
  getUserMedia.mockReturnValueOnce(new Promise(resolve => { resolveStream = resolve; }));
  const pending = session.enable(video);
  session.cancel(); resolveStream(stream); await pending;
  expect(track.stop).toHaveBeenCalled();
  expect(video.srcObject).toBeFalsy();
  expect(session.view.phase).toBe('idle');
});

test('reset during playback keeps a late play completion from reopening the camera', async () => {
  let resolvePlay!: () => void;
  vi.mocked(video.play).mockReturnValueOnce(new Promise(resolve => { resolvePlay = resolve; }));
  const pending = session.enable(video);
  await Promise.resolve(); session.reset(); resolvePlay(); await pending;
  expect(session.view.phase).toBe('idle');
  expect(video.srcObject).toBeNull();
  expect(track.stop).toHaveBeenCalled();
});

test('playback rejection releases camera', async () => {
  vi.mocked(video.play).mockRejectedValueOnce(new Error('private detail'));
  await session.enable(video);
  expect(session.view).toMatchObject({ phase: 'error', error: 'unknown' });
  expect(track.stop).toHaveBeenCalled();
});

test('stop waits for final data and exposes exactly one nonempty clip', async () => {
  const recorder = await start();
  session.record(); expect(FakeRecorder.instances).toHaveLength(1);
  session.stop(); session.stop();
  expect(recorder.stop).toHaveBeenCalledTimes(1);
  expect(session.view.phase).toBe('stopping');
  recorder.chunk(12); recorder.finish();
  expect(session.view.phase).toBe('captured');
  if (session.view.phase !== 'captured') throw new Error('Missing captured clip');
  expect(session.view.clip.size).toBe(12);
  expect(session.view.clip.type).toBe(recorder.mimeType);
  expect(session.view.durationMs).toBe(500);
  recorder.chunk(5); recorder.finish();
  expect(session.view.clip.size).toBe(12);
});

test('cancelling during finalization ignores final events and retains preview', async () => {
  const recorder = await start(); session.stop(); session.cancel();
  recorder.chunk(); recorder.finish();
  expect(session.view.phase).toBe('preview');
  expect(track.stop).not.toHaveBeenCalled();
});

test('old recorder callbacks cannot replace a newer capture', async () => {
  const recorder = await start(); session.cancel(); session.record();
  recorder.chunk(); recorder.finish();
  expect(session.view.phase).toBe('recording');
});

test('discarding a captured clip returns to preview', async () => {
  const recorder = await start(); session.stop(); recorder.chunk(); recorder.finish();
  session.cancel(); expect(session.view).toEqual({ phase: 'preview' });
});

test('safety cap stops recording at five seconds', async () => {
  const recorder = await start();
  vi.advanceTimersByTime(captureLimits.maximumCaptureMs - 500);
  expect(recorder.stop).toHaveBeenCalledTimes(1);
  recorder.chunk(); recorder.finish(); expect(session.view.phase).toBe('captured');
});

test('too-short clip is discarded', async () => {
  await session.enable(video); session.record(); session.stop();
  const recorder = FakeRecorder.instances[0]!; recorder.chunk(); recorder.finish();
  expect(session.view).toMatchObject({ phase: 'error', error: 'tooShort' });
});

test('empty clip and missing stop event fail closed', async () => {
  const recorder = await start(); session.stop(); recorder.finish();
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
  const nextRecorder = await start(); session.stop(); nextRecorder.chunk();
  vi.advanceTimersByTime(captureLimits.finalizeTimeoutMs);
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
});

test('byte limit discards chunks and stops the stream', async () => {
  const recorder = await start(); recorder.chunk(captureLimits.maximumBytes + 1);
  expect(session.view).toMatchObject({ phase: 'error', error: 'tooLarge' });
  expect(track.stop).toHaveBeenCalled();
});

test('unexpected recorder stop does not publish a clip', async () => {
  const recorder = await start(); recorder.chunk(); recorder.finish();
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
});

test('device disconnection clears capture and camera resources', async () => {
  const recorder = await start(); track.dispatchEvent(new Event('ended'));
  recorder.chunk(); recorder.finish();
  expect(session.view).toMatchObject({ phase: 'error', error: 'disconnected' });
  expect(video.srcObject).toBeNull();
});

test('unsupported recorder format still permits preview', async () => {
  FakeRecorder.isTypeSupported.mockReturnValue(false);
  await session.enable(video); expect(session.view.phase).toBe('preview');
  session.record(); expect(session.view).toMatchObject({ phase: 'error', error: 'recordingUnsupported' });
});

test.each(['insecure', 'unavailable'] as const)('%s camera environment fails safely', async environment => {
  if (environment === 'insecure') vi.stubGlobal('isSecureContext', false);
  else Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: undefined });
  await session.enable(video);
  expect(session.view).toMatchObject({ phase: 'error', error: environment });
  expect(getUserMedia).not.toHaveBeenCalled();
});

test('release clears resources and invalidates pending recorder events', async () => {
  const recorder = await start(); session.release(); recorder.chunk(); recorder.finish();
  expect(track.stop).toHaveBeenCalled(); expect(video.srcObject).toBeNull();
  expect(session.view.phase).toBe('idle'); expect(vi.getTimerCount()).toBe(0);
});

test.each(['NotFoundError', 'OverconstrainedError', 'NotReadableError'])('maps %s without exposing device details', async name => {
  getUserMedia.mockRejectedValueOnce(new DOMException('private detail', name));
  await session.enable(video);
  expect(session.view).toMatchObject({ phase: 'error', error: name === 'NotReadableError' ? 'busy' : 'unavailable' });
});

test('an already-ended device never enters preview', async () => {
  track.readyState = 'ended'; await session.enable(video);
  expect(session.view).toMatchObject({ phase: 'error', error: 'disconnected' });
});

test('recorder error and stop failure both release the stream', async () => {
  let recorder = await start(); recorder.dispatchEvent(new Event('error'));
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
  recorder = await start(); recorder.stop.mockImplementation(() => { throw new DOMException('stop failed'); });
  session.cancel(); expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
  expect(video.srcObject).toBeNull();
});

test('synchronous recorder start failure never announces recording and logs no private error message', async () => {
  const phases: string[] = [];
  session = new CameraSession(view => phases.push(view.phase));
  class StartFailureRecorder extends FakeRecorder {
    constructor() {
      super();
      this.start.mockImplementation(() => { throw new DOMException('private device detail', 'NotReadableError'); });
    }
  }
  vi.stubGlobal('MediaRecorder', StartFailureRecorder);
  await session.enable(video);
  session.record();
  expect(phases).not.toContain('recording');
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
  expect(track.stop).toHaveBeenCalled();
  const warning = vi.mocked(console.warn).mock.calls.at(-1);
  expect(warning).toEqual(['MediaRecorder capture failed', expect.objectContaining({
    stage: 'start', errorName: 'NotReadableError', recorderState: 'inactive',
    chunkCount: 0, byteCount: 0, videoTrackStates: ['live'],
  })]);
  expect(JSON.stringify(warning)).not.toContain('private device detail');
});

test('asynchronous named recorder error is diagnosed and late events are ignored', async () => {
  const recorder = await start();
  const error = new Event('error');
  Object.defineProperty(error, 'error', { value: new DOMException('private message', 'NotSupportedError') });
  recorder.dispatchEvent(error);
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
  expect(vi.mocked(console.warn)).toHaveBeenCalledWith('MediaRecorder capture failed',
    expect.objectContaining({ stage: 'event', errorName: 'NotSupportedError' }));
  expect(JSON.stringify(vi.mocked(console.warn).mock.calls)).not.toContain('private message');
  const warningCount = vi.mocked(console.warn).mock.calls.length;
  recorder.chunk(); recorder.finish(); recorder.dispatchEvent(error);
  expect(vi.mocked(console.warn)).toHaveBeenCalledTimes(warningCount);
  expect(session.view.phase).toBe('error');
});

test('recorder changing to inactive before stop fails instead of trapping the UI in recording', async () => {
  const recorder = await start();
  recorder.state = 'inactive';
  session.stop();
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingFailed' });
  expect(vi.mocked(console.warn)).toHaveBeenCalledWith('MediaRecorder capture failed',
    expect.objectContaining({ stage: 'unexpected-state', recorderState: 'inactive' }));
  expect(vi.getTimerCount()).toBe(0);
});

test('missing MediaRecorder does not prevent preview', async () => {
  vi.stubGlobal('MediaRecorder', undefined); await session.enable(video);
  expect(session.view.phase).toBe('preview'); session.record();
  expect(session.view).toMatchObject({ phase: 'error', error: 'recordingUnsupported' });
});

test('a delayed stop past the allowed envelope discards the clip', async () => {
  await session.enable(video); session.record();
  vi.setSystemTime(Date.now() + 7000);
  vi.spyOn(performance, 'now').mockReturnValue(captureLimits.maximumDurationMs + 10000);
  session.stop(); expect(session.view).toMatchObject({ phase: 'error', error: 'tooLong' });
});
