// apps/web/src/features/recognition/CameraRecorder.tsx - Giao dien xem truoc va dieu khien mot doan quay.
import { useEffect, useRef, type RefObject } from 'react';
import { cameraErrors, vi } from '../../content/vi';
import { type CameraView, type CameraSession } from './cameraSession';
import { useCameraCapture } from './useCameraCapture';

function CameraViewport({ videoRef, active }: { videoRef: RefObject<HTMLVideoElement | null>; active: boolean }) {
  return <div className={`camera-viewport ${active ? 'camera-active' : ''}`}>
    <video ref={videoRef} autoPlay muted playsInline aria-label={vi.preview} />
    {!active && <div className="camera-placeholder"><span className="camera-glyph" aria-hidden="true" />
      <p>Khuôn mặt và hai tay<br />trong khung hình</p></div>}
    <div className="framing-guide" aria-hidden="true"><i /><i /><i /><i /></div>
  </div>;
}

function CameraControls({ session, view, enable }: { session: CameraSession; view: CameraView; enable: () => void }) {
  return <div className="capture-controls" role="group" aria-label="Điều khiển camera">
    {(view.phase === 'idle' || view.phase === 'error') && <button className="primary-button" onClick={enable}>{view.phase === 'error' ? 'Thử lại' : 'Bật camera'}</button>}
    {view.phase === 'permission' && <button className="quiet-button" onClick={() => session.cancel()}>Hủy yêu cầu</button>}
    {(view.phase === 'preview' || view.phase === 'captured') && <button className="primary-button" onClick={() => session.record()}><span className="record-dot" aria-hidden="true" />{view.phase === 'captured' ? 'Quay lại' : 'Quay ký hiệu'}</button>}
    {view.phase === 'recording' && <button className="primary-button stop-button" onClick={() => session.stop()}><span className="stop-mark" aria-hidden="true" />Kết thúc</button>}
    {view.phase === 'stopping' && <span className="finishing-label">Đang hoàn tất…</span>}
    {(view.phase === 'recording' || view.phase === 'stopping' || view.phase === 'captured') && <button className="quiet-button" onClick={() => session.cancel()}>Hủy đoạn quay</button>}
    {['preview', 'recording', 'stopping', 'captured'].includes(view.phase) && <button className="quiet-button camera-off" onClick={() => session.reset()}>Tắt camera</button>}
  </div>;
}

function CaptureFeedback({ view }: { view: CameraView }) {
  if (view.phase === 'error') {
    const [title, guidance] = cameraErrors[view.error];
    return <div className="capture-feedback error-feedback" role="alert"><h3>{title}</h3><p>{guidance}</p></div>;
  }
  if (view.phase === 'captured') return <div className="capture-feedback"><h3>Đã quay xong</h3>
    <p>Đoạn quay dài {(view.durationMs / 1000).toFixed(1)} giây đã sẵn sàng và chưa được gửi đi. Bạn có thể quay lại hoặc hủy.</p></div>;
  return <div className="capture-feedback"><p>{view.phase === 'recording' ? 'Thực hiện ký hiệu rồi chọn Kết thúc. Đoạn quay tự dừng sau 5 giây.' : 'Giữ hai tay và phần thân trên trong khung. Bật camera chỉ mở hình xem trước.'}</p></div>;
}

export function CameraRecorder() {
  const { view, session, videoRef } = useCameraCapture();
  const panel = useRef<HTMLElement>(null);
  const previousPhase = useRef(view.phase);
  const active = ['preview', 'recording', 'stopping', 'captured'].includes(view.phase);
  useEffect(() => {
    if (previousPhase.current !== view.phase) {
      panel.current?.querySelector<HTMLButtonElement>('.capture-controls button')?.focus();
    }
    previousPhase.current = view.phase;
  }, [view.phase]);
  return <section ref={panel} className="camera-workspace" aria-labelledby="camera-heading">
    <div className="workspace-heading"><h2 id="camera-heading">Một ký hiệu, một lần quay.</h2>
      <span className={`status-badge status-${view.phase}`} role="status"><span aria-hidden="true" />{vi.states[view.phase]}</span></div>
    <div className="capture-layout">
      <CameraViewport videoRef={videoRef} active={active} />
      <CameraControls session={session} view={view} enable={() => void session.enable(videoRef.current)} />
      <section className="translation-panel" aria-labelledby="translation-heading">
        <h3 id="translation-heading">Văn bản dịch</h3><p className="translation-empty">Chưa có bản dịch.</p>
      </section>
      <CaptureFeedback view={view} /><p className="privacy-note">{vi.privacy}</p>
    </div>
  </section>;
}
