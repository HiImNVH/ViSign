import { cameraErrors, predictionErrors, vi, type CameraError } from '../../content/vi';
import { InferenceApiError } from '../../services/inferenceApi';

type Props =
  | { type: 'camera'; error: CameraError }
  | { type: 'api'; error: InferenceApiError; stage: 'model' | 'prediction' };

function predictionMessage(error: InferenceApiError): string | null {
  if (error.kind === 'route-not-found' || error.status === 404) return predictionErrors.apiRouteNotFound;
  if (error.kind === 'method-not-allowed' || error.status === 405) return predictionErrors.apiMethodNotAllowed;
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
  const compatibility = props.error.kind === 'route-not-found' || props.error.kind === 'method-not-allowed'
    || props.error.status === 404 || props.error.status === 405;
  const message = props.stage === 'model' && !compatibility ? vi.recognition.modelUnavailable : predictionMessage(props.error);
  return message ? <p role="alert">{message}</p> : null;
}
