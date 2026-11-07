import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import type { ModelInfo, PredictionResponse } from '../../src/types/inference-api';
import { CameraSession, type CameraView } from '../../src/features/recognition/cameraSession';
import * as cameraHook from '../../src/features/recognition/useCameraCapture';
import { useRecognition } from '../../src/features/recognition/useRecognition';
import { InferenceApiError, createInferenceApi } from '../../src/services/inferenceApi';
import { HISTORY_STORAGE_KEY } from '../../src/features/recognition/translationHistory';

type Api = Pick<ReturnType<typeof createInferenceApi>, 'modelInfo' | 'predict'>;
type PredictionReply = Awaited<ReturnType<Api['predict']>>;

const info: ModelInfo = {
  modelVersion: 'fixture-v1', artifactKind: 'fixture', datasetVersion: 'sample',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1', meanings: ['Cảm ơn'],
  acceptanceThreshold: 0.7, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
const accepted: PredictionResponse = {
  requestId: 'prediction-id', text: 'Cảm ơn', classLabel: 'CAM_ON', confidence: 0.93,
  accepted: true, modelVersion: 'fixture-v1', processingTimeMs: 320,
};
const clip = new Blob(['fake video'], { type: 'video/webm' });
let cameraView: CameraView;
let session: CameraSession;
let api: Api;

beforeEach(() => {
  cameraView = { phase: 'idle' };
  session = new CameraSession(vi.fn());
  vi.spyOn(cameraHook, 'useCameraCapture').mockImplementation(() => {
    session.view = cameraView;
    return { view: cameraView, session, videoRef: { current: null } };
  });
  api = {
    modelInfo: vi.fn().mockResolvedValue({ data: info, requestId: 'metadata-id' }),
    predict: vi.fn().mockResolvedValue({ data: accepted, requestId: 'prediction-id' }),
  };
});
afterEach(() => vi.restoreAllMocks());

test('loads artifact metadata and progresses from camera states to explicit submitted result', async () => {
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model).toMatchObject({ status: 'ready', info: { artifactKind: 'fixture' } }));
  expect(hook.result.current.state.phase).toBe('idle');

  for (const phase of ['permission', 'preview', 'recording', 'stopping'] as const) {
    cameraView = { phase };
    hook.rerender();
    expect(hook.result.current.state.phase).toBe(phase);
  }
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  hook.rerender();
  expect(hook.result.current.state.phase).toBe('captured');
  expect(api.predict).not.toHaveBeenCalled();

  let finish!: (reply: PredictionReply) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  let sending!: Promise<void>;
  act(() => { sending = hook.result.current.submit(); void hook.result.current.submit(); });
  expect(hook.result.current.state).toMatchObject({ phase: 'submitting', artifactKind: 'fixture' });
  expect(api.predict).toHaveBeenCalledTimes(1);
  act(() => finish({ data: accepted, requestId: 'prediction-id' }));
  await act(async () => { await sending; });
  expect(hook.result.current.state).toMatchObject({ phase: 'result', requestId: 'prediction-id', result: accepted, artifactKind: 'fixture' });
  expect(hook.result.current.state).not.toHaveProperty('clip'); // do not retain the video blob in result state
  await act(async () => { await hook.result.current.submit(); });
  expect(api.predict).toHaveBeenCalledTimes(1); // no repeat upload of completed clip
});

test('does not send the clip while metadata is unavailable; explicit reload recovers', async () => {
  vi.mocked(api.modelInfo).mockRejectedValueOnce(new InferenceApiError('http', 'meta-request', 503, 'MODEL_NOT_READY'));
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('unavailable'));
  await act(async () => { await hook.result.current.submit(); });
  expect(api.predict).not.toHaveBeenCalled();
  act(() => hook.result.current.reloadModelInfo());
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('result');
});

test('invalidates in-flight submission on recapture, cancellation or camera reset, ignoring late responses', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  let finish!: (reply: PredictionReply) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  let pending!: Promise<void>;
  act(() => { pending = hook.result.current.submit(); });
  const signal = vi.mocked(api.predict).mock.calls[0]![1]?.signal;
  expect(signal?.aborted).toBe(false);
  cameraView = { phase: 'recording' };
  hook.rerender();
  expect(signal?.aborted).toBe(true);
  act(() => finish({ data: accepted, requestId: 'late' }));
  await act(async () => { await pending; });
  expect(hook.result.current.state.phase).toBe('recording');
  cameraView = { phase: 'captured', clip: new Blob(['new'], { type: 'video/webm' }), durationMs: 550 };
  hook.rerender();
  expect(hook.result.current.state.phase).toBe('captured');
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('result');
  act(() => hook.result.current.reset());
  expect(hook.result.current.state.phase).toBe('captured'); // mock view updates on rerender
  cameraView = { phase: 'idle' };
  hook.rerender();
  expect(hook.result.current.state.phase).toBe('idle');
});

test('shows API failure without raw message, and allows a deliberate retry', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  vi.mocked(api.predict).mockRejectedValueOnce(new InferenceApiError('http', 'request-id', 503, 'SERVICE_BUSY'));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state).toMatchObject({ phase: 'error', source: 'api', error: { code: 'SERVICE_BUSY' } });
  expect(api.predict).toHaveBeenCalledTimes(1);
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('result');
  expect(api.predict).toHaveBeenCalledTimes(2);
});

test('returns to an explicit retry after prediction timeout without uploading automatically', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  vi.mocked(api.predict).mockRejectedValueOnce(new InferenceApiError('timeout', 'timeout-id'));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state).toMatchObject({ phase: 'error', error: { kind: 'timeout' } });
  expect(api.predict).toHaveBeenCalledTimes(1);
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('result');
  expect(api.predict).toHaveBeenCalledTimes(2);
});

test('late completion or rejection of request A cannot overwrite or unlock request B', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  let rejectFirst!: (reason: Error) => void;
  let resolveSecond!: (reply: PredictionReply) => void;
  vi.mocked(api.predict)
    .mockImplementationOnce(() => new Promise((_resolve, reject) => { rejectFirst = reject; }))
    .mockImplementationOnce(() => new Promise(resolve => { resolveSecond = resolve; }));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  let first!: Promise<void>;
  act(() => { first = hook.result.current.submit(); });
  act(() => hook.result.current.cancel());
  let second!: Promise<void>;
  act(() => { second = hook.result.current.submit(); });
  act(() => rejectFirst(new InferenceApiError('network', 'late-error')));
  await act(async () => { await first; });
  expect(hook.result.current.state.phase).toBe('submitting');
  act(() => { void hook.result.current.submit(); });
  expect(api.predict).toHaveBeenCalledTimes(2);
  await act(async () => { resolveSecond({ data: accepted, requestId: 'second' }); await second; });
  expect(hook.result.current.state).toMatchObject({ phase: 'result', requestId: 'second' });
});

test('ignores a failure after the camera session changed before React rerenders', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  let reject!: (reason: Error) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise((_resolve, fail) => { reject = fail; }));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  let pending!: Promise<void>;
  act(() => { pending = hook.result.current.submit(); });
  session.view = { phase: 'recording' };
  await act(async () => { reject(new InferenceApiError('network', 'late-error')); await pending; });
  expect(hook.result.current.state.phase).toBe('submitting'); // stale camera render, no new error
  cameraView = { phase: 'recording' };
  hook.rerender();
  expect(hook.result.current.state.phase).toBe('recording');
});

test('late metadata response cannot replace a newer refresh result', async () => {
  let finishOld!: (reply: Awaited<ReturnType<Api['modelInfo']>>) => void;
  vi.mocked(api.modelInfo).mockImplementationOnce(() => new Promise(resolve => { finishOld = resolve; }));
  vi.mocked(api.modelInfo).mockResolvedValueOnce({ data: { ...info, modelVersion: 'current-v2' }, requestId: 'current' });
  const hook = renderHook(() => useRecognition(api));
  act(() => hook.result.current.reloadModelInfo());
  await waitFor(() => expect(hook.result.current.model).toMatchObject({ status: 'ready', info: { modelVersion: 'current-v2' } }));
  await act(async () => { finishOld({ data: info, requestId: 'stale' }); });
  expect(hook.result.current.model).toMatchObject({ status: 'ready', info: { modelVersion: 'current-v2' } });
});

test('discards a result from another model version and reloads metadata without auto retry', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  vi.mocked(api.predict).mockResolvedValueOnce({ data: { ...accepted, modelVersion: 'other-version' }, requestId: 'mismatch-id' });
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state).toMatchObject({ phase: 'error', source: 'api', error: { kind: 'invalid-response' } });
  await waitFor(() => expect(api.modelInfo).toHaveBeenCalledTimes(2));
  expect(api.predict).toHaveBeenCalledTimes(1);
});

test('aborts metadata fetch and prediction on unmount', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  vi.mocked(api.predict).mockImplementation(() => new Promise(() => {}));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  act(() => { void hook.result.current.submit(); });
  const signal = vi.mocked(api.predict).mock.calls[0]![1]?.signal;
  const metaSignal = vi.mocked(api.modelInfo).mock.calls[0]![0]?.signal;
  hook.unmount();
  expect(signal?.aborted).toBe(true);
  expect(metaSignal?.aborted).toBe(true);
});

test('blocks a submission during metadata refresh, including before React rerenders', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));

  let finishMetadata!: (reply: Awaited<ReturnType<Api['modelInfo']>>) => void;
  vi.mocked(api.modelInfo).mockImplementationOnce(() => new Promise(resolve => { finishMetadata = resolve; }));
  act(() => {
    hook.result.current.reloadModelInfo();
    void hook.result.current.submit();
  });
  expect(api.predict).not.toHaveBeenCalled();
  expect(hook.result.current.model.status).toBe('loading');

  await act(async () => { finishMetadata({ data: info, requestId: 'fresh-metadata' }); });
  expect(hook.result.current.model.status).toBe('ready');
  await act(async () => { await hook.result.current.submit(); });
  expect(api.predict).toHaveBeenCalledTimes(1);
});

test('aborts an in-flight upload on pagehide and restores metadata on bfcache return', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  let finishPrediction!: (reply: PredictionReply) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise(resolve => { finishPrediction = resolve; }));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));

  let pending!: Promise<void>;
  act(() => { pending = hook.result.current.submit(); });
  const predictionSignal = vi.mocked(api.predict).mock.calls[0]![1]?.signal;
  act(() => window.dispatchEvent(new Event('pagehide')));
  expect(predictionSignal?.aborted).toBe(true);
  await act(async () => { finishPrediction({ data: accepted, requestId: 'late-result' }); await pending; });
  expect(hook.result.current.state.phase).toBe('captured'); // mocked camera remains unchanged
  await act(async () => { await hook.result.current.submit(); });
  expect(api.predict).toHaveBeenCalledTimes(1); // stale metadata cannot authorize a new upload

  const show = new Event('pageshow');
  Object.defineProperty(show, 'persisted', { value: true });
  act(() => window.dispatchEvent(show));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));
  expect(api.modelInfo).toHaveBeenCalledTimes(2);
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('result');
});

test('cancel and reset immediately abort a pending upload', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  vi.mocked(api.predict).mockImplementation(() => new Promise(() => {}));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));

  act(() => { void hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('submitting');
  const firstSignal = vi.mocked(api.predict).mock.calls[0]![1]?.signal;
  act(() => hook.result.current.cancel());
  expect(firstSignal?.aborted).toBe(true);
  expect(hook.result.current.state.phase).toBe('captured');

  act(() => { void hook.result.current.submit(); });
  const secondSignal = vi.mocked(api.predict).mock.calls[1]![1]?.signal;
  act(() => hook.result.current.reset());
  expect(secondSignal?.aborted).toBe(true);
  cameraView = { phase: 'idle' };
  hook.rerender();
  expect(hook.result.current.state.phase).toBe('idle');
});

test('does not upload or accept a result after the camera session changes before React rerenders', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));

  session.view = { phase: 'recording' };
  await act(async () => { await hook.result.current.submit(); });
  expect(api.predict).not.toHaveBeenCalled();

  session.view = cameraView;
  let finish!: (reply: PredictionReply) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  let pending!: Promise<void>;
  act(() => { pending = hook.result.current.submit(); });
  expect(hook.result.current.state.phase).toBe('submitting');
  session.view = { phase: 'recording' }; // immediate session change, React view is still captured
  await act(async () => { finish({ data: accepted, requestId: 'late' }); await pending; });
  cameraView = { phase: 'recording' };
  hook.rerender();
  expect(hook.result.current.state.phase).toBe('recording');
});

test('uses loaded pilot artifact metadata for rejected results without changing API endpoint', async () => {
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  vi.mocked(api.modelInfo).mockResolvedValueOnce({ data: { ...info, artifactKind: 'pilot', demoReady: false }, requestId: 'pilot-info' });
  vi.mocked(api.predict).mockResolvedValueOnce({
    data: { ...accepted, accepted: false, text: 'Không nhận diện được', classLabel: null, confidence: 0.2 },
    requestId: 'rejected-request',
  });
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model).toMatchObject({ status: 'ready', info: { artifactKind: 'pilot', demoReady: false } }));
  await act(async () => { await hook.result.current.submit(); });
  expect(hook.result.current.state).toMatchObject({
    phase: 'result', artifactKind: 'pilot', requestId: 'rejected-request',
    result: { accepted: false, classLabel: null, text: 'Không nhận diện được' },
  });
  expect(api.predict).toHaveBeenCalledWith(clip, { signal: expect.any(AbortSignal) });
});

test('another tab updates history without interrupting submission, but clearing it aborts an in-flight result', async () => {
  localStorage.removeItem(HISTORY_STORAGE_KEY);
  cameraView = { phase: 'captured', clip, durationMs: 650 };
  let finish!: (reply: PredictionReply) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const hook = renderHook(() => useRecognition(api));
  await waitFor(() => expect(hook.result.current.model.status).toBe('ready'));

  let pending!: Promise<void>;
  act(() => { pending = hook.result.current.submit(); });
  const signal = vi.mocked(api.predict).mock.calls[0]![1]?.signal;
  expect(signal?.aborted).toBe(false);

  const saved = JSON.stringify({ schemaVersion: 1, entries: [{
    requestId: '123e4567-e89b-42d3-a456-426614174001', text: 'Từ tab khác', confidence: .91,
    modelVersion: 'fixture-v1', createdAt: new Date().toISOString(),
  }] });
  act(() => {
    localStorage.setItem(HISTORY_STORAGE_KEY, saved);
    window.dispatchEvent(new StorageEvent('storage', {
      key: HISTORY_STORAGE_KEY, newValue: saved, storageArea: localStorage,
    }));
  });
  expect(hook.result.current.history.entries.map(entry => entry.text)).toEqual(['Từ tab khác']);
  expect(signal?.aborted).toBe(false);

  act(() => {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    window.dispatchEvent(new StorageEvent('storage', {
      key: HISTORY_STORAGE_KEY, oldValue: saved, newValue: null, storageArea: localStorage,
    }));
  });
  expect(signal?.aborted).toBe(true);
  expect(hook.result.current.history.entries).toEqual([]);
  expect(hook.result.current.transcript).toEqual([]);
  await act(async () => { finish({ data: accepted, requestId: 'late-response' }); await pending; });
  expect(hook.result.current.state.phase).toBe('captured');
  expect(localStorage.getItem(HISTORY_STORAGE_KEY)).toBeNull();
});
