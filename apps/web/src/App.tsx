// apps/web/src/App.tsx - Bo cuc trang camera va thong tin thu nghiem.
import { useEffect } from 'react';
import { CameraHelp } from './components/CameraHelp';
import { CameraGuidance, LiveCamera } from './features/live/LiveCamera';
import { useLiveRecognition } from './features/live/useLiveRecognition';
import { HistoryPanel } from './features/recognition/HistoryPanel';
import './styles.css';
import './graphics.css';

export function App() {
  const recognition = useLiveRecognition();
  const { liveStatus, paused, start, resume, pause, stop } = recognition;
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== ' ' && event.key !== 'Escape') return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable
        || ['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'SUMMARY'].includes(target.tagName))) return;
      if (document.querySelector('dialog[open]')) return;
      if (event.key === ' ') {
        event.preventDefault();
        if (liveStatus === 'off' || liveStatus === 'error') void start();
        else if (paused) resume();
        else if (liveStatus !== 'starting') pause();
      } else if (liveStatus !== 'off') {
        event.preventDefault();
        stop();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [liveStatus, paused, start, resume, pause, stop]);
  return (
    <main className="app-shell">
      <header className="app-header"><div className="brand"><h1>V<span className="brand-i">i</span>S<span className="brand-i">i</span>gn</h1></div>
        <CameraGuidance live={recognition} />
        <div className="header-actions"><CameraHelp /></div></header>
      <div className="recognition-layout">
        <LiveCamera live={recognition} />
        <HistoryPanel variant="sidebar" history={recognition.history} refreshHistory={recognition.refreshHistory}
          clearHistory={recognition.clearHistory} removeHistoryEntry={recognition.removeHistoryEntry} />
      </div>
      <footer className="app-footer">© 2026 ViSign · 5HVT | Hackathon · Bản thử nghiệm</footer>
    </main>
  );
}
