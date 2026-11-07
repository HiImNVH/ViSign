import { useRef, useState } from 'react';
import { vi } from '../../content/vi';
import type { useRecognition } from './useRecognition';

type Props = Pick<ReturnType<typeof useRecognition>, 'history' | 'refreshHistory' | 'clearHistory'>;

export function HistoryPanel({ history, refreshHistory, clearHistory }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [confirming, setConfirming] = useState(false);
  const [clearError, setClearError] = useState(false);
  const open = () => { refreshHistory(); setConfirming(false); setClearError(false); dialog.current?.showModal(); };
  const clear = () => {
    if (clearHistory()) { setConfirming(false); setClearError(false); }
    else setClearError(true);
  };
  return <>
    <button ref={trigger} className="quiet-button history-trigger" onClick={open}>{vi.history.open}</button>
    <dialog ref={dialog} className="help-dialog history-dialog" aria-labelledby="history-title"
      onClose={() => { setConfirming(false); trigger.current?.focus(); }}>
      <div className="dialog-heading"><h2 id="history-title">{vi.history.title}</h2>
        <button className="quiet-button" onClick={() => dialog.current?.close()} aria-label={vi.history.close}>Đóng</button></div>
      <p className="history-disclosure">{vi.history.disclosure}</p>
      <p className="history-disclosure">{vi.transcript.description}</p>
      {!history.available && <p role="alert" className="history-warning">{vi.history.unavailable}</p>}
      {history.entries.length ? <ol className="history-entries">
        {history.entries.map(entry => <li key={entry.requestId}>
          <strong>{entry.text}</strong>
          <span>{new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(entry.createdAt))}</span>
          <span>{vi.history.confidence}: {(entry.confidence * 100).toFixed(0)}% · {vi.history.model}: {entry.modelVersion}</span>
        </li>)}
      </ol> : <p className="history-empty">{vi.history.empty}</p>}
      {clearError && <p role="alert" className="history-warning">{vi.history.clearFailed}</p>}
      {history.entries.length > 0 && <div className="history-actions">
        {confirming ? <>
          <p>{vi.history.confirm}</p>
          <button className="primary-button" onClick={clear}>{vi.history.confirmYes}</button>
          <button className="quiet-button" onClick={() => { setConfirming(false); setClearError(false); }}>{vi.history.cancel}</button>
        </> : <button className="quiet-button" onClick={() => setConfirming(true)}>{vi.history.clear}</button>}
      </div>}
    </dialog>
  </>;
}
