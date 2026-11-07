import { useLayoutEffect, useRef, useState } from 'react';
import { vi } from '../../content/vi';
import type { useRecognition } from './useRecognition';

type Props = Pick<ReturnType<typeof useRecognition>, 'history' | 'refreshHistory' | 'clearHistory'>;

export function HistoryPanel({ history, refreshHistory, clearHistory }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const clearButton = useRef<HTMLButtonElement>(null);
  const confirmButton = useRef<HTMLButtonElement>(null);
  const focusAfterChange = useRef<'confirm' | 'clear' | 'close' | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [clearError, setClearError] = useState(false);
  useLayoutEffect(() => {
    if (!dialog.current?.open) return;
    const next = focusAfterChange.current;
    if (!next) return;
    (next === 'confirm' ? confirmButton : next === 'clear' ? clearButton : closeButton).current?.focus();
    focusAfterChange.current = null;
  }, [confirming, history.entries.length]);
  const open = () => { focusAfterChange.current = null; refreshHistory(); setConfirming(false); setClearError(false); dialog.current?.showModal(); };
  const clear = () => {
    if (clearHistory()) { focusAfterChange.current = 'close'; setConfirming(false); setClearError(false); }
    else setClearError(true);
  };
  return <>
    <button ref={trigger} className="quiet-button history-trigger" onClick={open}>{vi.history.open}</button>
    <dialog ref={dialog} className="help-dialog history-dialog" aria-labelledby="history-title"
      onClose={() => { focusAfterChange.current = null; setConfirming(false); trigger.current?.focus(); }}>
      <div className="dialog-heading"><h2 id="history-title">{vi.history.title}</h2>
        <button ref={closeButton} className="quiet-button" onClick={() => dialog.current?.close()} aria-label={vi.history.close}>Đóng</button></div>
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
      {(history.entries.length > 0 || !history.available) && <div className="history-actions">
        {confirming ? <>
          <p>{vi.history.confirm}</p>
          <button ref={confirmButton} className="primary-button" onClick={clear}>{vi.history.confirmYes}</button>
          <button className="quiet-button" onClick={() => { focusAfterChange.current = 'clear'; setConfirming(false); setClearError(false); }}>{vi.history.cancel}</button>
        </> : <button ref={clearButton} className="quiet-button" onClick={() => { focusAfterChange.current = 'confirm'; setConfirming(true); }}>{vi.history.clear}</button>}
      </div>}
    </dialog>
  </>;
}
