// apps/web/src/features/recognition/CameraRecorder.tsx - Giao dien xem truoc va dieu khien mot doan quay.
import { useEffect, useRef, type ReactNode, type RefObject } from 'react';
import { cameraErrors, vi } from '../../content/vi';
import { type CameraView, type CameraSession } from './cameraSession';
import { useCameraCapture } from './useCameraCapture';
import { RecognitionOverlay, type CapturedRecognitionResult } from './RecognitionOverlay';

function CameraViewport({ videoRef, view, children }: { videoRef: RefObject<HTMLVideoElement | null>; view: CameraView; children: ReactNode }) {
  const active = ['preview', 'recording', 'stopping', 'captured'].includes(view.phase);
  return <div className={`camera-viewport ${active ? 'camera-active' : ''}`} data-phase={view.phase}>
    <video ref={videoRef} autoPlay muted playsInline aria-label={vi.preview} />
    {!active && view.phase !== 'error' && <div className="camera-placeholder"><span className="camera-glyph" aria-hidden="true" />
      <p>Khuôn mặt và hai tay<br />trong khung hình</p></div>}
    <span className={`status-badge status-${view.phase}`} role="status"><span aria-hidden="true" />{vi.states[view.phase]}</span>
    {children}
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
  return null;
}

export function CameraRecorder({ recognitionResult = null }: { recognitionResult?: CapturedRecognitionResult | null }) {
  const { view, session, videoRef } = useCameraCapture();
  const panel = useRef<HTMLElement>(null);
  const previousPhase = useRef(view.phase);
  const currentResult = view.phase === 'captured' && recognitionResult?.clip === view.clip ? recognitionResult : null;
  useEffect(() => {
    if (previousPhase.current !== view.phase && !document.querySelector('dialog[open]')) {
      panel.current?.querySelector<HTMLButtonElement>('.capture-controls button')?.focus();
    }
    previousPhase.current = view.phase;
  }, [view.phase]);
  return <section ref={panel} className="camera-workspace" aria-label="Nhận diện ký hiệu bằng camera" aria-describedby="camera-privacy">
    <CameraViewport videoRef={videoRef} view={view}>
      <CaptureFeedback view={view} />
      <div className="camera-dock">
        <RecognitionOverlay result={currentResult} />
        <CameraControls session={session} view={view} enable={() => void session.enable(videoRef.current)} />
      </div>
    </CameraViewport>
    <p id="camera-privacy" className="sr-only">{vi.privacy}</p>
  </section>;
}
