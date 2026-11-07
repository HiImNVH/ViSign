import { cameraErrors, predictionErrors, vi, type CameraError } from '../../content/vi';
import { InferenceApiError } from '../../services/inferenceApi';

type Props =
  | { type: 'camera'; error: CameraError }
  | { type: 'api'; error: InferenceApiError; stage: 'model' | 'prediction' };

function predictionMessage(error: InferenceApiError): string | null {
  if (error.kind === 'cancelled') return null;
  if (error.kind === 'network') return predictionErrors.network;
  if (error.kind === 'timeout') return predictionErrors.timeout;
  if (error.kind === 'invalid-response') return predictionErrors.invalidResponse;
  if (error.kind === 'http' && error.code && Object.hasOwn(predictionErrors.codes, error.code)) {
    return predictionErrors.codes[error.code as keyof typeof predictionErrors.codes];
  }
  return vi.recognition.submitError;
}

export function RecognitionError(props: Props) {
  if (props.type === 'camera') {
    const [title, guidance] = cameraErrors[props.error];
    return <div className="capture-feedback error-feedback" role="alert"><h3>{title}</h3><p>{guidance}</p></div>;
  }

  // Metadata errors should always offer the existing explicit reconnect action.
  // Prediction errors can be retried by an explicit submit or a fresh capture.
  const message = props.stage === 'model' ? vi.recognition.modelUnavailable : predictionMessage(props.error);
  return message ? <p role="alert">{message}</p> : null;
}
