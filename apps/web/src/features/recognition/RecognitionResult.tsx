// T042: accepted prediction presentation. T043 will wire the API model and camera into this view.
import { vi } from '../../content/vi';
import type { ModelInfo, PredictionResponse } from '../../types/inference-api';

export type RecognitionResultModel = Pick<ModelInfo, 'modelVersion' | 'artifactKind' | 'meanings' | 'demoReady'>;

interface RecognitionResultProps {
  result: PredictionResponse | null;
  model: RecognitionResultModel | null;
}

export function RecognitionResult({ result, model }: RecognitionResultProps) {
  // Metadata must match the prediction, including after an artifact swap or refresh.
  if (!result || !model || result.accepted !== true || result.modelVersion !== model.modelVersion
    || !result.text.trim() || !result.classLabel?.trim()
    || !Number.isFinite(result.confidence) || result.confidence < 0 || result.confidence > 1) return null;

  const notReady = !model.demoReady || model.artifactKind !== 'full';
  const meanings = model.meanings.join(', ');

  return <section className="translation-panel" aria-label="Văn bản dịch" aria-live="polite" aria-atomic="true">
    <p className="translation-text">{result.text.trim()}</p>
    <p className="translation-confidence">{vi.recognition.confidence} {(result.confidence * 100).toFixed(0)}%</p>
    <p className="translation-notice">
      <span className="full-disclaimer">{vi.disclaimer}</span>
      <span className="short-disclaimer">{vi.recognition.shortDisclaimer}</span>
    </p>
    {notReady && <>
      <p className="translation-model-warning" role="note">{vi.recognition.modelNotReady[model.artifactKind]}</p>
      <p className="translation-coverage" title={meanings || vi.recognition.noMeanings}>
        {meanings ? `${vi.recognition.meanings}: ${meanings}` : vi.recognition.noMeanings}
      </p>
    </>}
  </section>;
}
