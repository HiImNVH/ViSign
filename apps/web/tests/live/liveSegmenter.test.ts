// T105: bo cat doan tu dong theo nguoi/mat/tay va chuyen dong tay.
import { expect, test } from 'vitest';
import { LiveSegmenter, presenceOf, segmenterConfig as cfg } from '../../src/features/live/liveSegmenter';
import { handMotion } from '../../src/features/live/presenceDetector';

const frame = (motion: number, extra: Partial<{ person: boolean; face: boolean; hands: number }> = {}) =>
  ({ person: true, face: true, hands: 1, motion, ...extra });

test('presence needs a person, a face and at least one hand', () => {
  expect(presenceOf(frame(0, { person: false, face: false, hands: 0 }))).toBe('none');
  expect(presenceOf(frame(0, { face: false }))).toBe('partial');
  expect(presenceOf(frame(0, { hands: 0 }))).toBe('partial');
  expect(presenceOf(frame(0))).toBe('ready');
});

test('starts only when ready and hands move, stops after hands stay still', () => {
  const s = new LiveSegmenter();
  expect(s.step(frame(1, { face: false }), 0).action).toBeNull();
  expect(s.step(frame(cfg.startMotion / 2), 100).action).toBeNull();
  expect(s.step(frame(cfg.startMotion), 200).action).toBe('start');
  expect(s.step(frame(cfg.startMotion), 900).action).toBeNull();
  expect(s.step(frame(0), 900 + cfg.stillMs - 1).action).toBeNull();
  expect(s.step(frame(0), 900 + cfg.stillMs).action).toBe('stop');
  expect(s.isRecording).toBe(false);
});

test('a short movement blip is discarded instead of sent', () => {
  const s = new LiveSegmenter();
  expect(s.step(frame(1), 0).action).toBe('start');
  expect(s.step(frame(0), cfg.stillMs).action).toBe('discard');
});

test('hands leaving the frame end the segment like stillness', () => {
  const s = new LiveSegmenter();
  s.step(frame(1), 0);
  s.step(frame(1), cfg.minMs);
  expect(s.step(frame(0, { hands: 0, face: false }), cfg.minMs + cfg.stillMs).action).toBe('stop');
});

test('continuous motion is cut at the maximum segment length', () => {
  const s = new LiveSegmenter();
  s.step(frame(1), 0);
  expect(s.step(frame(1), cfg.maxMs - 1).action).toBeNull();
  expect(s.step(frame(1), cfg.maxMs).action).toBe('stop');
});

test('reset abandons an open segment', () => {
  const s = new LiveSegmenter();
  s.step(frame(1), 0);
  s.reset();
  expect(s.isRecording).toBe(false);
  expect(s.step(frame(0), 5000).action).toBeNull();
});

test('hand motion treats appearing hands as movement and averages displacement', () => {
  expect(handMotion(null, [])).toBe(0);
  expect(handMotion(null, [{ x: .5, y: .5 }])).toBe(1);
  expect(handMotion([{ x: .5, y: .5 }], [{ x: .5, y: .5 }, { x: .1, y: .1 }])).toBe(1);
  expect(handMotion([{ x: 0, y: 0 }, { x: 0, y: 0 }], [{ x: .03, y: .04 }, { x: 0, y: 0 }])).toBeCloseTo(.025);
});
