// apps/web/tests/recognition/recognition-overlay.test.tsx - Chi hien chu khi ket qua duoc chap nhan cho dung clip.
import { render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { RecognitionOverlay, type CapturedRecognitionResult } from '../../src/features/recognition/RecognitionOverlay';
import { CameraRecorder } from '../../src/features/recognition/CameraRecorder';
import { CameraSession } from '../../src/features/recognition/cameraSession';

const clip = new Blob(['test-only'], { type: 'video/webm' });
const accepted: CapturedRecognitionResult = { clip, accepted: true, text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: .92 };
afterEach(() => vi.restoreAllMocks());

test('accepted translation shows text, confidence and experimental notice', () => {
  render(<RecognitionOverlay result={accepted} />);
  expect(screen.getByRole('region', { name: 'Văn bản dịch' })).toHaveTextContent('Xin chào');
  expect(screen.getByText('Độ tin cậy 92%')).toBeVisible();
  expect(screen.getByText(/có thể không chính xác/)).toBeVisible();
});

test.each([
  null,
  { ...accepted, accepted: false },
  { ...accepted, text: '  ' },
  { ...accepted, classLabel: null },
  { ...accepted, classLabel: '' },
  { ...accepted, confidence: NaN },
  { ...accepted, confidence: 1.1 },
  { ...accepted, confidence: -.1 },
])('absent or invalid recognition does not render a translation panel: %j', result => {
  const { container } = render(<RecognitionOverlay result={result} />);
  expect(container).toBeEmptyDOMElement();
});

test('camera displays accepted API results only in a captured prediction state', () => {
  const session = new CameraSession(vi.fn());
  const apiResult = { requestId: 'prediction-id', text: 'Xin chào', classLabel: 'XIN_CHAO',
    confidence: .92, accepted: true, modelVersion: 'fixture-v1', processingTimeMs: 50 };
  const model = { status: 'ready' as const, info: { modelVersion: 'fixture-v1', artifactKind: 'fixture' as const,
    datasetVersion: 'demo', featureSchemaVersion: 'v1', extractorVersion: 'v1', meanings: ['Xin chào'],
    acceptanceThreshold: .7, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false } };
  const makeController = (cameraView: typeof session.view, showResult: boolean) => ({
    camera: { view: cameraView, session, videoRef: { current: null } }, model,
    state: showResult ? { phase: 'result' as const, artifactKind: 'fixture' as const, result: apiResult, requestId: 'prediction-id' } : cameraView,
    enableCamera: async () => {}, startRecording: () => {}, stopRecording: () => {}, submit: async () => {},
    cancel: () => {}, reset: () => {}, reloadModelInfo: () => {},
  });
  const rendered = render(<CameraRecorder controller={makeController({ phase: 'captured', clip, durationMs: 500 }, true)} />);
  expect(screen.getByRole('region', { name: 'Văn bản dịch' })).toBeVisible();
  const video = screen.getByLabelText('Hình ảnh xem trước từ camera');
  rendered.rerender(<CameraRecorder controller={makeController({ phase: 'recording' }, false)} />);
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
  expect(screen.getByLabelText('Hình ảnh xem trước từ camera')).toBe(video);
  rendered.rerender(<CameraRecorder controller={makeController({ phase: 'captured', clip: new Blob(['another']), durationMs: 500 }, false)} />);
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
});
