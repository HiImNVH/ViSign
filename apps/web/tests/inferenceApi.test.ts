import { afterEach, describe, expect, it, vi } from 'vitest';
import { createInferenceApi, InferenceApiError } from '../src/services/inferenceApi';

afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

describe('inference API transport', () => {
  it('sends a camera blob and reads the correlation header without requiring diagnostics', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      requestId: 'server-id', text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: 0.9,
      accepted: true, modelVersion: 'v1', processingTimeMs: 12,
    }), { status: 200, headers: { 'X-Request-ID': 'server-id' } }));
    const clip = new Blob(['video'], { type: 'video/webm' });
    const result = await createInferenceApi('https://example.test/').predict(clip);
    expect(result.requestId).toBe('server-id');
    expect(result.data.text).toBe('Xin chào');
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe('https://example.test/api/v1/predictions');
    expect((init?.body as FormData).getAll('clip')).toHaveLength(1);
    expect(((init?.body as FormData).get('clip') as Blob).size).toBe(clip.size);
    expect((init?.headers as Record<string, string>)['X-Request-ID']).toMatch(/^[0-9a-f-]{36}$/i);
    expect(init?.credentials).toBe('omit');
  });

  it('reads model metadata with nullable metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ modelVersion: 'v1', artifactKind: 'fixture', datasetVersion: 'd', featureSchemaVersion: 's', extractorVersion: 'e', meanings: [], acceptanceThreshold: 0.5, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false })));
    expect((await createInferenceApi().modelInfo()).data.modelVersion).toBe('v1');
  });

  it('preserves unknown error codes and retry metadata without server messages', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ code: 'FUTURE_ERROR', message: 'private', requestId: 'id' }), { status: 503, headers: { 'X-Request-ID': 'id', 'Retry-After': '3' } }));
    const error = await createInferenceApi().modelInfo().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(InferenceApiError);
    expect(error).toMatchObject({ kind: 'http', code: 'FUTURE_ERROR', retryAfter: '3', requestId: 'id', message: 'http' });
  });

  it('rejects invalid responses and distinguishes cancellation', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}'));
    await expect(createInferenceApi().modelInfo()).rejects.toMatchObject({ kind: 'invalid-response' });
    const controller = new AbortController();
    controller.abort();
    vi.mocked(fetch).mockRejectedValue(new DOMException('Aborted', 'AbortError'));
    await expect(createInferenceApi().health({ signal: controller.signal })).rejects.toMatchObject({ kind: 'cancelled' });
  });

  it('times out metadata requests after five seconds', async () => {
    vi.useFakeTimers();
    vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    }));
    const result = createInferenceApi().modelInfo().catch((error: unknown) => error);
    await vi.advanceTimersByTimeAsync(5000);
    expect(await result).toMatchObject({ kind: 'timeout' });
  });

  it('times out a prediction only after fifteen seconds and aborts its transport', async () => {
    vi.useFakeTimers();
    let signal: AbortSignal | undefined;
    vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => new Promise((_resolve, reject) => {
      signal = init?.signal ?? undefined;
      signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    }));
    const pending = createInferenceApi().predict(new Blob(['video'])).catch((error: unknown) => error);
    await vi.advanceTimersByTimeAsync(14999);
    expect(signal?.aborted).toBe(false);
    await vi.advanceTimersByTimeAsync(1);
    expect(await pending).toMatchObject({ kind: 'timeout' });
    expect(signal?.aborted).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('keeps user cancellation even if the request settles after its deadline', async () => {
    vi.useFakeTimers();
    let rejectFetch!: (error: Error) => void;
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise((_resolve, reject) => {
      rejectFetch = reject;
    }));
    const controller = new AbortController();
    const pending = createInferenceApi().predict(new Blob(['video']), { signal: controller.signal })
      .catch((error: unknown) => error);
    controller.abort();
    await vi.advanceTimersByTimeAsync(15000);
    rejectFetch(new DOMException('Aborted', 'AbortError'));
    expect(await pending).toMatchObject({ kind: 'cancelled' });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('rejects a late successful response body after cancellation and clears its timer', async () => {
    vi.useFakeTimers();
    let finishBody!: (value: unknown) => void;
    const response = {
      ok: true, status: 200, headers: new Headers({ 'X-Request-ID': 'server-response' }),
      json: () => new Promise(resolve => { finishBody = resolve; }),
    } as Response;
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response);
    const controller = new AbortController();
    const pending = createInferenceApi().predict(new Blob(['video']), { signal: controller.signal })
      .catch((error: unknown) => error);
    await vi.advanceTimersByTimeAsync(0); // allow fetch to reach the body reader
    controller.abort();
    finishBody({ requestId: 'server-response', text: 'Late success', classLabel: 'LATE',
      confidence: .9, accepted: true, modelVersion: 'v1', processingTimeMs: 10 });
    expect(await pending).toMatchObject({ kind: 'cancelled', requestId: 'server-response' });
    expect(vi.getTimerCount()).toBe(0);
  });
});
