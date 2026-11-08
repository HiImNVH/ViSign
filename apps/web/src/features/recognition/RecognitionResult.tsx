// T042/T051: accepted translation and rejected-result retry presentation.
import { vi } from '../../content/vi';
import type { Ref } from 'react';
import type { ModelInfo, PredictionResponse } from '../../types/inference-api';

export type RecognitionResultModel = Pick<ModelInfo, 'modelVersion' | 'artifactKind' | 'meanings' | 'demoReady'>
  & Partial<Pick<ModelInfo, 'meaningDisplayTexts'>>;

interface RecognitionResultProps {
  result: PredictionResponse | null;
  model: RecognitionResultModel | null;
  onRetry?: () => void;
  retryRef?: Ref<HTMLButtonElement>;
}

export function RecognitionResult({ result, model, onRetry, retryRef }: RecognitionResultProps) {
  // Metadata must match the prediction, including after an artifact swap or refresh.
  if (!result || !model || result.modelVersion !== model.modelVersion) return null;

  // Rejected predictions cannot display a translation, regardless of returned text/confidence.
  if (!result.accepted) return <section className="translation-panel translation-rejected"
    aria-label="Kết quả nhận diện" aria-live="polite" aria-atomic="true">
    <p className="translation-rejected-message">{vi.recognition.rejected}</p>
    {onRetry && <button ref={retryRef} type="button" className="quiet-button translation-retry" onClick={onRetry}>Quay lại</button>}
  </section>;

  if (!result.text.trim() || !result.classLabel?.trim()
    || !Number.isFinite(result.confidence) || result.confidence < 0 || result.confidence > 1) return null;

  return <section className="translation-panel" aria-label="Văn bản dịch" aria-live="polite" aria-atomic="true">
    <p className="translation-text">{result.text.trim()}</p>
  </section>;
}
