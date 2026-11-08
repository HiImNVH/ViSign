// T106: luong dich truc tiep qua hook + giao dien that, voi bo phat hien, MediaRecorder va API gia lap.
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { CameraGuidance, LiveCamera } from '../../src/features/live/LiveCamera';
import { useLiveRecognition } from '../../src/features/live/useLiveRecognition';
import type { PresenceDetectorFactory, PresenceFrame } from '../../src/features/live/presenceDetector';
import { InferenceApiError } from '../../src/services/inferenceApi';
import type { RecognitionApi } from '../../src/features/recognition/useRecognition';
import type { ModelInfo, PredictionResponse } from '../../src/types/inference-api';

const model: ModelInfo = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'test',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1', meanings: ['GIAY_TO', 'NHAN'],
  acceptanceThreshold: .5, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
const reply = (text: string, accepted = true): PredictionResponse => ({
  requestId: crypto.randomUUID(), text: accepted ? text : 'Không nhận diện được', classLabel: accepted ? 'NHAN_HCM_1' : null,
  confidence: accepted ? .8 : .3, accepted, modelVersion: model.modelVersion, processingTimeMs: 40,
});

class FakeRecorder extends EventTarget {
  static instances: FakeRecorder[] = [];
  static isTypeSupported = () => true;
  state = 'inactive';
  mimeType = 'video/webm;codecs=vp8';
  constructor() { super(); FakeRecorder.instances.push(this); }
  start() { this.state = 'recording'; }
  stop() {
    this.state = 'inactive';
    // Trinh duyet phat dataavailable roi stop sau khi dung
    queueMicrotask(() => {
      const event = new Event('dataavailable');
      Object.defineProperty(event, 'data', { value: new Blob([new Uint8Array(32)]) });
      this.dispatchEvent(event);
      this.dispatchEvent(new Event('stop'));
    });
  }
}

let clock = 0;
let current: PresenceFrame;
let api: RecognitionApi;
let track: EventTarget & { readyState: string; stop: ReturnType<typeof vi.fn> };
let factory: PresenceDetectorFactory;
let mediaDevicesDescriptor: PropertyDescriptor | undefined;

const nobody: PresenceFrame = { person: false, face: false, hands: 0, motion: 0 };
const ready = (motion = 0): PresenceFrame => ({ person: true, face: true, hands: 2, motion });

function Harness() {
  const live = useLiveRecognition(api, factory);
  return <><CameraGuidance live={live} /><LiveCamera live={live} /></>;
}

const status = () => screen.getByRole('status');
async function tick(ms = 120) { await act(async () => { clock += ms; await new Promise(resolve => setTimeout(resolve, 110)); }); }
async function show(frame: PresenceFrame, ticks = 2, ms = 120) { current = frame; for (let i = 0; i < ticks; i++) await tick(ms); }

async function start() {
  render(<Harness />);
  expect(status()).toHaveTextContent('Đang tắt');
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(status()).toHaveTextContent('Không phát hiện người'));
}

async function signOnce() {
  await show(ready(0), 1);
  await show(ready(.05), 6);
  await waitFor(() => expect(status()).toHaveTextContent('Đang ghi ký hiệu'));
  await show(ready(0), 1, 800);
}

beforeEach(() => {
  clock = 0;
  current = nobody;
  FakeRecorder.instances = [];
  mediaDevicesDescriptor = Object.getOwnPropertyDescriptor(navigator, 'mediaDevices');
  track = Object.assign(new EventTarget(), { readyState: 'live', stop: vi.fn() });
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: vi.fn().mockResolvedValue(stream) } });
  vi.stubGlobal('isSecureContext', true);
  vi.stubGlobal('MediaRecorder', FakeRecorder);
  vi.spyOn(performance, 'now').mockImplementation(() => clock);
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  vi.spyOn(HTMLMediaElement.prototype, 'readyState', 'get').mockReturnValue(4);
  factory = vi.fn(async () => ({ detect: () => current, close: vi.fn() }));
  api = {
    modelInfo: vi.fn().mockResolvedValue({ data: model, requestId: 'meta' }),
    predict: vi.fn().mockResolvedValueOnce({ data: reply('Nhận'), requestId: 'p1' })
      .mockResolvedValueOnce({ data: reply('Giấy tờ'), requestId: 'p2' }),
  };
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  if (mediaDevicesDescriptor) Object.defineProperty(navigator, 'mediaDevices', mediaDevicesDescriptor);
  else Reflect.deleteProperty(navigator, 'mediaDevices');
});

test('status follows person, face and hands before anything is recorded', async () => {
  await start();
  await show({ person: true, face: false, hands: 0, motion: 0 });
  expect(status()).toHaveTextContent('Chưa thấy đủ mặt và tay');
  expect(screen.getByRole('list', { name: 'Trạng thái phát hiện' })).toHaveTextContent('Người: có');
  await show(ready(0));
  expect(status()).toHaveTextContent('Sẵn sàng');
  expect(FakeRecorder.instances).toHaveLength(0);
  expect(api.predict).not.toHaveBeenCalled();
});

test('a sign is recorded, sent automatically and appended; the next sign continues without clicks', async () => {
  await start();
  await signOnce();
  await waitFor(() => expect(status()).toHaveTextContent('Đã dịch'));
  expect(api.predict).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveTextContent('Nhận');
  await waitFor(() => expect(status()).toHaveTextContent('Sẵn sàng'), { timeout: 3000 });
  await signOnce();
  await waitFor(() => expect(api.predict).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(screen.getByRole('region', { name: 'Bản dịch trực tiếp' })).toHaveTextContent('Nhận Giấy tờ'));
});

test('a brief hand twitch is discarded and never uploaded', async () => {
  await start();
  await show(ready(.05), 1);
  await waitFor(() => expect(status()).toHaveTextContent('Đang ghi ký hiệu'));
  await show(ready(0), 1, 800);
  await waitFor(() => expect(status()).toHaveTextContent('Sẵn sàng'));
  expect(api.predict).not.toHaveBeenCalled();
});

test('a rejected sign shows its own status and leaves the transcript unchanged', async () => {
  vi.mocked(api.predict).mockReset().mockResolvedValue({ data: reply('', false), requestId: 'r' });
  await start();
  await signOnce();
  await waitFor(() => expect(status()).toHaveTextContent('Không nhận diện được'));
  expect(screen.queryByRole('region', { name: 'Bản dịch trực tiếp' })).not.toBeInTheDocument();
  await waitFor(() => expect(status()).toHaveTextContent('Sẵn sàng'), { timeout: 3000 });
});

test('a busy service shows an error, then returns to listening without resending', async () => {
  vi.mocked(api.predict).mockReset().mockRejectedValue(new InferenceApiError('http', 'busy', 503, 'SERVICE_BUSY'));
  await start();
  await signOnce();
  await waitFor(() => expect(status()).toHaveTextContent('Lỗi'));
  expect(screen.getByRole('alert')).toHaveTextContent('Dịch vụ đang bận');
  await waitFor(() => expect(status()).toHaveTextContent('Sẵn sàng'), { timeout: 4000 });
  expect(api.predict).toHaveBeenCalledTimes(1);
});

test('pause stops recording until resumed; camera off releases the device', async () => {
  await start();
  fireEvent.click(screen.getByRole('button', { name: 'Tạm dừng' }));
  expect(status()).toHaveTextContent('Tạm dừng');
  await show(ready(.05), 3);
  expect(FakeRecorder.instances).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục' }));
  await show(ready(.05), 2);
  await waitFor(() => expect(status()).toHaveTextContent('Đang ghi ký hiệu'));
  fireEvent.click(screen.getByRole('button', { name: 'Tắt camera' }));
  expect(status()).toHaveTextContent('Đang tắt');
  expect(track.stop).toHaveBeenCalled();
  expect(api.predict).not.toHaveBeenCalled();
});

test('no segment starts while model metadata is unavailable', async () => {
  vi.mocked(api.modelInfo).mockReset().mockRejectedValue(new InferenceApiError('network', 'x'));
  await start();
  await show(ready(.05), 3);
  expect(FakeRecorder.instances).toHaveLength(0);
  expect(screen.getByRole('button', { name: 'Thử kết nối lại' })).toBeVisible();
});

test('detector loading failure shows an error with retry', async () => {
  factory = vi.fn().mockRejectedValue(new Error('wasm'));
  render(<Harness />);
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(status()).toHaveTextContent('Lỗi'));
  expect(screen.getByRole('alert')).toHaveTextContent('Không nạp được bộ phát hiện');
  expect(screen.getByRole('button', { name: 'Thử lại' })).toBeVisible();
});

test('denied camera permission shows the error state and retry', async () => {
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true,
    value: { getUserMedia: vi.fn().mockRejectedValue(new DOMException('no', 'NotAllowedError')) } });
  render(<Harness />);
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(status()).toHaveTextContent('Lỗi'));
  expect(screen.getByRole('alert')).toHaveTextContent('Chưa có quyền sử dụng camera');
  expect(screen.getByRole('button', { name: 'Thử lại' })).toHaveFocus();
});
