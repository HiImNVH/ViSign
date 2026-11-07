import type { RefObject } from 'react';
import type { CameraView } from './cameraSession';
import type { ArtifactKind, ModelInfo, PredictionResponse } from '../../types/inference-api';
import type { InferenceApiError } from '../../services/inferenceApi';
import type { HistoryRead, TranslationHistoryEntry } from './translationHistory';

export type ModelStatus =
  | { status: 'loading' }
  | { status: 'ready'; info: ModelInfo }
  | { status: 'unavailable'; error: InferenceApiError };

export type PredictionState =
  | { phase: 'submitting'; artifactKind: ArtifactKind }
  | { phase: 'result'; artifactKind: ArtifactKind; result: PredictionResponse; requestId: string }
  | { phase: 'error'; source: 'api'; artifactKind: ArtifactKind; error: InferenceApiError };

export type RecognitionState = CameraView | PredictionState;

export interface CameraController {
  camera: { view: CameraView; videoRef: RefObject<HTMLVideoElement | null> };
  state: RecognitionState;
  model: ModelStatus;
  compatibilityError: InferenceApiError | null;
  transcript: TranslationHistoryEntry[];
  enableCamera: () => Promise<void>;
  startRecording: () => void;
  stopRecording: () => void;
  submit: () => Promise<void>;
  cancel: () => void;
  reset: () => void;
  reloadModelInfo: () => void;
}

export interface HistoryController {
  history: HistoryRead;
  refreshHistory: () => void;
  clearHistory: () => boolean;
}

export type RecognitionController = CameraController & HistoryController;
