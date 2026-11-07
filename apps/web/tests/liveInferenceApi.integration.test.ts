// @vitest-environment node
// apps/web/tests/liveInferenceApi.integration.test.ts — opt-in API v1 real-HTTP consumer smoke.
import { describe, expect, it } from 'vitest';
import { createInferenceApi, InferenceApiError } from '../src/services/inferenceApi';

const acceptedUrl = process.env.VISIGN_LIVE_API_URL;
const rejectedUrl = process.env.VISIGN_LIVE_API_REJECT_URL;
const degradedUrl = process.env.VISIGN_LIVE_API_DEGRADED_URL;

// The fixture predictor requires both the EBML magic and WebM DocType; it does not decode frames.
const fixtureClip = () => new Blob([new Uint8Array([
  0x1a, 0x45, 0xdf, 0xa3, 0x42, 0x82, 0x84, 0x77, 0x65, 0x62, 0x6d,
])], { type: 'video/webm' });

describe.skipIf(!acceptedUrl)('T040 live API fixture HTTP integration', () => {
  it('reads health/metadata and submits exactly one accepted multipart prediction', async () => {
    const api = createInferenceApi(acceptedUrl);
    const health = await api.health();
    expect(health.data).toMatchObject({ status: 'ok', modelReady: true });
    expect(health.requestId).toMatch(/^[0-9a-f-]{36}$/i);
    const info = await api.modelInfo();
    expect(info.data).toMatchObject({ artifactKind: 'fixture', demoReady: false });
    expect(info.data.meanings.length).toBeGreaterThan(0);
    expect(info.data.meanings.length).toBeLessThanOrEqual(10);
    const result = await api.predict(fixtureClip());
    expect(result.requestId).toBe(result.data.requestId);
    expect(result.data).toMatchObject({ accepted: true, text: 'Cảm ơn', confidence: .95,
      modelVersion: info.data.modelVersion });
    expect(result.data.processingTimeMs).toBeGreaterThanOrEqual(0);
    expect(result.data.qualityHints).toMatchObject({ frameCount: 30 });
  });

  it('preserves the real 415 error envelope and response correlation', async () => {
    const api = createInferenceApi(acceptedUrl);
    const error = await api.predict(new Blob(['text'], { type: 'text/plain' })).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(InferenceApiError);
    expect(error).toMatchObject({ kind: 'http', status: 415, code: 'UNSUPPORTED_MEDIA_TYPE' });
    expect((error as InferenceApiError).requestId).toMatch(/^[0-9a-f-]{36}$/i);
  });
});

describe.skipIf(!rejectedUrl)('T040 live low-confidence fixture', () => {
  it('preserves the canonical rejected response without translating it', async () => {
    const result = await createInferenceApi(rejectedUrl).predict(fixtureClip());
    expect(result.data).toMatchObject({ accepted: false, text: 'Không nhận diện được',
      classLabel: null, confidence: .42 });
    expect(result.requestId).toBe(result.data.requestId);
  });
});

describe.skipIf(!degradedUrl)('T040 live degraded backend', () => {
  it('serves degraded health and reports MODEL_NOT_READY with retry metadata', async () => {
    const api = createInferenceApi(degradedUrl);
    expect((await api.health()).data).toMatchObject({ status: 'degraded', modelReady: false });
    for (const call of [() => api.modelInfo(), () => api.predict(fixtureClip())]) {
      const error = await call().catch((e: unknown) => e);
      expect(error).toMatchObject({ kind: 'http', status: 503, code: 'MODEL_NOT_READY', retryAfter: '5' });
    }
  });
});
