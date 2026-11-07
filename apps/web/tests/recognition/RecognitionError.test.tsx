import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { cameraErrors, predictionErrors, vi, type CameraError } from '../../src/content/vi';
import { RecognitionError } from '../../src/features/recognition/RecognitionError';
import { InferenceApiError } from '../../src/services/inferenceApi';

test.each(Object.keys(cameraErrors) as CameraError[])('camera error %s uses fixed Vietnamese title and advice', error => {
  render(<RecognitionError type="camera" error={error} />);
  expect(screen.getByRole('alert')).toHaveTextContent(cameraErrors[error][0]);
  expect(screen.getByRole('alert')).toHaveTextContent(cameraErrors[error][1]);
});

test.each(Object.entries(predictionErrors.codes))('prediction HTTP code %s has safe guidance', (code, message) => {
  const error = new InferenceApiError('http', 'sensitive-request-id', 422, code, '4');
  render(<RecognitionError type="api" stage="prediction" error={error} />);
  expect(screen.getByRole('alert')).toHaveTextContent(message);
  expect(screen.getByRole('alert')).not.toHaveTextContent('sensitive-request-id');
  expect(screen.getByRole('alert')).not.toHaveTextContent(code);
  expect(screen.getByRole('alert')).not.toHaveTextContent('4');
});

test.each([
  ['network', predictionErrors.network],
  ['timeout', predictionErrors.timeout],
  ['invalid-response', predictionErrors.invalidResponse],
] as const)('%s prediction errors show local Vietnamese guidance', (kind, message) => {
  render(<RecognitionError type="api" stage="prediction" error={new InferenceApiError(kind, 'private')} />);
  expect(screen.getByRole('alert')).toHaveTextContent(message);
});

test.each(['UNKNOWN_CODE', '__proto__', 'constructor', '<script>alert(1)</script>', undefined])(
  'unknown API error code %s safely falls back', code => {
    const error = new InferenceApiError('http', 'sensitive-request-id', 500, code, '123');
    render(<RecognitionError type="api" stage="prediction" error={error} />);
    expect(screen.getByRole('alert')).toHaveTextContent(vi.recognition.submitError);
    expect(screen.getByRole('alert')).not.toHaveTextContent('sensitive-request-id');
    expect(screen.getByRole('alert')).not.toHaveTextContent('script');
    expect(screen.getByRole('alert')).not.toHaveTextContent('123');
  },
);

test('cancelled API requests do not generate an error alert', () => {
  render(<RecognitionError type="api" stage="prediction" error={new InferenceApiError('cancelled', 'private')} />);
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

test('metadata failure retains reconnect guidance without leaking API details', () => {
  render(<RecognitionError type="api" stage="model" error={new InferenceApiError('http', 'private-id', 503, 'MODEL_NOT_READY')} />);
  expect(screen.getByRole('alert')).toHaveTextContent(vi.recognition.modelUnavailable);
  expect(screen.getByRole('alert')).not.toHaveTextContent('MODEL_NOT_READY');
  expect(screen.getByRole('alert')).not.toHaveTextContent('private-id');
});
