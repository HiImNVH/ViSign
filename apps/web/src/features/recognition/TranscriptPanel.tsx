import { vi } from '../../content/vi';
import type { TranslationHistoryEntry } from './translationHistory';

export function TranscriptPanel({ entries }: { entries: TranslationHistoryEntry[] }) {
  if (!entries.length) return null;
  return <section className="transcript-panel" aria-label={vi.transcript.title}>
    <span className="transcript-label">{vi.transcript.title}</span>
    <p className="transcript-text" aria-live="polite" aria-atomic="true">{entries.map(entry => entry.text).join(' ')}</p>
    <span className="sr-only">{vi.transcript.description}</span>
  </section>;
}
