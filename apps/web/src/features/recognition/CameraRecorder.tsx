// apps/web/src/features/recognition/CameraRecorder.tsx - Giao dien xem truoc va dieu khien mot doan quay.
import { useLayoutEffect, useRef, type ReactNode, type RefObject } from 'react';
import { vi } from '../../content/vi';
import { type CameraView } from './cameraSession';
import { RecognitionError } from './RecognitionError';
import { RecognitionResult } from './RecognitionResult';
import { TranscriptPanel } from './TranscriptPanel';
import { type useRecognition } from './useRecognition';

// Keep legacy camera-only fixtures valid; the recognition hook supplies these fields in production.
type RecognitionController = Pick<ReturnType<typeof useRecognition>,
  'state' | 'model' | 'camera' | 'enableCamera' | 'startRecording' | 'stopRecording' |
  'submit' | 'cancel' | 'reset' | 'reloadModelInfo'>
  & Partial<Pick<ReturnType<typeof useRecognition>, 'compatibilityError' | 'transcript'>>;

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

function CameraControls({ controller, view, rejectedVisible }: { controller: RecognitionController; view: CameraView; rejectedVisible: boolean }) {
  const { state, model, enableCamera, startRecording, stopRecording, submit, cancel, reset } = controller;
  const pending = state.phase === 'submitting';
  const finished = state.phase === 'result';
  return <div className="capture-controls" role="group" aria-label="Điều khiển camera">
    {(view.phase === 'idle' || view.phase === 'error') && <button className="primary-button" onClick={enableCamera}>{view.phase === 'error' ? 'Thử lại' : 'Bật camera'}</button>}
    {view.phase === 'permission' && <button className="quiet-button" onClick={cancel}>Hủy yêu cầu</button>}
    {(view.phase === 'preview' || (view.phase === 'captured' && !rejectedVisible)) && <button className="primary-button" onClick={startRecording}><span className="record-dot" aria-hidden="true" />{view.phase === 'captured' ? 'Quay lại' : 'Quay ký hiệu'}</button>}
    {view.phase === 'captured' && !finished && <button className="primary-button submit-button" onClick={() => void submit()}
      disabled={model.status !== 'ready' || pending} aria-label={vi.recognition.send}>
      {pending ? vi.recognition.sending : <><span className="long-label">{vi.recognition.send}</span><span className="compact-label" aria-hidden="true">Gửi</span></>}
    </button>}
    {view.phase === 'recording' && <button className="primary-button stop-button" onClick={stopRecording}><span className="stop-mark" aria-hidden="true" />Kết thúc</button>}
    {view.phase === 'stopping' && <span className="finishing-label">Đang hoàn tất…</span>}
    {(view.phase === 'recording' || view.phase === 'stopping' || view.phase === 'captured') && <button className="quiet-button" onClick={cancel}><span className="long-label">Hủy đoạn quay</span><span className="compact-label" aria-hidden="true">Hủy</span></button>}
    {['preview', 'recording', 'stopping', 'captured'].includes(view.phase) && <button className="quiet-button camera-off" onClick={reset}><span className="long-label">Tắt camera</span><span className="compact-label" aria-hidden="true">Tắt</span></button>}
  </div>;
}

export function CameraRecorder({ controller }: { controller: RecognitionController }) {
  const { view, videoRef } = controller.camera;
  const { state, model, reloadModelInfo, startRecording, compatibilityError, transcript = [] } = controller;
  const panel = useRef<HTMLElement>(null);
  const previousPhase = useRef(view.phase);
  const previousRecognitionPhase = useRef(state.phase);
  const currentResult = view.phase === 'captured' && state.phase === 'result' && model.status === 'ready'
    ? state.result : null;
  const rejectedVisible = currentResult !== null && !currentResult.accepted && model.status === 'ready'
    && currentResult.modelVersion === model.info.modelVersion;
  useLayoutEffect(() => {
    const focused = document.activeElement;
    if ((previousPhase.current !== view.phase || previousRecognitionPhase.current !== state.phase)
      && !document.querySelector('dialog[open]')
      && (!focused || focused === document.body || !focused.isConnected)) {
      panel.current?.querySelector<HTMLButtonElement>('.translation-retry, .capture-controls button:not([disabled])')?.focus();
    }
    previousPhase.current = view.phase;
    previousRecognitionPhase.current = state.phase;
  }, [view.phase, state.phase]);
  return <section ref={panel} className="camera-workspace" aria-label="Nhận diện ký hiệu bằng camera" aria-describedby="camera-privacy">
    <CameraViewport videoRef={videoRef} view={view}>
      <TranscriptPanel entries={transcript} />
      {view.phase === 'error' && <RecognitionError type="camera" error={view.error} />}
      <div className="camera-dock">
        {compatibilityError && <div className="recognition-feedback"><RecognitionError type="api" stage="prediction" error={compatibilityError} /></div>}
        <RecognitionResult result={currentResult} model={model.status === 'ready' ? model.info : null} onRetry={startRecording} />
        {view.phase === 'captured' && <div className="recognition-feedback">
          {model.status === 'loading' && <p role="status">{vi.recognition.modelLoading}</p>}
          {model.status === 'unavailable' && <><RecognitionError type="api" stage="model" error={model.error} />
            <button className="quiet-button model-retry" onClick={reloadModelInfo}>{vi.recognition.reloadModel}</button></>}
          {model.status === 'ready' && state.phase === 'error' && 'source' in state && state.source === 'api'
            && <RecognitionError type="api" stage="prediction" error={state.error} />}
        </div>}
        <CameraControls controller={controller} view={view} rejectedVisible={rejectedVisible} />
      </div>
    </CameraViewport>
    <p id="camera-privacy" className="sr-only">{vi.privacy}</p>
  </section>;
}
