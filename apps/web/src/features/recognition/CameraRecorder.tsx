// apps/web/src/features/recognition/CameraRecorder.tsx - Giao dien xem truoc va dieu khien mot doan quay.
import { useLayoutEffect, useRef, type ReactNode, type RefObject } from 'react';
import { vi } from '../../content/vi';
import { type CameraView } from './cameraSession';
import { RecognitionError } from './RecognitionError';
import { RecognitionResult } from './RecognitionResult';
import { TranscriptPanel } from './TranscriptPanel';
import type { CameraController } from './recognitionController';

type FocusRefs = {
  primary: RefObject<HTMLButtonElement | null>;
  submit: RefObject<HTMLButtonElement | null>;
  cancel: RefObject<HTMLButtonElement | null>;
  reset: RefObject<HTMLButtonElement | null>;
};

function CameraViewport({ videoRef, view, status, children }: { videoRef: RefObject<HTMLVideoElement | null>; view: CameraView; status?: string | undefined; children: ReactNode }) {
  const active = ['preview', 'recording', 'stopping', 'captured'].includes(view.phase);
  return <div className={`camera-viewport ${active ? 'camera-active' : ''}`} data-phase={view.phase}>
    <video ref={videoRef} autoPlay muted playsInline aria-label={vi.preview} />
    {!active && view.phase !== 'error' && <div className="camera-placeholder"><span className="camera-glyph" aria-hidden="true" />
      <p>Khuôn mặt và hai tay<br />trong khung hình</p></div>}
    <span className={`status-badge status-${view.phase}`} role="status" aria-atomic="true"><span aria-hidden="true" />{status ?? vi.states[view.phase]}</span>
    {children}
  </div>;
}

function CameraControls({ controller, view, rejectedVisible, focusRefs }: { controller: CameraController; view: CameraView; rejectedVisible: boolean; focusRefs: FocusRefs }) {
  const { state, model, enableCamera, startRecording, stopRecording, submit, cancel, reset } = controller;
  const pending = state.phase === 'submitting';
  const finished = state.phase === 'result';
  return <div className="capture-controls" role="group" aria-label="Điều khiển camera">
    {(view.phase === 'idle' || view.phase === 'error') && <button ref={focusRefs.primary} className="primary-button" onClick={enableCamera}>{view.phase === 'error' ? 'Thử lại' : 'Bật camera'}</button>}
    {view.phase === 'permission' && <button ref={focusRefs.primary} className="quiet-button" onClick={cancel}>Hủy yêu cầu</button>}
    {(view.phase === 'preview' || (view.phase === 'captured' && !rejectedVisible)) && <button ref={focusRefs.primary} className="primary-button" onClick={startRecording}><span className="record-dot" aria-hidden="true" />{view.phase === 'captured' ? 'Quay lại' : 'Quay ký hiệu'}</button>}
    {view.phase === 'captured' && !finished && <button ref={focusRefs.submit} className="primary-button submit-button" onClick={() => void submit()}
      disabled={model.status !== 'ready' || pending} aria-label={pending ? vi.recognition.sending : vi.recognition.send}>
      {pending ? vi.recognition.sending : <><span className="long-label">{vi.recognition.send}</span><span className="compact-label" aria-hidden="true">Gửi</span></>}
    </button>}
    {view.phase === 'recording' && <button ref={focusRefs.primary} className="primary-button stop-button" onClick={stopRecording}><span className="stop-mark" aria-hidden="true" />Kết thúc</button>}
    {view.phase === 'stopping' && <span className="finishing-label">Đang hoàn tất…</span>}
    {(view.phase === 'recording' || view.phase === 'stopping' || view.phase === 'captured') && <button ref={focusRefs.cancel} className="quiet-button" onClick={cancel}><span className="long-label">Hủy đoạn quay</span><span className="compact-label" aria-hidden="true">Hủy</span></button>}
    {['preview', 'recording', 'stopping', 'captured'].includes(view.phase) && <button ref={focusRefs.reset} className="quiet-button camera-off" onClick={reset}><span className="long-label">Tắt camera</span><span className="compact-label" aria-hidden="true">Tắt</span></button>}
  </div>;
}

export function CameraRecorder({ controller }: { controller: CameraController }) {
  const { view, videoRef } = controller.camera;
  const { state, model, reloadModelInfo, startRecording, compatibilityError, transcript } = controller;
  const retry = useRef<HTMLButtonElement>(null);
  const primary = useRef<HTMLButtonElement>(null);
  const submit = useRef<HTMLButtonElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const reset = useRef<HTMLButtonElement>(null);
  const focusRefs = { primary, submit, cancel, reset };
  const focusAvailable = () => {
    for (const ref of [retry, primary, submit, cancel, reset]) {
      const button = ref.current;
      if (button?.isConnected && !button.disabled) { button.focus(); return; }
    }
  };
  const previousPhase = useRef(view.phase);
  const previousRecognitionPhase = useRef(state.phase);
  const currentResult = view.phase === 'captured' && state.phase === 'result' && model.status === 'ready'
    ? state.result : null;
  const rejectedVisible = currentResult !== null && !currentResult.accepted && model.status === 'ready'
    && currentResult.modelVersion === model.info.modelVersion;
  useLayoutEffect(() => {
    const focused = document.activeElement;
    if ((previousPhase.current !== view.phase || previousRecognitionPhase.current !== state.phase)
      && !(document.activeElement instanceof HTMLElement && document.activeElement.closest('dialog[open]'))
      && (!focused || focused === document.body || !focused.isConnected
        || (focused instanceof HTMLButtonElement && focused.disabled))) {
      focusAvailable();
    }
    previousPhase.current = view.phase;
    previousRecognitionPhase.current = state.phase;
  }, [view.phase, state.phase]);
  return <section className="camera-workspace" aria-label="Nhận diện ký hiệu bằng camera" aria-describedby="camera-privacy">
    <CameraViewport videoRef={videoRef} view={view} status={state.phase === 'submitting' ? vi.recognition.sending : undefined}>
      <TranscriptPanel entries={transcript} />
      {view.phase === 'error' && <RecognitionError type="camera" error={view.error} />}
      <div className="camera-dock">
        {compatibilityError && <div className="recognition-feedback"><RecognitionError type="api" stage="prediction" error={compatibilityError} /></div>}
        <RecognitionResult result={currentResult} model={model.status === 'ready' ? model.info : null} onRetry={startRecording} retryRef={retry} />
        {view.phase === 'captured' && <div className="recognition-feedback">
          {model.status === 'loading' && <p role="status">{vi.recognition.modelLoading}</p>}
          {model.status === 'unavailable' && <><RecognitionError type="api" stage="model" error={model.error} />
            <button className="quiet-button model-retry" onClick={() => {
              // The retry button unmounts while metadata reloads; move focus to a stable control first.
              focusAvailable();
              reloadModelInfo();
            }}>{vi.recognition.reloadModel}</button></>}
          {model.status === 'ready' && state.phase === 'error' && 'source' in state && state.source === 'api'
            && <RecognitionError type="api" stage="prediction" error={state.error} />}
        </div>}
        <CameraControls controller={controller} view={view} rejectedVisible={rejectedVisible} focusRefs={focusRefs} />
      </div>
    </CameraViewport>
    <p id="camera-privacy" className="sr-only">{vi.privacy}</p>
  </section>;
}
