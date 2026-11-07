// T101: browser-only metadata for accepted translations; never store captures or landmarks.
export const HISTORY_STORAGE_KEY = 'visign.translation-history.v1';
export const HISTORY_TTL_MS = 24 * 60 * 60 * 1000;

export type TranslationHistoryEntry = {
  requestId: string;
  text: string;
  confidence: number;
  modelVersion: string;
  createdAt: string;
};

export type HistoryRead = { entries: TranslationHistoryEntry[]; available: boolean };

const isObject = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const isUuid = (value: unknown): value is string => typeof value === 'string'
  && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value);

function validEntry(value: unknown, now: number): value is TranslationHistoryEntry {
  if (!isObject(value) || Object.keys(value).sort().join(',') !== 'confidence,createdAt,modelVersion,requestId,text') return false;
  if (!isUuid(value.requestId) || typeof value.text !== 'string' || !value.text.trim()
    || typeof value.modelVersion !== 'string' || !value.modelVersion.trim()
    || typeof value.confidence !== 'number' || !Number.isFinite(value.confidence)
    || value.confidence < 0 || value.confidence > 1 || typeof value.createdAt !== 'string') return false;
  const timestamp = Date.parse(value.createdAt);
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value.createdAt)
    && Number.isFinite(timestamp) && new Date(timestamp).toISOString() === value.createdAt
    && timestamp <= now && now - timestamp < HISTORY_TTL_MS;
}

function project(entry: TranslationHistoryEntry): TranslationHistoryEntry {
  return { requestId: entry.requestId, text: entry.text, confidence: entry.confidence,
    modelVersion: entry.modelVersion, createdAt: entry.createdAt };
}

function load(now: number): HistoryRead {
  try {
    const storage = window.localStorage;
    const raw = storage.getItem(HISTORY_STORAGE_KEY);
    if (raw === null) return { entries: [], available: true };
    let parsed: unknown;
    try { parsed = JSON.parse(raw); } catch { parsed = null; }
    if (!isObject(parsed) || parsed.schemaVersion !== 1 || !Array.isArray(parsed.entries)) {
      storage.removeItem(HISTORY_STORAGE_KEY);
      return { entries: [], available: true };
    }
    const seen = new Set<string>();
    const entries: TranslationHistoryEntry[] = [];
    for (const item of parsed.entries) {
      if (validEntry(item, now) && !seen.has(item.requestId)) {
        seen.add(item.requestId);
        entries.push(project(item));
      }
    }
    entries.sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt));
    if (entries.length !== parsed.entries.length || JSON.stringify(entries) !== JSON.stringify(parsed.entries)) {
      if (entries.length) storage.setItem(HISTORY_STORAGE_KEY, JSON.stringify({ schemaVersion: 1, entries }));
      else storage.removeItem(HISTORY_STORAGE_KEY);
    }
    return { entries, available: true };
  } catch {
    return { entries: [], available: false };
  }
}

export function readTranslationHistory(now = Date.now()): HistoryRead { return load(now); }

export function appendTranslationHistory(entry: TranslationHistoryEntry, now = Date.now()): HistoryRead {
  const previous = load(now);
  if (!previous.available) return previous;
  if (!validEntry(entry, now)) return previous;
  if (previous.entries.some(item => item.requestId === entry.requestId)) return previous;
  const entries = [...previous.entries, project(entry)]
    .sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt));
  try {
    window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify({ schemaVersion: 1, entries }));
    return { entries, available: true };
  } catch {
    return { entries: previous.entries, available: false };
  }
}

export function clearTranslationHistory(): boolean {
  try { window.localStorage.removeItem(HISTORY_STORAGE_KEY); return true; }
  catch { return false; }
}
