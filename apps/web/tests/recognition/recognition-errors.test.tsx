// CP4 T046: negative recognition flows across the real hook and camera UI.
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { CameraRecorder } from '../../src/features/recognition/CameraRecorder';
import { useRecognition } from '../../src/features/recognition/useRecognition';
import { InferenceApiError, createInferenceApi } from '../../src/services/inferenceApi';
import type { ModelInfo, PredictionResponse } from '../../src/types/inference-api';

type Api = Pick<ReturnType<typeof createInferenceApi>, 'modelInfo' | 'predict'>;
type PredictionReply = Awaited<ReturnType<Api['predict']>>;

const model: ModelInfo = {
  modelVersion: 'pilot-v1', artifactKind: 'pilot', datasetVersion: 'test',
  featureSchemaVersion: 'schema-v1', extractorVersion: 'extract-v1', meanings: ['Xin chào'],
  acceptanceThreshold: .7, macroF1: null, perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
const accepted: PredictionResponse = {
  requestId: 'prediction-id', text: 'Xin chào', classLabel: 'XIN_CHAO',
  confidence: .91, accepted: true, modelVersion: model.modelVersion, processingTimeMs: 50,
};

class FakeRecorder extends EventTarget {
  static instances: FakeRecorder[] = [];
  static isTypeSupported = () => true;
  state = 'inactive';
  mimeType = 'video/webm;codecs=vp8';
  constructor() { super(); FakeRecorder.instances.push(this); }
  start() { this.state = 'recording'; }
  stop() { this.state = 'inactive'; }
  chunk() {
    const event = new Event('dataavailable');
    Object.defineProperty(event, 'data', { value: new Blob([new Uint8Array(16)]) });
    this.dispatchEvent(event);
  }
  finish() { this.dispatchEvent(new Event('stop')); }
}

let clock = 0;
let api: Api;
let getUserMedia: ReturnType<typeof vi.fn<() => Promise<MediaStream>>>;
let mediaDevicesDescriptor: PropertyDescriptor | undefined;
let track: EventTarget & { readyState: string; stop: ReturnType<typeof vi.fn> };
let stream: MediaStream;

function RecognitionHarness() {
  const controller = useRecognition(api);
  return <CameraRecorder controller={controller} />;
}

beforeEach(() => {
  clock = 0;
  FakeRecorder.instances = [];
  mediaDevicesDescriptor = Object.getOwnPropertyDescriptor(navigator, 'mediaDevices');
  track = Object.assign(new EventTarget(), { readyState: 'live', stop: vi.fn() });
  stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
  getUserMedia = vi.fn<() => Promise<MediaStream>>().mockResolvedValue(stream);
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } });
  vi.stubGlobal('isSecureContext', true);
  vi.stubGlobal('MediaRecorder', FakeRecorder);
  vi.spyOn(performance, 'now').mockImplementation(() => clock);
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  api = {
    modelInfo: vi.fn().mockResolvedValue({ data: model, requestId: 'metadata-id' }),
    predict: vi.fn().mockResolvedValue({ data: accepted, requestId: 'prediction-id' }),
  };
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  if (mediaDevicesDescriptor) Object.defineProperty(navigator, 'mediaDevices', mediaDevicesDescriptor);
  else Reflect.deleteProperty(navigator, 'mediaDevices');
});

async function preview() {
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng'));
}

async function capture() {
  await preview();
  fireEvent.click(screen.getByRole('button', { name: 'Quay ký hiệu' }));
  expect(screen.getByRole('status')).toHaveTextContent('Đang quay ký hiệu');
  clock += 500;
  fireEvent.click(screen.getByRole('button', { name: 'Kết thúc' }));
  const recorder = FakeRecorder.instances.at(-1);
  if (!recorder) throw new Error('Missing fake recorder');
  act(() => { recorder.chunk(); recorder.finish(); });
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Đã quay xong'));
}

test('denied camera permission provides safe Vietnamese guidance and recovers on explicit retry', async () => {
  getUserMedia.mockRejectedValueOnce(new DOMException('secret camera hardware info', 'NotAllowedError'));
  render(<RecognitionHarness />);
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Chưa có quyền sử dụng camera'));
  expect(screen.getByRole('alert')).toHaveTextContent('Cho phép camera trong cài đặt');
  expect(screen.getByRole('alert')).not.toHaveTextContent('secret camera hardware info');
  expect(api.predict).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng'));
  expect(getUserMedia).toHaveBeenCalledTimes(2);
});

test('cancel during permission pending keeps camera off and releases a late stream', async () => {
  let resolveStream!: (value: MediaStream) => void;
  getUserMedia.mockImplementationOnce(() => new Promise(resolve => { resolveStream = resolve; }));
  render(<RecognitionHarness />);
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  expect(screen.getByRole('status')).toHaveTextContent('Đang chờ quyền camera');
  fireEvent.click(screen.getByRole('button', { name: 'Hủy yêu cầu' }));
  expect(screen.getByRole('status')).toHaveTextContent('Camera chưa bật');
  await act(async () => { resolveStream(stream); await Promise.resolve(); });
  expect(track.stop).toHaveBeenCalledTimes(1);
  expect((screen.getByLabelText('Hình ảnh xem trước từ camera') as HTMLVideoElement).srcObject).toBeFalsy();
  expect(api.predict).not.toHaveBeenCalled();
});

test('cancel recording discards the capture and never submits a clip', async () => {
  render(<RecognitionHarness />);
  await preview();
  fireEvent.click(screen.getByRole('button', { name: 'Quay ký hiệu' }));
  fireEvent.click(screen.getByRole('button', { name: 'Hủy đoạn quay' }));
  expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng');
  expect(screen.queryByRole('button', { name: 'Gửi nhận diện' })).not.toBeInTheDocument();
  expect(api.predict).not.toHaveBeenCalled();
});

test('a rejected prediction never displays translation or resends the completed clip', async () => {
  vi.mocked(api.predict).mockResolvedValueOnce({
    data: { ...accepted, accepted: false, text: 'Xin chào', classLabel: 'XIN_CHAO', confidence: .2 },
    requestId: 'rejected-id',
  });
  render(<RecognitionHarness />);
  await capture();
  expect(api.predict).not.toHaveBeenCalled();
  screen.getByRole('button', { name: 'Gửi nhận diện' }).focus();
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
  await waitFor(() => expect(screen.getByText('Chưa nhận diện được ký hiệu. Hãy quay một ký hiệu mới.')).toBeVisible());
  const rejected = screen.getByRole('region', { name: 'Kết quả nhận diện' });
  expect(rejected).toHaveAttribute('aria-live', 'polite');
  expect(screen.getAllByRole('button', { name: 'Quay lại' })).toHaveLength(1);
  expect(screen.getByRole('button', { name: 'Quay lại' })).toHaveFocus();
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Gửi nhận diện' })).not.toBeInTheDocument();
  expect(api.predict).toHaveBeenCalledTimes(1);
  screen.getByRole('button', { name: 'Quay lại' }).focus();
  fireEvent.click(screen.getByRole('button', { name: 'Quay lại' }));
  expect(FakeRecorder.instances).toHaveLength(2);
  expect(screen.getByRole('button', { name: 'Kết thúc' })).toHaveFocus();
  expect(screen.queryByText('Chưa nhận diện được ký hiệu. Hãy quay một ký hiệu mới.')).not.toBeInTheDocument();
  expect(api.predict).toHaveBeenCalledTimes(1);
  clock += 500;
  fireEvent.click(screen.getByRole('button', { name: 'Kết thúc' }));
  act(() => { FakeRecorder.instances[1]!.chunk(); FakeRecorder.instances[1]!.finish(); });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeEnabled());
  expect(api.predict).toHaveBeenCalledTimes(1);
});

test.each(['SERVICE_BUSY', 'MODEL_NOT_READY'] as const)(
  'a %s service error is safe and retries only after a second explicit submit', async code => {
    vi.mocked(api.predict).mockRejectedValueOnce(new InferenceApiError('http', 'private-request', 503, code, '2'));
    render(<RecognitionHarness />);
    await capture();
    fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    const guidance = code === 'SERVICE_BUSY' ? 'Dịch vụ đang bận.' : 'Dịch vụ nhận diện chưa sẵn sàng.';
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(guidance));
    expect(screen.getByRole('alert')).not.toHaveTextContent(code);
    expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
    expect(api.predict).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    await waitFor(() => expect(screen.getByRole('region', { name: 'Văn bản dịch' })).toHaveTextContent('Xin chào'));
    expect(api.predict).toHaveBeenCalledTimes(2);
  },
);

test('metadata outage blocks upload; explicit reconnect reloads metadata without auto-upload', async () => {
  vi.mocked(api.modelInfo).mockRejectedValueOnce(new InferenceApiError('http', 'meta-id', 503, 'MODEL_NOT_READY'));
  render(<RecognitionHarness />);
  await capture();
  await waitFor(() => expect(screen.getByText('Chưa kết nối được dịch vụ nhận diện. Bạn vẫn có thể quay ký hiệu.')).toBeVisible());
  expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeDisabled();
  expect(api.predict).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Thử kết nối lại' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeEnabled());
  expect(api.modelInfo).toHaveBeenCalledTimes(2);
  expect(api.predict).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
  await waitFor(() => expect(screen.getByRole('region', { name: 'Văn bản dịch' })).toBeVisible());
  expect(api.predict).toHaveBeenCalledTimes(1);
});

test('cancel during upload aborts it and ignores its late accepted response', async () => {
  let resolvePrediction!: (value: PredictionReply) => void;
  vi.mocked(api.predict).mockImplementationOnce(() => new Promise(resolve => { resolvePrediction = resolve; }));
  render(<RecognitionHarness />);
  await capture();
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
  expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toHaveTextContent('Đang nhận diện…');
  const signal = vi.mocked(api.predict).mock.calls[0]?.[1]?.signal;
  expect(signal?.aborted).toBe(false);
  fireEvent.click(screen.getByRole('button', { name: 'Hủy đoạn quay' }));
  expect(signal?.aborted).toBe(true);
  expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng');
  await act(async () => { resolvePrediction({ data: accepted, requestId: 'late-id' }); await Promise.resolve(); });
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(api.predict).toHaveBeenCalledTimes(1);
});

test.each([404, 405])('prediction HTTP %i renders safe compatibility guidance without automatically resubmitting', async status => {
  const kind = status === 404 ? 'route-not-found' : 'method-not-allowed';
  const safeText = status === 404 ? 'Không tìm thấy chức năng API.' : 'Ứng dụng và dịch vụ chưa tương thích.';
  vi.mocked(api.predict).mockRejectedValueOnce(new InferenceApiError(kind, 'raw-secret-request', status,
    'SERVER_SECRET'));
  render(<RecognitionHarness />);
  await capture();
  fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(safeText));
  expect(screen.getByRole('alert')).not.toHaveTextContent('SERVER_SECRET');
  expect(api.predict).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole('region', { name: 'Văn bản dịch' })).not.toBeInTheDocument();
  if (status === 404) {
    expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng');
    expect(screen.queryByRole('button', { name: 'Gửi nhận diện' })).not.toBeInTheDocument();
  } else {
    expect(screen.getByRole('status')).toHaveTextContent('Đã quay xong');
    fireEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    await waitFor(() => expect(api.predict).toHaveBeenCalledTimes(2));
  }
});

test.each([404, 405])('metadata HTTP %i blocks upload with safe guidance until manual metadata retry', async status => {
  vi.mocked(api.modelInfo).mockRejectedValueOnce(new InferenceApiError(
    status === 404 ? 'route-not-found' : 'method-not-allowed', 'secret', status, 'secret-code'));
  render(<RecognitionHarness />);
  await capture();
  expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeDisabled();
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(status === 404
    ? 'Không tìm thấy chức năng API.' : 'Ứng dụng và dịch vụ chưa tương thích.'));
  expect(screen.getByRole('alert')).not.toHaveTextContent('secret-code');
  expect(api.predict).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Thử kết nối lại' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeEnabled());
  expect(api.predict).not.toHaveBeenCalled();
});
