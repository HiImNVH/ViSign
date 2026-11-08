// Regression for the production camera component (no obsolete overlay).
import { render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { CameraRecorder } from './ManualRecorder';
import type { CameraView } from '../../src/features/recognition/cameraSession';

const clip = new Blob(['test-only'], { type: 'video/webm' });
afterEach(() => vi.restoreAllMocks());

test('camera displays accepted API results only in a captured prediction state', () => {
  const apiResult = { requestId: 'prediction-id', text: 'Xin chào', classLabel: 'XIN_CHAO',
    confidence: .92, accepted: true, modelVersion: 'fixture-v1', processingTimeMs: 50 };
  const model = { status: 'ready' as const, info: { modelVersion: 'fixture-v1', artifactKind: 'fixture' as const,
    datasetVersion: 'demo', featureSchemaVersion: 'v1', extractorVersion: 'v1', meanings: ['Xin chào'],
    acceptanceThreshold: .7, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false } };
  const makeController = (cameraView: CameraView, showResult: boolean) => ({
    camera: { view: cameraView, videoRef: { current: null } }, model,
    compatibilityError: null, transcript: [],
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
