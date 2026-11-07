import { vi } from '../../content/vi';
import type { TranslationHistoryEntry } from './translationHistory';

// Render a short viewport and announce only the new item, not the whole session.
export const TRANSCRIPT_WINDOW_SIZE = 30;

export function TranscriptPanel({ entries }: { entries: TranslationHistoryEntry[] }) {
  if (!entries.length) return null;
  const visible = entries.slice(-TRANSCRIPT_WINDOW_SIZE);
  return <section className="transcript-panel" aria-label={vi.transcript.title}>
    <span className="transcript-label">{vi.transcript.title}</span>
    <p className="transcript-text">{visible.map(entry => entry.text).join(' ')}</p>
    <span className="sr-only" aria-live="polite" aria-atomic="true">{entries.at(-1)?.text}</span>
    <span className="sr-only">{vi.transcript.description}</span>
  </section>;
}
