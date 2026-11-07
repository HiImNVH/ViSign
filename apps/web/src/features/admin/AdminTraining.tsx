import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { AdminApiError, adminErrorMessage, createAdminApi, MAX_ADMIN_CLIP_BYTES } from '../../services/adminApi';
import PilotPanel from './PilotPanel';
import '../../styles.css';
import './admin.css';

export default function AdminTraining() {
  const [code, setCode] = useState('');
  const [token, setToken] = useState('');
  const [notice, setNotice] = useState('');
  const [video, setVideo] = useState<File | null>(null);
  const [archive, setArchive] = useState<Blob | null>(null);
  const [inspecting, setInspecting] = useState(false);
  const [inspectError, setInspectError] = useState('');
  const requestRef = useRef<AbortController | null>(null);

  useEffect(() => () => requestRef.current?.abort(), []);

  const disconnect = useCallback((message: string) => {
    requestRef.current?.abort();
    setToken('');
    setCode('');
    setArchive(null);
    setVideo(null);
    setInspectError('');
    setNotice(message);
  }, []);

  const onUnauthorized = useCallback(() => {
    disconnect('Mã admin không đúng hoặc đã hết hiệu lực (401). Vui lòng nhập lại.');
  }, [disconnect]);

  function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!code.trim()) { setNotice('Vui lòng nhập mã admin.'); return; }
    requestRef.current?.abort();
    setToken(code.trim());
    setCode('');
    setNotice('Đang xác minh quyền truy cập với backend…');
    setInspectError('');
    setArchive(null);
  }

  async function inspect() {
    if (!video || !token || inspecting) return;
    setInspectError('');
    setArchive(null);
    if (!/\.(mp4|webm)$/i.test(video.name) || !video.size || video.size > MAX_ADMIN_CLIP_BYTES) {
      setInspectError('Chỉ nhận MP4/WebM có dung lượng từ 1 byte đến 100 MiB.');
      return;
    }
    setInspecting(true);
    const controller = new AbortController();
    requestRef.current = controller;
    try {
      const zip = await createAdminApi(token).inspect(video, controller.signal);
      if (!controller.signal.aborted) setArchive(zip);
    } catch (error) {
      if (controller.signal.aborted) return;
      if (error instanceof AdminApiError && error.kind === 'unauthorized') onUnauthorized();
      else setInspectError(adminErrorMessage(error));
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
      setInspecting(false);
    }
  }

  function download() {
    if (!archive) return;
    const url = URL.createObjectURL(archive);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'visign-inspect-result.zip';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <main className="admin-page">
    <header className="admin-header">
      <div><strong>ViSign</strong><span>Công cụ quản trị nội bộ · Train model</span></div>
      <a href="/">← Trở về nhận diện</a>
    </header>
    <div className="admin-layout">
      <div className="admin-intro">
        <h1>Kiểm tra clip và huấn luyện pilot</h1>
        <p>Chỉ dành cho môi trường nội bộ đã bật <code>VISIGN_ADMIN_TOKEN</code> trên backend.</p>
      </div>
      <section className="admin-card" aria-labelledby="admin-auth-title">
        <h2 id="admin-auth-title">Quyền truy cập</h2>
        <form onSubmit={connect} className="admin-login" autoComplete="off">
          <label htmlFor="admin-token">Mã admin</label>
          <input id="admin-token" type="password" value={code} onChange={event => setCode(event.target.value)}
            autoComplete="off" placeholder="Nhập mã từ backend" />
          <button className="admin-primary" type="submit">{token ? 'Đổi mã' : 'Kết nối'}</button>
          {token && <button type="button" onClick={() => disconnect('Đã ngắt kết nối admin.')}>Ngắt kết nối</button>}
        </form>
        <p role="status" className="admin-note">{token ? 'Đã nhập mã. Backend sẽ kiểm tra quyền khi gọi API.' : notice || 'Nhập mã admin để mở công cụ.'}</p>
      </section>
      {token && <>
        <section className="admin-card" aria-labelledby="admin-inspect-title">
          <h2 id="admin-inspect-title">Kiểm tra clip</h2>
          <p className="admin-note">Chọn một tệp MP4/WebM, tối đa 100 MiB. Kết quả trả về là ZIP để tải về máy.</p>
          <label htmlFor="admin-clip">Video cần kiểm tra</label>
          <input id="admin-clip" type="file" accept=".mp4,.webm,video/mp4,video/webm" disabled={inspecting}
            onChange={event => {
              setVideo(event.target.files?.[0] ?? null);
              setArchive(null);
              setInspectError('');
            }} />
          <div className="admin-actions">
            <button type="button" className="admin-primary" onClick={() => void inspect()} disabled={!video || inspecting}>
              {inspecting ? 'Đang kiểm tra…' : 'Chạy kiểm tra'}
            </button>
            <button type="button" disabled={!archive || inspecting} onClick={download}>Tải ZIP kết quả</button>
          </div>
          {inspecting && <p role="status">Backend đang xử lý clip. Không đóng trang cho đến khi hoàn tất.</p>}
          {archive && <p role="status" className="admin-success">Kiểm tra thành công. ZIP đã sẵn sàng để tải.</p>}
          {inspectError && <p role="alert" className="admin-warning">{inspectError}</p>}
        </section>
        <PilotPanel token={token} onUnauthorized={onUnauthorized} />
      </>}
    </div>
  </main>;
}
