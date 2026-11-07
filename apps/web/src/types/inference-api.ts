// apps/web/src/types/inference-api.ts
// Kieu du lieu API v1 viet tay theo specs/001-vsl-recognition-mvp/contracts/openapi.yaml (T099, quyet dinh D4).
// tests/contract/test_api_contract_drift.py so enum, field, required va nullable voi OpenAPI va Python domain.

// D3: moi ma loi backend phat hanh phai co trong danh sach nay truoc
export const ERROR_CODES = [
  'INVALID_REQUEST',
  'UNSUPPORTED_MEDIA_TYPE',
  'CLIP_TOO_LARGE',
  'CLIP_TOO_SHORT',
  'CLIP_TOO_LONG',
  'NO_PERSON_DETECTED',
  'INSUFFICIENT_LANDMARKS',
  'CLIP_DECODE_FAILED',
  'SERVICE_BUSY',
  'MODEL_NOT_READY',
  'PREDICTION_FAILED',
  'ROUTE_NOT_FOUND',
  'METHOD_NOT_ALLOWED',
] as const;

export const ARTIFACT_KINDS = ['fixture', 'pilot', 'full'] as const;

export const HEALTH_STATUSES = ['ok', 'degraded'] as const;

export type KnownErrorCode = (typeof ERROR_CODES)[number];

export type ArtifactKind = (typeof ARTIFACT_KINDS)[number];

export type HealthStatus = (typeof HEALTH_STATUSES)[number];

export interface HealthResponse {
  status: HealthStatus;
  modelReady: boolean;
  modelVersion?: string | null;
}

export interface ModelInfo {
  modelVersion: string;
  artifactKind: ArtifactKind;
  datasetVersion: string;
  featureSchemaVersion: string;
  extractorVersion: string;
  meanings: string[];
  acceptanceThreshold: number;
  macroF1: number | null;
  perMeaningRecall: Record<string, number> | null;
  evaluatedAt: string | null;
  demoReady: boolean;
}

export interface PredictionTimings {
  decode: number;
  extract: number;
  infer: number;
}

export interface PredictionQualityHints {
  handsDetectedRatio: number;
  frameCount: number;
}

export interface PredictionResponse {
  requestId: string;
  text: string;
  classLabel: string | null;
  confidence: number;
  accepted: boolean;
  modelVersion: string;
  processingTimeMs: number;
  timingsMs?: PredictionTimings;
  qualityHints?: PredictionQualityHints;
}

export interface ErrorEnvelope {
  // Giu string de ma moi chua biet di vao nhanh fallback thay vi lam vo kieu
  code: KnownErrorCode | (string & {});
  message: string;
  requestId: string;
}

export function isKnownErrorCode(errorCode: string): errorCode is KnownErrorCode {
  return (ERROR_CODES as readonly string[]).includes(errorCode);
}
