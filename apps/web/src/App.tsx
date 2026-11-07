// apps/web/src/App.tsx - Bo cuc trang camera va thong tin thu nghiem.
import { CameraHelp } from './components/CameraHelp';
import { vi } from './content/vi';
import { CameraRecorder } from './features/recognition/CameraRecorder';
import { HistoryPanel } from './features/recognition/HistoryPanel';
import { useRecognition } from './features/recognition/useRecognition';
import './styles.css';

export function App() {
  const recognition = useRecognition();
  return (
    <main className="app-shell">
      <header className="app-header"><div className="brand"><h1>ViSign</h1><span>{vi.title}</span></div>
        <div className="header-actions"><span className="trial-label">Bản thử nghiệm</span>
          <HistoryPanel history={recognition.history} refreshHistory={recognition.refreshHistory}
            clearHistory={recognition.clearHistory} /><CameraHelp /></div></header>
      <CameraRecorder controller={recognition} />
    </main>
  );
}
