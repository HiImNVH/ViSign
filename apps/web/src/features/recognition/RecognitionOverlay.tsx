// apps/web/src/features/recognition/RecognitionOverlay.tsx - Chi hien ket qua hop le da duoc chap nhan.
export interface CapturedRecognitionResult {
  clip: Blob;
  accepted: boolean;
  text: string;
  classLabel: string | null;
  confidence: number;
}

export function RecognitionOverlay({ result }: { result: CapturedRecognitionResult | null }) {
  if (!result || result.accepted !== true || !result.text.trim() || !result.classLabel?.trim()
    || !Number.isFinite(result.confidence) || result.confidence < 0 || result.confidence > 1) return null;
  return <section className="translation-panel" aria-label="Văn bản dịch" aria-live="polite">
    <p className="translation-text">{result.text}</p>
    <p className="translation-confidence">Độ tin cậy {(result.confidence * 100).toFixed(0)}%</p>
    <p className="translation-notice">Kết quả thử nghiệm, có thể không chính xác.</p>
  </section>;
}
