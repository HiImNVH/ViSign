import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { vi } from '../../content/vi';
import type { HistoryController } from './recognitionController';

type Props = HistoryController & { variant?: 'dialog' | 'sidebar' };
const HISTORY_PAGE_SIZE = 50;

export function HistoryPanel({ history, refreshHistory, clearHistory, removeHistoryEntry, variant = 'dialog' }: Props) {
  const sidebar = variant === 'sidebar';
  const titleId = useId();
  const heading = useRef<HTMLHeadingElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const clearButton = useRef<HTMLButtonElement>(null);
  const confirmButton = useRef<HTMLButtonElement>(null);
  const focusAfterChange = useRef<'confirm' | 'clear' | 'close' | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [clearError, setClearError] = useState(false);
  const [visibleCount, setVisibleCount] = useState(HISTORY_PAGE_SIZE);
  const [selectedEntry, setSelectedEntry] = useState<string | null>(null);
  const visibleEntries = history.entries.slice(0, visibleCount);
  const newestEntryId = history.entries[0]?.requestId ?? null;
  const activeEntryId = selectedEntry ?? newestEntryId;
  const previousNewestEntryId = useRef(newestEntryId);
  useEffect(() => {
    if (previousNewestEntryId.current !== newestEntryId) {
      previousNewestEntryId.current = newestEntryId;
      setSelectedEntry(null);
    }
  }, [newestEntryId]);
  useLayoutEffect(() => {
    if (!sidebar && !dialog.current?.open) return;
    const next = focusAfterChange.current;
    if (!next) return;
    if (sidebar && !heading.current?.getClientRects().length) { focusAfterChange.current = null; return; }
    if (next === 'close' && sidebar) heading.current?.focus();
    else (next === 'confirm' ? confirmButton : next === 'clear' ? clearButton : closeButton).current?.focus();
    focusAfterChange.current = null;
  }, [confirming, history.entries.length, sidebar]);
  const open = () => { focusAfterChange.current = null; setVisibleCount(HISTORY_PAGE_SIZE); refreshHistory(); setConfirming(false); setClearError(false); dialog.current?.showModal(); };
  const clear = () => {
    if (clearHistory()) { focusAfterChange.current = 'close'; setConfirming(false); setClearError(false); }
    else setClearError(true);
  };
  const content = <>
      <div className="dialog-heading">
        <div className="history-title-group">
          <svg className="history-heading-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2M4 4l2 2"/></svg>
          <h2 ref={heading} tabIndex={sidebar ? -1 : undefined} id={titleId}>{vi.history.title}</h2>
          {sidebar && <span className="history-count" aria-label={`${history.entries.length} bản dịch`}>{history.entries.length}</span>}
        </div>
        {sidebar ? <button type="button" className="quiet-button history-delete-selected"
          aria-label="Xóa bản dịch đang chọn" title="Xóa bản dịch đang chọn" disabled={!activeEntryId}
          onClick={() => {
            if (activeEntryId && removeHistoryEntry(activeEntryId)) setSelectedEntry(null);
            else if (activeEntryId) setClearError(true);
          }}>
          <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false" style={{ display: 'block', flex: 'none', overflow: 'visible' }}>
            <path d="M4 7h16M10 11v6m4-6v6M6 7l1 13h10l1-13M9 7V4h6v3" fill="none" stroke="#147655" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button> : <button ref={closeButton} className="quiet-button" onClick={() => dialog.current?.close()} aria-label={vi.history.close}>Đóng</button>}</div>
      {!history.available && <p role="alert" className="history-warning">{vi.history.unavailable}</p>}
      <div className="history-content">
        {history.entries.length ? <>
          {visibleCount < history.entries.length && <button className="quiet-button history-load-more"
            onClick={() => setVisibleCount(count => count + HISTORY_PAGE_SIZE)}>
            {vi.history.showOlder}
          </button>}
          <ol className="history-entries">
            {visibleEntries.map((entry, index) => {
              const highlighted = activeEntryId ? activeEntryId === entry.requestId : index === 0;
              return <li key={entry.requestId} className={highlighted ? 'history-entry-highlighted' : undefined}>
                <button type="button" className="history-entry-button" aria-pressed={highlighted}
                  onClick={() => setSelectedEntry(entry.requestId)}>
                  <strong>{entry.text}</strong>
                  <time dateTime={entry.createdAt}>{new Intl.DateTimeFormat('vi-VN', {
                    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
                  }).format(new Date(entry.createdAt))}</time>
                </button>
              </li>;
            })}
          </ol>
        </> : <p className="history-empty">{vi.history.empty}</p>}
      </div>
      {clearError && <p role="alert" className="history-warning">{vi.history.clearFailed}</p>}
      {(history.entries.length > 0 || !history.available) && <div className="history-actions">
        {confirming ? <>
          <p>{vi.history.confirm}</p>
          <button ref={confirmButton} className="primary-button" onClick={clear}>{vi.history.confirmYes}</button>
          <button className="quiet-button" onClick={() => { focusAfterChange.current = 'clear'; setConfirming(false); setClearError(false); }}>{vi.history.cancel}</button>
        </> : <button ref={clearButton} className="quiet-button" onClick={() => { focusAfterChange.current = 'confirm'; setConfirming(true); }}>
          <svg className="history-trash-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6m4-6v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>
          {vi.history.clear}
        </button>}
      </div>}
  </>;
  if (sidebar) return <aside className="history-sidebar" aria-labelledby={titleId}>{content}</aside>;
  return <>
    <button ref={trigger} className="quiet-button history-trigger" onClick={open}>{vi.history.open}</button>
    <dialog ref={dialog} className="app-dialog history-dialog" aria-labelledby={titleId}
      onClose={() => { focusAfterChange.current = null; setConfirming(false); trigger.current?.focus(); }}>
      {content}
    </dialog>
  </>;
}
