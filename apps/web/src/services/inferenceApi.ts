// apps/web/src/services/inferenceApi.ts — typed HTTP client for API v1.
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
const probability = (value: unknown) => number(value) && value >= 0 && value <= 1;
const nonNegativeInteger = (value: unknown): value is number => number(value) && Number.isInteger(value) && value >= 0;
const uuid = (value: unknown) => typeof value === 'string' && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value);
const dateTime = (value: unknown) => typeof value === 'string'
  && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
  && Number.isFinite(Date.parse(value));

function validTimings(value: unknown): boolean {
  return object(value) && ['decode', 'extract', 'infer'].every(key => nonNegativeInteger(value[key]));
}

function validQualityHints(value: unknown): boolean {
  if (!object(value)) return false;
  const frameCount = value.frameCount;
  return probability(value.handsDetectedRatio)
    && nonNegativeInteger(frameCount) && frameCount >= 1;
}

function isPrediction(value: unknown): value is PredictionResponse {
  if (!object(value)) return false;
  return uuid(value.requestId) && typeof value.text === 'string' && nullableString(value.classLabel)
    && probability(value.confidence) && typeof value.accepted === 'boolean'
    && (value.accepted
      ? Boolean(value.text.trim()) && typeof value.classLabel === 'string' && Boolean(value.classLabel.trim())
      : value.classLabel === null && value.text === 'Không nhận diện được')
    && typeof value.modelVersion === 'string' && nonNegativeInteger(value.processingTimeMs)
    && (value.timingsMs === undefined || validTimings(value.timingsMs))
    && (value.qualityHints === undefined || validQualityHints(value.qualityHints));
}

function isModelInfo(value: unknown): value is ModelInfo {
  if (!object(value)) return false;
  return ['modelVersion', 'datasetVersion', 'featureSchemaVersion', 'extractorVersion'].every(k => typeof value[k] === 'string')
    && ['fixture', 'pilot', 'full'].includes(String(value.artifactKind))
    && Array.isArray(value.meanings) && value.meanings.length >= 1 && value.meanings.length <= 10
    && value.meanings.every(v => typeof v === 'string')
    && probability(value.acceptanceThreshold) && (value.macroF1 === null || probability(value.macroF1))
    && (value.perMeaningRecall === null || (object(value.perMeaningRecall) && Object.values(value.perMeaningRecall).every(probability)))
    && (value.evaluatedAt === null || dateTime(value.evaluatedAt)) && typeof value.demoReady === 'boolean';
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
    let abortReason: 'timeout' | 'cancelled' | null = null;
    const abort = (reason: 'timeout' | 'cancelled') => {
      if (controller.signal.aborted) return;
      abortReason = reason;
      controller.abort();
    };
    const cancel = () => abort('cancelled');
    if (options.signal?.aborted) cancel();
    else options.signal?.addEventListener('abort', cancel, { once: true });
    const timer = setTimeout(() => abort('timeout'), timeout);
    let responseId: string = requestId;
    try {
      const init: RequestInit = { method: body ? 'POST' : 'GET', headers: { 'X-Request-ID': requestId }, signal: controller.signal, credentials: 'omit' };
      if (body) init.body = body;
      const response = await fetch(`${base}/api/v1/${path}`, init);
      const correlationHeader = response.headers.get('X-Request-ID');
      responseId = correlationHeader || requestId;
      let payload: unknown;
      try { payload = await response.json(); } catch { if (controller.signal.aborted) throw new DOMException('Aborted', 'AbortError'); }
      // A body reader can finish after cancellation even when fetch itself resolved.
      if (controller.signal.aborted) throw new DOMException('Aborted', 'AbortError');
      if (!response.ok) throw new InferenceApiError('http', responseId, response.status, object(payload) && typeof payload.code === 'string' ? payload.code : undefined, response.headers.get('Retry-After') ?? undefined);
      if (!guard(payload)) throw new InferenceApiError('invalid-response', responseId, response.status);
      if (correlationHeader && object(payload) && 'requestId' in payload && payload.requestId !== correlationHeader) {
        throw new InferenceApiError('invalid-response', responseId, response.status);
      }
      return { data: payload, requestId: responseId };
    } catch (error) {
      if (controller.signal.aborted) throw new InferenceApiError(abortReason ?? 'cancelled', responseId);
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
