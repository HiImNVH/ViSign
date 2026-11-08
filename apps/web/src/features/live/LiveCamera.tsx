// apps/web/src/features/live/LiveCamera.tsx - Giao dien dich truc tiep (T106): xem truoc, trang thai, ban dich.
import { useLayoutEffect, useRef } from 'react';
import { vi } from '../../content/vi';
import { RecognitionError } from '../recognition/RecognitionError';
import { RecognitionResult } from '../recognition/RecognitionResult';
import { TranscriptPanel } from '../recognition/TranscriptPanel';
import type { LiveRecognition, LiveStatus } from './useLiveRecognition';

const ACTIVE: LiveStatus[] = ['noPerson', 'partial', 'ready', 'recording', 'translating', 'translated', 'rejected', 'paused'];

function PresenceChips({ live }: { live: LiveRecognition }) {
  const { person, face, hands } = live.presence;
  const items: [string, boolean][] = [
    [vi.live.parts.person, person], [vi.live.parts.face, face], [vi.live.parts.hands, hands > 0],
  ];
  return <ul className="presence-chips" aria-label={vi.live.parts.label}>
    {items.map(([label, ok]) => <li key={label} className={ok ? 'chip-on' : 'chip-off'}>
      <span aria-hidden="true">{ok ? '✓' : '·'}</span> {label}<span className="sr-only">{ok ? ': có' : ': chưa có'}</span>
    </li>)}
  </ul>;
}

export function LiveCamera({ live }: { live: LiveRecognition }) {
  const { camera, liveStatus, state, model, compatibilityError, transcript, paused } = live;
  const view = camera.view;
  const active = ACTIVE.includes(liveStatus);
  const primary = useRef<HTMLButtonElement>(null);
  const previous = useRef(liveStatus);
  const result = model.status === 'ready' ? live.lastResult : null;

  // Giu focus ban phim khi nut dang focus bien mat do doi trang thai
  useLayoutEffect(() => {
    const focused = document.activeElement;
    if (previous.current !== liveStatus && (!focused || focused === document.body || !focused.isConnected)) {
      primary.current?.focus();
    }
    previous.current = liveStatus;
  }, [liveStatus]);

  return <section className="camera-workspace" aria-label="Dịch ký hiệu trực tiếp bằng camera" aria-describedby="camera-privacy">
    <div className={`camera-viewport ${view.phase !== 'idle' && view.phase !== 'error' ? 'camera-active' : ''}`}
      data-live-status={liveStatus}>
      <video ref={camera.videoRef} autoPlay muted playsInline aria-label={vi.preview} />
      {!active && liveStatus !== 'error' && <div className="camera-placeholder"><div className="camera-guide" aria-hidden="true">
        <svg className="camera-illustration" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 18l4-6h12l4 6h8a6 6 0 0 1 6 6v24a6 6 0 0 1-6 6H14a6 6 0 0 1-6-6V24a6 6 0 0 1 6-6z" />
          <circle cx="32" cy="35" r="11" /><path d="M46 26h2" />
        </svg></div>
        <p>Khuôn mặt và hai tay<br />trong khung hình</p></div>}
      <span className={`status-badge live-${liveStatus}`} role="status" aria-atomic="true">
        <span aria-hidden="true" />{vi.live.status[liveStatus]}
      </span>
      <div className="camera-guidance">
        {active && <PresenceChips live={live} />}
        {liveStatus !== 'off' && <p className="live-hint">{vi.live.hint[liveStatus]}</p>}
      </div>
      <div className="sr-only"><TranscriptPanel entries={transcript} /></div>
      <div className="camera-dock">
        {view.phase === 'error' && <RecognitionError type="camera" error={view.error} />}
        {live.detectorError && view.phase !== 'error' && <div className="capture-feedback error-feedback" role="alert">
          <h3>{vi.live.detectorFailed[0]}</h3><p>{vi.live.detectorFailed[1]}</p></div>}
        {compatibilityError && <RecognitionError type="api" stage="prediction" error={compatibilityError} />}
        {model.status === 'unavailable' && active && <div className="recognition-feedback">
          <RecognitionError type="api" stage="model" error={model.error} />
          <button className="quiet-button model-retry" onClick={live.reloadModelInfo}>{vi.recognition.reloadModel}</button>
        </div>}
        {state.phase === 'error' && 'source' in state && <RecognitionError type="api" stage="prediction" error={state.error} />}
        <RecognitionResult result={result} model={model.status === 'ready' ? model.info : null} />
        <div className="capture-controls" role="group" aria-label="Điều khiển dịch trực tiếp">
          {(liveStatus === 'off' || liveStatus === 'error') && <button ref={primary} className="primary-button"
            onClick={() => { if (liveStatus === 'error') live.stop(); void live.start(); }}>
            {liveStatus === 'error' ? vi.live.retry : vi.live.start}</button>}
          {active && (paused
            ? <button ref={primary} type="button" className="quiet-button icon-button" aria-label={vi.live.resume}
              title={vi.live.resume} onClick={live.resume}>
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="M8 5.5v13l10-6.5z" fill="currentColor" />
              </svg>
            </button>
            : <button ref={primary} type="button" className="quiet-button icon-button" aria-label={vi.live.pause}
              title={vi.live.pause} onClick={live.pause}>
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="M8 5v14M16 5v14" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
              </svg>
            </button>)}
          {(active || liveStatus === 'starting') && <button type="button" className="quiet-button icon-button camera-off-button"
            aria-label={vi.live.stop} title={vi.live.stop} onClick={live.stop}>
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <rect x="3.5" y="7.5" width="11" height="9" rx="2" fill="none" stroke="currentColor" strokeWidth="1.9" />
              <path d="m14.5 10 5-3v10l-5-3M3 3l18 18" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>}
        </div>
      </div>
    </div>
    <p id="camera-privacy" className="sr-only">{vi.privacy}</p>
  </section>;
}
