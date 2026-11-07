import { afterEach, describe, expect, it, vi } from 'vitest';
import { createInferenceApi, InferenceApiError } from '../src/services/inferenceApi';

afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });
const validId = '123e4567-e89b-42d3-a456-426614174000';
const model = {
  modelVersion: 'v1', artifactKind: 'fixture', datasetVersion: 'd', featureSchemaVersion: 's',
  extractorVersion: 'e', meanings: ['CAM_ON'], acceptanceThreshold: 0.5,
  macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
const prediction = { requestId: validId, text: 'Xin chào', classLabel: 'XIN_CHAO',
  confidence: .9, accepted: true, modelVersion: 'v1', processingTimeMs: 12 };

describe('inference API transport', () => {
  it('sends a camera blob and reads the correlation header without requiring diagnostics', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      requestId: validId, text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: 0.9,
      accepted: true, modelVersion: 'v1', processingTimeMs: 12,
    }), { status: 200, headers: { 'X-Request-ID': validId } }));
    const clip = new Blob(['video'], { type: 'video/webm' });
    const result = await createInferenceApi('https://example.test/').predict(clip);
    expect(result.requestId).toBe(validId);
    expect(result.data.text).toBe('Xin chào');
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe('https://example.test/api/v1/predictions');
    expect((init?.body as FormData).getAll('clip')).toHaveLength(1);
    expect(((init?.body as FormData).get('clip') as Blob).size).toBe(clip.size);
    expect((init?.headers as Record<string, string>)['X-Request-ID']).toMatch(/^[0-9a-f-]{36}$/i);
    expect(init?.credentials).toBe('omit');
  });

  it('reads model metadata with nullable metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(model)));
    expect((await createInferenceApi().modelInfo()).data.modelVersion).toBe('v1');
  });

  it.each([
    { meanings: [] }, { meanings: Array.from({ length: 11 }, (_, i) => `MEANING_${i}`) },
    { acceptanceThreshold: -0.1 }, { acceptanceThreshold: 1.01 },
    { macroF1: 1.1 }, { perMeaningRecall: { CAM_ON: -0.1 } },
    { evaluatedAt: 'yesterday' }, { evaluatedAt: '2026-11-07T11:10:00' },
    { evaluatedAt: '2026-11-07T11:10:00Z', demoReady: 'yes' },
  ])('rejects out-of-contract model metadata %j', async invalid => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...model, ...invalid })));
    await expect(createInferenceApi().modelInfo()).rejects.toMatchObject({ kind: 'invalid-response' });
  });

  it.each([
    { requestId: 'not-a-uuid' }, { confidence: 1.1 }, { processingTimeMs: 2.5 },
    { text: '', accepted: true }, { classLabel: null, accepted: true },
    { accepted: false, classLabel: null },
    { timingsMs: { decode: 0, extract: -1, infer: 3 } },
    { timingsMs: { decode: 0.5, extract: 1, infer: 3 } },
    { qualityHints: { handsDetectedRatio: 1.1, frameCount: 20 } },
    { qualityHints: { handsDetectedRatio: .5, frameCount: 0 } },
    { qualityHints: null },
  ])('rejects out-of-contract prediction %j', async invalid => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...prediction, ...invalid })));
    await expect(createInferenceApi().predict(new Blob(['video']))).rejects.toMatchObject({ kind: 'invalid-response' });
  });

  it('accepts valid optional diagnostics and a canonical rejected outcome', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({
      ...prediction, timingsMs: { decode: 0, extract: 4, infer: 3 },
      qualityHints: { handsDetectedRatio: 1, frameCount: 1 },
    }))).mockResolvedValueOnce(new Response(JSON.stringify({
      ...prediction, text: 'Không nhận diện được', classLabel: null, accepted: false,
    })));
    expect((await createInferenceApi().predict(new Blob(['video']))).data.qualityHints?.frameCount).toBe(1);
    expect((await createInferenceApi().predict(new Blob(['video']))).data.accepted).toBe(false);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('classifies network failure and falls back to the outbound correlation ID when the response header is absent', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(new Response(JSON.stringify(model)));
    await expect(createInferenceApi().modelInfo()).rejects.toMatchObject({ kind: 'network' });
    const response = await createInferenceApi().modelInfo();
    const outbound = (fetchMock.mock.calls[1]![1]!.headers as Record<string, string>)['X-Request-ID'];
    expect(response.requestId).toBe(outbound);
  });

  it('rejects a successful prediction with a mismatched correlation header', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(prediction), {
      headers: { 'X-Request-ID': '123e4567-e89b-42d3-a456-426614174001' },
    }));
    await expect(createInferenceApi().predict(new Blob(['video']))).rejects.toMatchObject({ kind: 'invalid-response' });
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
