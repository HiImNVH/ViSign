// apps/web/tests/recognition/recognition-flow.test.tsx - Kiem tra React StrictMode, focus va don camera.
import { StrictMode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { CameraRecorder } from './ManualRecorder';
import { useCameraCapture } from '../../src/features/recognition/useCameraCapture';

function CameraRecorderHarness() {
  const camera = useCameraCapture();
  return <CameraRecorder controller={{
    camera: { view: camera.view, videoRef: camera.videoRef }, state: camera.view,
    model: { status: 'loading' }, compatibilityError: null, transcript: [],
    enableCamera: () => camera.session.enable(camera.videoRef.current),
    startRecording: () => camera.session.record(), stopRecording: () => camera.session.stop(),
    submit: async () => {}, cancel: () => camera.session.cancel(), reset: () => camera.session.reset(),
    reloadModelInfo: () => {},
  }} />;
}

const track = Object.assign(new EventTarget(), { readyState: 'live', stop: vi.fn() });
const stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
const getUserMedia = vi.fn<() => Promise<MediaStream>>();

beforeEach(() => {
  getUserMedia.mockReset().mockResolvedValue(stream); track.stop.mockClear();
  vi.stubGlobal('isSecureContext', true);
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } });
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

async function openPreview() {
  const rendered = render(<StrictMode><CameraRecorderHarness /></StrictMode>);
  expect(getUserMedia).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng'));
  return rendered;
}

test('preview survives StrictMode and moves focus to capture then back to enable', async () => {
  await openPreview();
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: 'Quay ký hiệu' })).toHaveFocus();
  fireEvent.click(screen.getByRole('button', { name: 'Tắt camera' }));
  expect(track.stop).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: 'Bật camera' })).toHaveFocus();
});

test('unmount disconnects the preview and releases the device', async () => {
  const rendered = await openPreview();
  const video = screen.getByLabelText('Hình ảnh xem trước từ camera') as HTMLVideoElement;
  rendered.unmount();
  expect(track.stop).toHaveBeenCalledTimes(1);
  expect(video.srcObject).toBeNull();
});

test('pagehide resets UI and releases the camera', async () => {
  await openPreview();
  fireEvent(window, new Event('pagehide'));
  expect(track.stop).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('status')).toHaveTextContent('Camera chưa bật');
});

test('camera errors show safe Vietnamese guidance and a focused retry button', async () => {
  getUserMedia.mockRejectedValueOnce(new DOMException('private device detail', 'NotAllowedError'));
  render(<CameraRecorderHarness />);
  fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Chưa có quyền sử dụng camera'));
  expect(screen.getByRole('alert')).not.toHaveTextContent('private device detail');
  expect(screen.getByRole('button', { name: 'Thử lại' })).toHaveFocus();
  fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Camera sẵn sàng'));
});
