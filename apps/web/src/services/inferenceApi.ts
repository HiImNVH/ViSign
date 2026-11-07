import type { HealthResponse, ModelInfo, PredictionResponse } from '../types/inference-api';

export class InferenceApiError extends Error {
  constructor(
    public readonly kind: 'http' | 'network' | 'timeout' | 'cancelled' | 'invalid-response',
    public readonly requestId: string,
    public readonly status?: number,
    public readonly code?: string,
    public readonly retryAfter?: string,
  ) { super(kind); }
}

type ApiResult<T> = { data: T; requestId: string };
type RequestOptions = { signal?: AbortSignal };
type JsonObject = Record<string, unknown>;
const object = (value: unknown): value is JsonObject => typeof value === 'object' && value !== null && !Array.isArray(value);
const number = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const nullableString = (value: unknown) => value === null || typeof value === 'string';

function isPrediction(value: unknown): value is PredictionResponse {
  if (!object(value)) return false;
  return typeof value.requestId === 'string' && typeof value.text === 'string' && nullableString(value.classLabel)
    && number(value.confidence) && value.confidence >= 0 && value.confidence <= 1 && typeof value.accepted === 'boolean'
    && typeof value.modelVersion === 'string' && number(value.processingTimeMs) && value.processingTimeMs >= 0
    && (value.timingsMs === undefined || (object(value.timingsMs) && ['decode', 'extract', 'infer'].every(k => number((value.timingsMs as JsonObject)[k]))))
    && (value.qualityHints === undefined || (object(value.qualityHints) && number(value.qualityHints.handsDetectedRatio) && number(value.qualityHints.frameCount)));
}

function isModelInfo(value: unknown): value is ModelInfo {
  if (!object(value)) return false;
  return ['modelVersion', 'datasetVersion', 'featureSchemaVersion', 'extractorVersion'].every(k => typeof value[k] === 'string')
    && ['fixture', 'pilot', 'full'].includes(String(value.artifactKind)) && Array.isArray(value.meanings) && value.meanings.every(v => typeof v === 'string')
    && number(value.acceptanceThreshold) && (value.macroF1 === null || number(value.macroF1))
    && (value.perMeaningRecall === null || (object(value.perMeaningRecall) && Object.values(value.perMeaningRecall).every(number)))
    && nullableString(value.evaluatedAt) && typeof value.demoReady === 'boolean';
}

function isHealth(value: unknown): value is HealthResponse {
  return object(value) && (value.status === 'ok' || value.status === 'degraded') && typeof value.modelReady === 'boolean'
    && (value.modelVersion === undefined || nullableString(value.modelVersion));
}

export function createInferenceApi(baseUrl = import.meta.env.VITE_API_BASE_URL ?? '') {
  const base = String(baseUrl).replace(/\/$/, '');
  async function request<T>(path: string, timeout: number, guard: (value: unknown) => value is T, options: RequestOptions, body?: FormData): Promise<ApiResult<T>> {
    const requestId = crypto.randomUUID();
    const controller = new AbortController();
    let timedOut = false;
    const cancel = () => controller.abort();
    if (options.signal?.aborted) cancel();
    else options.signal?.addEventListener('abort', cancel, { once: true });
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeout);
    let responseId: string = requestId;
    try {
      const init: RequestInit = { method: body ? 'POST' : 'GET', headers: { 'X-Request-ID': requestId }, signal: controller.signal, credentials: 'omit' };
      if (body) init.body = body;
      const response = await fetch(`${base}/api/v1/${path}`, init);
      responseId = response.headers.get('X-Request-ID') || requestId;
      let payload: unknown;
      try { payload = await response.json(); } catch { if (controller.signal.aborted) throw new DOMException('Aborted', 'AbortError'); }
      if (!response.ok) throw new InferenceApiError('http', responseId, response.status, object(payload) && typeof payload.code === 'string' ? payload.code : undefined, response.headers.get('Retry-After') ?? undefined);
      if (!guard(payload)) throw new InferenceApiError('invalid-response', responseId, response.status);
      return { data: payload, requestId: responseId };
    } catch (error) {
      if (controller.signal.aborted) throw new InferenceApiError(timedOut ? 'timeout' : 'cancelled', responseId);
      if (error instanceof InferenceApiError) throw error;
      throw new InferenceApiError('network', responseId);
    } finally {
      clearTimeout(timer);
      options.signal?.removeEventListener('abort', cancel);
    }
  }
  return {
    health: (options: RequestOptions = {}) => request('health', 5000, isHealth, options),
    modelInfo: (options: RequestOptions = {}) => request('model-info', 5000, isModelInfo, options),
    predict: (clip: Blob, options: RequestOptions = {}) => {
      const form = new FormData();
      form.append('clip', clip, 'capture.webm');
      return request('predictions', 15000, isPrediction, options, form);
    },
  };
}
