import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import AdminTraining from '../../src/features/admin/AdminTraining';
import { MAX_ADMIN_CLIP_BYTES } from '../../src/services/adminApi';

const idle = { phase: 'idle', runId: null, sampleTotal: 0, accepted: 0, updatedAt: '2026-11-08T02:00:00Z' };
const ready = { ...idle, phase: 'ready', runId: 'pilot-001', sampleTotal: 6, accepted: 6, datasetVersion: 'manifest-v1', featureSchemaVersion: 'v0.3' };
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { 'Content-Type': 'application/json' },
});

async function login() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Mã admin'), 'test-secret');
  await user.click(screen.getByRole('button', { name: 'Kết nối' }));
  return user;
}

function mockApi(overrides: (path: string, method: string) => Response = () => json(idle)) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) =>
    overrides(String(input), init?.method ?? 'GET'));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe('T081 / T082 internal admin training', () => {
  it('requires a token before exposing actions and sends it only as a bearer header', async () => {
    const fetchMock = mockApi();
    render(<AdminTraining />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Kết nối' }));
    expect(screen.getByRole('status')).toHaveTextContent('Vui lòng nhập mã admin');
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.queryByText('Kiểm tra clip', { exact: true })).not.toBeInTheDocument();
    await login();
    await screen.findByText('Chưa có lần chạy pilot');
    const [path, options] = fetchMock.mock.calls[0]!;
    expect(path).toBe('/api/admin/pilot');
    expect(options?.headers).toEqual({ Authorization: 'Bearer test-secret' });
    expect(options?.credentials).toBe('omit');
    expect(screen.getByLabelText('Mã admin')).toHaveValue('');
    expect(localStorage.length).toBe(0);
    await user.click(screen.getByRole('button', { name: 'Ngắt kết nối' }));
    expect(screen.getByRole('status')).toHaveTextContent('Đã ngắt kết nối admin.');
    expect(screen.queryByRole('button', { name: 'Chạy kiểm tra' })).not.toBeInTheDocument();
  });

  it('inspects an MP4 as multipart video and downloads the returned ZIP', async () => {
    const fetchMock = mockApi((path) => path.endsWith('/inspect')
      ? new Response(new Blob(['PK-zip'], { type: 'application/zip' }), { status: 200 })
      : json(idle));
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:admin-result') });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    render(<AdminTraining />);
    const user = await login();
    await screen.findByText('Chưa có lần chạy pilot');
    expect(screen.getByRole('button', { name: 'Tải ZIP kết quả' })).toBeDisabled();
    const clip = new File(['video-binary'], 'sample.mp4', { type: 'video/mp4' });
    fireEvent.change(screen.getByLabelText('Video cần kiểm tra'), { target: { files: [clip] } });
    await user.click(screen.getByRole('button', { name: 'Chạy kiểm tra' }));
    expect(await screen.findByText(/ZIP đã sẵn sàng để tải/)).toBeVisible();
    const [, options] = fetchMock.mock.calls.find(([path]) => String(path).endsWith('/inspect'))!;
    expect(options?.method).toBe('POST');
    expect(options?.body).toBeInstanceOf(FormData);
    expect((options?.body as FormData).get('video')).toBe(clip);
    expect(options?.headers).toEqual({ Authorization: 'Bearer test-secret' });
    await user.click(screen.getByRole('button', { name: 'Tải ZIP kết quả' }));
    expect(click).toHaveBeenCalled();
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(document.querySelector('a[download]')).not.toBeInTheDocument();
  });

  it('rejects invalid/oversized clips locally without uploading them', async () => {
    const fetchMock = mockApi();
    render(<AdminTraining />);
    const user = await login();
    await screen.findByText('Chưa có lần chạy pilot');
    const clipInput = screen.getByLabelText('Video cần kiểm tra');
    fireEvent.change(clipInput, { target: { files: [new File(['a'], 'bad.exe')] } });
    await user.click(screen.getByRole('button', { name: 'Chạy kiểm tra' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Chỉ nhận MP4/WebM');
    const largeClip = new File(['a'], 'large.webm');
    Object.defineProperty(largeClip, 'size', { value: MAX_ADMIN_CLIP_BYTES + 1 });
    fireEvent.change(clipInput, { target: { files: [largeClip] } });
    await user.click(screen.getByRole('button', { name: 'Chạy kiểm tra' }));
    expect(fetchMock.mock.calls.some(([path]) => String(path).endsWith('/inspect'))).toBe(false);
  });

  it('runs preflight before enabling train and displays current metrics', async () => {
    let pilot: Record<string, unknown> = idle;
    const fetchMock = mockApi((path, method) => {
      if (path.endsWith('/pilot/prepare') && method === 'POST') {
        pilot = { ...ready, phase: 'preparing' };
        return json(pilot, 202);
      }
      if (path.endsWith('/pilot/train') && method === 'POST') return json({ ...ready, phase: 'training', epoch: 0, epochs: 10 }, 202);
      return json(pilot);
    });
    render(<AdminTraining />);
    const user = await login();
    await screen.findByText('Chưa có lần chạy pilot');
    expect(screen.getByRole('button', { name: 'Bắt đầu train' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Chạy preflight' }));
    expect(await screen.findByText('Đang kiểm tra dữ liệu và trích xuất đặc trưng')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Chạy preflight' })).toBeDisabled();
    pilot = ready;
    await user.click(screen.getByRole('button', { name: 'Tải lại trạng thái' }));
    await screen.findByText('Dữ liệu đã sẵn sàng để huấn luyện');
    expect(screen.getByText('manifest-v1')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Bắt đầu train' }));
    expect(await screen.findByText('Đang huấn luyện pilot')).toBeVisible();
    expect(fetchMock.mock.calls.map(([path]) => path)).toContain('/api/admin/pilot/prepare');
    expect(fetchMock.mock.calls.map(([path]) => path)).toContain('/api/admin/pilot/train');
  });

  it('handles active-job conflict (409) with a Vietnamese state', async () => {
    mockApi((path) => path.endsWith('/prepare') ? json({ detail: 'secret/private/path' }, 409) : json(idle));
    render(<AdminTraining />);
    const user = await login();
    await screen.findByText('Chưa có lần chạy pilot');
    await user.click(screen.getByRole('button', { name: 'Chạy preflight' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('công việc khác chạy (409)');
    expect(screen.queryByText(/secret\/private/)).not.toBeInTheDocument();
  });

  it('displays newest-first history and safe W&B online/offline evidence', async () => {
    mockApi((path) => path.endsWith('/history') ? json([
      { ...ready, runId: 'older-offline', phase: 'complete', updatedAt: '2026-11-01T00:00:00Z', wandbMode: 'offline', wandbRunId: 'off001', metrics: { accuracy: 0.75, macroF1: 0.7 } },
      { ...ready, runId: 'newer-online', phase: 'complete', updatedAt: '2026-11-08T00:00:00Z', wandbMode: 'online', wandbRunId: 'on001', wandbUrl: 'https://wandb.ai/team/visign/runs/on001' },
      { ...ready, runId: 'unsafe-link', phase: 'complete', updatedAt: '2026-11-04T00:00:00Z', wandbMode: 'online', wandbUrl: 'javascript:alert(1)' },
    ]) : json(idle));
    render(<AdminTraining />);
    const user = await login();
    await screen.findByText('Chưa có lần chạy pilot');
    await user.click(screen.getByRole('button', { name: 'Xem lịch sử train' }));
    const history = within(await screen.findByRole('region', { name: 'Lịch sử train' }));
    const entries = history.getAllByRole('listitem');
    expect(within(entries[0]!).getByText('newer-online')).toBeVisible();
    expect(within(entries[1]!).getByText('unsafe-link')).toBeVisible();
    expect(within(entries[2]!).getByText('older-offline')).toBeVisible();
    expect(history.getByText(/Log offline/)).toBeVisible();
    expect(history.getByText('Accuracy:', { exact: false })).toBeVisible();
    const link = history.getByRole('link', { name: /Mở biểu đồ W&B/ });
    expect(link).toHaveAttribute('href', 'https://wandb.ai/team/visign/runs/on001');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(history.getAllByRole('link')).toHaveLength(1);
  });

  it('clears credentials on 401, and shows disabled (404) or unavailable (503) messages', async () => {
    const fetchMock = mockApi(() => json({ detail: 'Internal stacktrace token=bad' }, 401));
    const { unmount } = render(<AdminTraining />);
    await login();
    expect(await screen.findByText(/Mã admin không đúng hoặc đã hết hiệu lực/)).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Chạy preflight' })).not.toBeInTheDocument();
    unmount();
    fetchMock.mockImplementation(async () => json({ detail: 'secret' }, 404));
    const second = render(<AdminTraining />);
    await login();
    expect(await screen.findByRole('alert')).toHaveTextContent('chưa được bật trên backend (404)');
    second.unmount();
    fetchMock.mockImplementation(async () => json({ detail: 'secret' }, 503));
    render(<AdminTraining />);
    await login();
    expect(await screen.findByRole('alert')).toHaveTextContent('chưa sẵn sàng (503)');
    expect(screen.queryByText(/stacktrace|token=bad|secret/i)).not.toBeInTheDocument();
  });

  it('reports inspect timeout (504) without displaying an unsafe server detail', async () => {
    mockApi((path) => path.endsWith('/inspect') ? json({ detail: '/tmp/worker/token' }, 504) : json(idle));
    render(<AdminTraining />);
    const user = await login();
    await screen.findByText('Chưa có lần chạy pilot');
    fireEvent.change(screen.getByLabelText('Video cần kiểm tra'), { target: { files: [new File(['a'], 'clip.webm')] } });
    await user.click(screen.getByRole('button', { name: 'Chạy kiểm tra' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('quá thời gian cho phép (504)');
    expect(screen.queryByText(/\/tmp\/worker/)).not.toBeInTheDocument();
  });

  it('rejects malformed pilot responses without crashing', async () => {
    mockApi(() => json({ phase: 'succeeded', runId: 'bad' }));
    render(<AdminTraining />);
    await login();
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('không đúng định dạng'));
  });
});
