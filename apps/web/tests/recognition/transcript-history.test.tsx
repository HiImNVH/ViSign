import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { CameraRecorder } from '../../src/features/recognition/CameraRecorder';
import { HistoryPanel } from '../../src/features/recognition/HistoryPanel';
import { useRecognition } from '../../src/features/recognition/useRecognition';
import { HISTORY_STORAGE_KEY } from '../../src/features/recognition/translationHistory';
import type { ModelInfo, PredictionResponse } from '../../src/types/inference-api';
import type { createInferenceApi } from '../../src/services/inferenceApi';

type Api = Pick<ReturnType<typeof createInferenceApi>, 'modelInfo' | 'predict'>;
const info: ModelInfo = { modelVersion: 'v1', artifactKind: 'pilot', datasetVersion: 'd',
  featureSchemaVersion: 's', extractorVersion: 'e', meanings: ['Xin chào'],
  acceptanceThreshold: .7, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false };
const uuid = (n: number) => `123e4567-e89b-42d3-a456-42661417400${n}`;
const response = (n: number, text: string, accepted = true): PredictionResponse => ({
  requestId: uuid(n), text: accepted ? text : 'Không nhận diện được',
  classLabel: accepted ? 'LABEL' : null, confidence: .9, accepted, modelVersion: 'v1', processingTimeMs: 8,
});

class Recorder extends EventTarget {
  static instances: Recorder[] = [];
  static isTypeSupported = () => true;
  state = 'inactive'; mimeType = 'video/webm';
  constructor() { super(); Recorder.instances.push(this); }
  start() { this.state = 'recording'; }
  stop() { this.state = 'inactive'; }
  finish() {
    const chunk = new Event('dataavailable');
    Object.defineProperty(chunk, 'data', { value: new Blob(['test']) });
    this.dispatchEvent(chunk); this.dispatchEvent(new Event('stop'));
  }
}

let api: Api;
let clock = 0;
let mediaDevicesDescriptor: PropertyDescriptor | undefined;
let originalShowModal: typeof HTMLDialogElement.prototype.showModal;
let originalClose: typeof HTMLDialogElement.prototype.close;

function Harness() {
  const ctrl = useRecognition(api);
  return <><HistoryPanel history={ctrl.history} refreshHistory={ctrl.refreshHistory} clearHistory={ctrl.clearHistory} />
    <CameraRecorder controller={ctrl} /></>;
}

beforeEach(() => {
  localStorage.clear();
  clock = 0;
  Recorder.instances = [];
  mediaDevicesDescriptor = Object.getOwnPropertyDescriptor(navigator, 'mediaDevices');
  const track = Object.assign(new EventTarget(), { readyState: 'live', stop: vi.fn() });
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true,
    value: { getUserMedia: vi.fn().mockResolvedValue(stream) } });
  vi.stubGlobal('isSecureContext', true);
  vi.stubGlobal('MediaRecorder', Recorder);
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  vi.spyOn(performance, 'now').mockImplementation(() => clock);
  originalShowModal = HTMLDialogElement.prototype.showModal;
  originalClose = HTMLDialogElement.prototype.close;
  // JSDOM dialog elements lack showModal/close; mimic open state for user-level tests.
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
  api = { modelInfo: vi.fn().mockResolvedValue({ data: info, requestId: 'model' }),
    predict: vi.fn().mockResolvedValue({ data: response(0, 'Xin chào'), requestId: uuid(0) }) };
});

afterEach(() => {
  vi.restoreAllMocks(); vi.unstubAllGlobals(); localStorage.clear();
  HTMLDialogElement.prototype.showModal = originalShowModal;
  HTMLDialogElement.prototype.close = originalClose;
  if (mediaDevicesDescriptor) Object.defineProperty(navigator, 'mediaDevices', mediaDevicesDescriptor);
  else Reflect.deleteProperty(navigator, 'mediaDevices');
});

async function record(first = false) {
  if (first) {
    fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng'));
  }
  fireEvent.click(screen.getByRole('button', { name: 'Quay ký hiệu' }));
  clock += 500;
  fireEvent.click(screen.getByRole('button', { name: 'Kết thúc' }));
  act(() => Recorder.instances.at(-1)!.finish());
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Đã quay xong'));
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
}

test('accepted results build chronological aria-live transcript; rejection leaves transcript unchanged', async () => {
  vi.mocked(api.predict)
    .mockResolvedValueOnce({ data: response(0, 'Xin chào'), requestId: uuid(0) })
    .mockResolvedValueOnce({ data: response(1, 'Cảm ơn'), requestId: uuid(1) })
    .mockResolvedValueOnce({ data: response(2, '', false), requestId: uuid(2) });
  render(<Harness />);
  expect(screen.queryByRole('region', { name: 'Bản dịch trực tiếp' })).not.toBeInTheDocument();
  await record(true);
  await waitFor(() => expect(screen.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveTextContent('Xin chào'));
  fireEvent.click(screen.getByRole('button', { name: 'Quay lại' }));
  clock += 500;
  fireEvent.click(screen.getByRole('button', { name: 'Kết thúc' }));
  act(() => Recorder.instances.at(-1)!.finish());
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
  await waitFor(() => expect(screen.getByRole('region', { name: 'Bản dịch trực tiếp' })
    .querySelector('[aria-live]')).toHaveTextContent('Xin chào Cảm ơn'));
  fireEvent.click(screen.getByRole('button', { name: 'Quay lại' }));
  clock += 500;
  fireEvent.click(screen.getByRole('button', { name: 'Kết thúc' }));
  act(() => Recorder.instances.at(-1)!.finish());
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
  await waitFor(() => expect(screen.getByRole('region', { name: 'Kết quả nhận diện' })).toBeInTheDocument());
  expect(screen.getByRole('region', { name: 'Bản dịch trực tiếp' }).querySelector('[aria-live]'))
    .toHaveTextContent('Xin chào Cảm ơn');
  expect(JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY)!).entries).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: 'Lịch sử' }));
  const dialog = within(screen.getByRole('dialog', { name: 'Lịch sử bản dịch' }));
  expect(dialog.getByText('Chỉ lưu trên thiết bị này trong 24 giờ. Không gửi lịch sử lên máy chủ.')).toBeInTheDocument();
  expect(dialog.getByText(/chưa phải câu dịch có ngữ pháp/)).toBeInTheDocument();
  expect(dialog.getAllByText('Độ tin cậy:', { exact: false })).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: 'Xoá toàn bộ lịch sử' }));
  fireEvent.click(screen.getByRole('button', { name: 'Xác nhận xoá' }));
  expect(screen.queryByRole('region', { name: 'Bản dịch trực tiếp' })).not.toBeInTheDocument();
  expect(localStorage.getItem(HISTORY_STORAGE_KEY)).toBeNull();
});

test('blocked local storage does not block live transcription, and history explains unavailability', async () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('storage blocked'); });
  render(<Harness />);
  await record(true);
  await waitFor(() => expect(screen.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveTextContent('Xin chào'));
  fireEvent.click(screen.getByRole('button', { name: 'Lịch sử' }));
  expect(screen.getByRole('alert')).toHaveTextContent('Bộ nhớ trình duyệt không khả dụng.');
  expect(screen.getByText('Chưa có bản dịch được lưu.')).toBeInTheDocument();
});
