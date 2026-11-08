import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { RecognitionResult } from '../../src/features/recognition/RecognitionResult';
import { vi as copy } from '../../src/content/vi';
import type { ModelInfo, PredictionResponse } from '../../src/types/inference-api';

const accepted: PredictionResponse = {
  requestId: 'r1', text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: .92,
  accepted: true, modelVersion: 'demo-v1', processingTimeMs: 120,
};
const model: ModelInfo = {
  modelVersion: 'demo-v1', artifactKind: 'full', datasetVersion: 'd1', featureSchemaVersion: 'f1',
  extractorVersion: 'e1', meanings: ['Xin chào', 'Cảm ơn'], acceptanceThreshold: .7,
  macroF1: .9, perMeaningRecall: {}, evaluatedAt: null, demoReady: true,
};

test('accepted result renders Vietnamese translation, confidence and full disclaimer', () => {
  render(<RecognitionResult result={accepted} model={model} />);
  const panel = screen.getByRole('region', { name: 'Văn bản dịch' });
  expect(panel).toHaveAttribute('aria-live', 'polite');
  expect(panel).toHaveAttribute('aria-atomic', 'true');
  expect(panel).toHaveTextContent('Xin chào');
  expect(panel).toHaveTextContent('Độ tin cậy 92%');
  expect(panel).toHaveTextContent(copy.disclaimer);
  expect(screen.queryByText(/chưa sẵn sàng.*demo/i)).not.toBeInTheDocument();
});

test.each([
  ['fixture', 'Tích hợp nội bộ', ['Xin chào']],
  ['pilot', 'Thí điểm giới hạn', ['Xin chào', 'Cảm ơn']],
  ['full', 'chưa đạt điều kiện demo', ['Xin chào']],
] as const)('model kind %s with demoReady=false visibly discloses scope', (artifactKind, expectedNotice, meanings) => {
  render(<RecognitionResult result={accepted} model={{ ...model, artifactKind, demoReady: false, meanings: [...meanings] }} />);
  expect(screen.getByRole('note')).toHaveTextContent(expectedNotice);
  expect(screen.getByRole('note')).toHaveTextContent('demo');
  expect(screen.getByText(new RegExp(`^Ý nghĩa hỗ trợ: ${meanings.join('.*')}$`))).toBeVisible();
  expect(screen.getByText(copy.disclaimer)).toBeVisible();
});

test('model with no supported meanings makes limitation explicit', () => {
  render(<RecognitionResult result={accepted} model={{ ...model, artifactKind: 'fixture', demoReady: false, meanings: [] }} />);
  expect(screen.getByText(/Chưa công bố ý nghĩa hỗ trợ/)).toBeVisible();
});

test('pilot cannot be presented as demo-ready even with inconsistent metadata', () => {
  render(<RecognitionResult result={accepted} model={{ ...model, artifactKind: 'pilot', demoReady: true }} />);
  expect(screen.getByRole('note')).toHaveTextContent('Thí điểm giới hạn');
  expect(screen.getByText(/^Ý nghĩa hỗ trợ:/)).toBeVisible();
});

test.each([
  [0, '0%'], [1, '100%'], [.925, '93%'],
] as const)('accepted confidence %s formats as %s', (confidence, expected) => {
  render(<RecognitionResult result={{ ...accepted, confidence }} model={model} />);
  expect(screen.getByText(`Độ tin cậy ${expected}`)).toBeVisible();
});

test('rejected result shows only safe guidance and explicitly starts a new recording', () => {
  const retry = vi.fn();
  render(<RecognitionResult result={{ ...accepted, accepted: false, text: 'Xin chào', classLabel: null, confidence: .95 }}
    model={model} onRetry={retry} />);
  const panel = screen.getByRole('region', { name: 'Kết quả nhận diện' });
  expect(panel).toHaveAttribute('aria-live', 'polite');
  expect(panel).toHaveAttribute('aria-atomic', 'true');
  expect(panel).toHaveTextContent(copy.recognition.rejected);
  expect(panel).not.toHaveTextContent('Xin chào');
  expect(panel).not.toHaveTextContent('95%');
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
  expect(retry).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Quay lại' }));
  expect(retry).toHaveBeenCalledOnce();
});

test.each([
  [null, model],
  [accepted, null],
  [{ ...accepted, text: '  ' }, model],
  [{ ...accepted, classLabel: null }, model],
  [{ ...accepted, classLabel: ' ' }, model],
  [{ ...accepted, confidence: NaN }, model],
  [{ ...accepted, confidence: Infinity }, model],
  [{ ...accepted, confidence: -.01 }, model],
  [{ ...accepted, confidence: 1.01 }, model],
  [{ ...accepted, modelVersion: 'different' }, model],
  [{ ...accepted, accepted: false, modelVersion: 'different' }, model],
  [{ ...accepted, accepted: false }, null],
])('invalid or stale result renders nothing: %j', (result, metadata) => {
  const { container } = render(<RecognitionResult result={result} model={metadata} />);
  expect(container).toBeEmptyDOMElement();
});

test('rerender clears stale result and removes outdated model warning', () => {
  const rendered = render(<RecognitionResult result={accepted} model={{ ...model, demoReady: false, artifactKind: 'pilot' }} />);
  expect(screen.getByRole('note')).toBeVisible();
  rendered.rerender(<RecognitionResult result={accepted} model={model} />);
  expect(screen.queryByRole('note')).not.toBeInTheDocument();
  rendered.rerender(<RecognitionResult result={{ ...accepted, accepted: false }} model={model} />);
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
});

test('backend text is shown as inert text, without executing HTML', () => {
  const input = '<img src=x onerror=alert(1)> & xin chào';
  const { container } = render(<RecognitionResult result={{ ...accepted, text: input }} model={model} />);
  expect(screen.getByText(input)).toBeVisible();
  expect(container.querySelector('img')).toBeNull();
});

test('T109 supported meanings show Vietnamese display text instead of meaning IDs', () => {
  render(<RecognitionResult result={accepted} model={{ ...model, artifactKind: 'pilot', demoReady: false,
    meanings: ['GIAY_TO', 'NHAN'], meaningDisplayTexts: { GIAY_TO: 'Giấy tờ (giấy)', NHAN: 'Nhận' } }} />);
  expect(screen.getByText('Ý nghĩa hỗ trợ: Giấy tờ (giấy), Nhận')).toBeVisible();
  expect(screen.queryByText(/GIAY_TO/)).not.toBeInTheDocument();
});

test('T109 falls back to the meaning ID only when an older artifact has no display text', () => {
  render(<RecognitionResult result={accepted} model={{ ...model, artifactKind: 'pilot', demoReady: false,
    meanings: ['GIAY_TO', 'NHAN'], meaningDisplayTexts: { NHAN: 'Nhận' } }} />);
  expect(screen.getByText('Ý nghĩa hỗ trợ: GIAY_TO, Nhận')).toBeVisible();
});
