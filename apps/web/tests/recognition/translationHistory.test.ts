import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { HISTORY_STORAGE_KEY, HISTORY_TTL_MS, appendTranslationHistory,
  clearTranslationHistory, readTranslationHistory } from '../../src/features/recognition/translationHistory';

const now = new Date('2026-11-07T12:00:00.000Z');
const first = { requestId: '123e4567-e89b-42d3-a456-426614174000', text: 'Xin chào',
  confidence: .92, modelVersion: 'v1', createdAt: now.toISOString() };
const second = { ...first, requestId: '123e4567-e89b-42d3-a456-426614174001', text: 'Cảm ơn' };

beforeEach(() => { localStorage.clear(); vi.useFakeTimers(); vi.setSystemTime(now); });
afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); localStorage.clear(); });

describe('browser-only accepted translation history', () => {
  it('stores exactly five metadata fields in versioned JSON and deduplicates request IDs', () => {
    expect(appendTranslationHistory({ ...first, video: 'secret', landmarks: [1] } as typeof first)).toMatchObject({ available: true });
    expect(appendTranslationHistory(first).entries).toHaveLength(1);
    expect(appendTranslationHistory(second).entries.map(x => x.text)).toEqual(['Xin chào', 'Cảm ơn']);
    expect(JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY)!)).toEqual({ schemaVersion: 1, entries: [first, second] });
    expect(localStorage.getItem(HISTORY_STORAGE_KEY)).not.toMatch(/video|landmark|classLabel|frame/);
  });

  it('keeps entries before 24 hours, expires them at the exact boundary during read and write', () => {
    appendTranslationHistory(first);
    vi.setSystemTime(new Date(now.getTime() + HISTORY_TTL_MS - 1));
    expect(readTranslationHistory().entries).toHaveLength(1);
    vi.setSystemTime(new Date(now.getTime() + HISTORY_TTL_MS));
    expect(readTranslationHistory().entries).toEqual([]);
    expect(localStorage.getItem(HISTORY_STORAGE_KEY)).toBeNull();
    const next = { ...second, createdAt: new Date().toISOString() };
    expect(appendTranslationHistory(next).entries).toEqual([next]);
  });

  it('drops invalid schema, corrupt JSON, malformed entries, future timestamp and duplicates', () => {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify({ schemaVersion: 2, entries: [first] }));
    expect(readTranslationHistory().entries).toEqual([]);
    localStorage.setItem(HISTORY_STORAGE_KEY, '{bad json');
    expect(readTranslationHistory().entries).toEqual([]);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify({ schemaVersion: 1, entries: [
      { ...first, confidence: 2 }, first, first,
      { ...second, createdAt: new Date(now.getTime() + 500).toISOString() },
      { ...second, classLabel: 'private' },
    ] }));
    expect(readTranslationHistory().entries).toEqual([first]);
  });

  it('continues when localStorage reads or writes throw and can clear after recovery', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementationOnce(() => { throw new Error('blocked'); });
    expect(readTranslationHistory()).toEqual({ entries: [], available: false });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementationOnce(() => { throw new Error('quota exceeded'); });
    expect(appendTranslationHistory(first).available).toBe(false);
    expect(readTranslationHistory().entries).toEqual([]);
    expect(appendTranslationHistory(first).entries).toHaveLength(1);
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementationOnce(() => { throw new Error('denied'); });
    expect(clearTranslationHistory()).toBe(false);
    expect(readTranslationHistory().entries).toHaveLength(1);
    expect(clearTranslationHistory()).toBe(true);
    expect(readTranslationHistory().entries).toEqual([]);
  });
});
