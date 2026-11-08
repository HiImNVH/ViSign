// apps/web/src/features/live/useLiveRecognition.ts - Dich truc tiep (T105-T106).
// Bat camera la luon theo doi: khi thay nguoi, mat va tay roi tay bat dau chuyen dong thi tu ghi mot doan, tay dung
// yen thi ket thuc, tu gui /api/v1/predictions, noi chu vao ban dich truc tiep roi quay ve Sang sang. Logic gui,
// lich su va transcript dung lai useRecognition (khong doi contract API).
import { useCallback, useEffect, useRef, useState } from 'react';
import { useRecognition, type RecognitionApi } from '../recognition/useRecognition';
import type { RecognitionController } from '../recognition/recognitionController';
import type { PredictionResponse } from '../../types/inference-api';
import { LiveSegmenter, type Presence } from './liveSegmenter';
import { createPresenceDetector, type PresenceDetector, type PresenceDetectorFactory } from './presenceDetector';

export type LiveStatus = 'off' | 'starting' | 'noPerson' | 'partial' | 'ready' | 'recording'
  | 'translating' | 'translated' | 'rejected' | 'paused' | 'error';

export interface PresenceParts { person: boolean; face: boolean; hands: number }

export const liveTiming = {
  /** Chu ky phat hien (~10 khung/giay). */
  detectIntervalMs: 100,
  /** Thoi gian giu ket qua tren man hinh truoc khi quay ve Sang sang. */
  translatedHoldMs: 1200,
  rejectedHoldMs: 1500,
  errorHoldMs: 2500,
} as const;

export interface LiveRecognition extends RecognitionController {
  liveStatus: LiveStatus;
  /** Ket qua gan nhat, giu tren man hinh toi khi bat dau ky hieu tiep theo hoac tat camera. */
  lastResult: PredictionResponse | null;
  presence: PresenceParts;
  detectorError: boolean;
  paused: boolean;
  pause: () => void;
  resume: () => void;
  start: () => Promise<void>;
  stop: () => void;
}

const NO_PRESENCE: PresenceParts = { person: false, face: false, hands: 0 };

export function useLiveRecognition(api?: RecognitionApi,
  detectorFactory: PresenceDetectorFactory = createPresenceDetector): LiveRecognition {
  const recognition = useRecognition(api);
  const { camera, state, model, compatibilityError } = recognition;
  const view = camera.view;
  const [detector, setDetector] = useState<PresenceDetector | null>(null);
  const [detectorError, setDetectorError] = useState(false);
  const [presence, setPresence] = useState<Presence>('none');
  const [parts, setParts] = useState<PresenceParts>(NO_PRESENCE);
  const [paused, setPaused] = useState(false);
  const [lastResult, setLastResult] = useState<PredictionResponse | null>(null);
  const segmenter = useRef(new LiveSegmenter());
  const loading = useRef(false);
  const latest = useRef(recognition);
  latest.current = recognition;

  // Nap bo phat hien mot lan khi camera da chay; tai su dung cho cac lan bat lai
  useEffect(() => {
    if (view.phase !== 'preview' || detector || loading.current || detectorError) return;
    loading.current = true;
    let cancelled = false;
    detectorFactory().then(created => {
      if (cancelled) { created.close(); return; }
      setDetector(created);
    }, () => { if (!cancelled) setDetectorError(true); })
      .finally(() => { loading.current = false; });
    return () => { cancelled = true; };
  }, [view.phase, detector, detectorError, detectorFactory]);

  useEffect(() => () => detector?.close(), [detector]);

  const busy = state.phase === 'submitting' || state.phase === 'result'
    || (state.phase === 'error' && 'source' in state) || view.phase === 'captured' || view.phase === 'stopping';
  const watching = !!detector && !paused && (view.phase === 'preview' || view.phase === 'recording');

  // Vong phat hien: cap nhat trang thai nguoi/mat/tay va tu bat dau/ket thuc doan
  useEffect(() => {
    if (!watching || !detector) return;
    const timer = setInterval(() => {
      const current = latest.current;
      const video = current.camera.videoRef.current;
      if (!video || video.readyState < 2) return;
      let frame;
      try { frame = detector.detect(video, performance.now()); } catch { setDetectorError(true); return; }
      const result = segmenter.current.step(frame, performance.now());
      setPresence(result.presence);
      setParts(previous => previous.person === frame.person && previous.face === frame.face
        && previous.hands === frame.hands ? previous : { person: frame.person, face: frame.face, hands: frame.hands });
      const phase = current.camera.view.phase;
      if (result.action === 'start') {
        if (phase === 'preview' && current.model.status === 'ready') { setLastResult(null); current.startRecording(); }
        else segmenter.current.reset();
      } else if (result.action === 'stop' && phase === 'recording') current.stopRecording();
      else if (result.action === 'discard' && phase === 'recording') current.cancel();
    }, liveTiming.detectIntervalMs);
    return () => clearInterval(timer);
  }, [watching, detector]);

  // Doan vua ghi xong: tu gui (nguoi dung bat camera la dong y dich truc tiep)
  useEffect(() => {
    if (view.phase !== 'captured' || state.phase !== 'captured') return;
    if (model.status === 'ready') void latest.current.submit();
    // Model mat ket noi giua chung: bo doan, khong giu video trong bo nho
    else if (model.status === 'unavailable') latest.current.cancel();
  }, [view, state.phase, model.status]);

  // Sau khi co ket qua/loi tam thoi: giu tren man hinh mot luc roi bo doan, quay ve Sang sang
  useEffect(() => {
    let hold: number | null = null;
    if (state.phase === 'result') {
      setLastResult(state.result);
      hold = state.result.accepted ? liveTiming.translatedHoldMs : liveTiming.rejectedHoldMs;
    }
    else if (state.phase === 'error' && 'source' in state) hold = liveTiming.errorHoldMs;
    if (hold === null) return;
    const timer = setTimeout(() => {
      segmenter.current.reset();
      latest.current.cancel();
    }, hold);
    return () => clearTimeout(timer);
  }, [state]);

  const pause = useCallback(() => {
    segmenter.current.reset();
    setPaused(true);
    const current = latest.current;
    if (['recording', 'stopping', 'captured'].includes(current.camera.view.phase)) current.cancel();
  }, []);
  const resume = useCallback(() => { segmenter.current.reset(); setPaused(false); }, []);

  // Chuyen tab/an trang thi tam dung de khong ghi khi nguoi dung khong nhin thay
  useEffect(() => {
    const onVisibility = () => { if (document.visibilityState === 'hidden') pause(); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [pause]);

  const start = useCallback(async () => {
    segmenter.current.reset();
    setPaused(false);
    setDetectorError(false);
    setPresence('none');
    setParts(NO_PRESENCE);
    await latest.current.enableCamera();
  }, []);
  const stop = useCallback(() => {
    segmenter.current.reset();
    setLastResult(null);
    setPaused(false);
    setPresence('none');
    setParts(NO_PRESENCE);
    latest.current.reset();
  }, []);

  let liveStatus: LiveStatus;
  if (view.phase === 'idle') liveStatus = 'off';
  else if (view.phase === 'error' || detectorError || compatibilityError) liveStatus = 'error';
  else if (view.phase === 'permission' || !detector) liveStatus = 'starting';
  else if (paused) liveStatus = 'paused';
  else if (state.phase === 'submitting') liveStatus = 'translating';
  else if (state.phase === 'result') liveStatus = state.result.accepted ? 'translated' : 'rejected';
  else if (state.phase === 'error') liveStatus = 'error';
  else if (busy) liveStatus = 'translating';
  else if (view.phase === 'recording') liveStatus = 'recording';
  else liveStatus = presence === 'ready' ? 'ready' : presence === 'partial' ? 'partial' : 'noPerson';

  return { ...recognition, liveStatus, lastResult, presence: parts, detectorError, paused, pause, resume, start, stop };
}
