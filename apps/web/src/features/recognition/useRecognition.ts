// T041: one recognition flow using the existing camera session and API v1.
import { useCallback, useEffect, useRef, useState } from 'react';
import type { CameraView } from './cameraSession';
import { useCameraCapture } from './useCameraCapture';
import { createInferenceApi, InferenceApiError } from '../../services/inferenceApi';
import type { ArtifactKind, ModelInfo, PredictionResponse } from '../../types/inference-api';

type Api = Pick<ReturnType<typeof createInferenceApi>, 'modelInfo' | 'predict'>;

export type ModelStatus =
  | { status: 'loading' }
  | { status: 'ready'; info: ModelInfo }
  | { status: 'unavailable'; error: InferenceApiError };

type PredictionState =
  | { phase: 'submitting'; artifactKind: ArtifactKind }
  | { phase: 'result'; artifactKind: ArtifactKind; result: PredictionResponse; requestId: string }
  | { phase: 'error'; source: 'api'; artifactKind: ArtifactKind; error: InferenceApiError };

type CapturedPrediction = { captureId: number; view: PredictionState };

export type RecognitionState = CameraView | PredictionState;

function asApiError(cause: unknown): InferenceApiError {
  return cause instanceof InferenceApiError ? cause : new InferenceApiError('network', '');
}

export function useRecognition(api?: Api) {
  const [client] = useState<Api>(() => api ?? createInferenceApi());
  const camera = useCameraCapture();
  const [model, setModel] = useState<ModelStatus>({ status: 'loading' });
  const [prediction, setPrediction] = useState<CapturedPrediction | null>(null);
  const metadataController = useRef<AbortController | null>(null);
  const metadataGeneration = useRef(0);
  const readyMetadataGeneration = useRef(0);
  const activeRequest = useRef<{ clip: Blob; controller: AbortController } | null>(null);
  // Weak keys identify captures without retaining video bytes after camera disposal.
  const captureIds = useRef(new WeakMap<Blob, number>());
  const nextCaptureId = useRef(0);

  const captureIdFor = useCallback((clip: Blob) => {
    let id = captureIds.current.get(clip);
    if (id === undefined) {
      id = ++nextCaptureId.current;
      captureIds.current.set(clip, id);
    }
    return id;
  }, []);

  const abortRequest = useCallback(() => {
    const active = activeRequest.current;
    activeRequest.current = null;
    active?.controller.abort();
  }, []);

  const refreshModelInfo = useCallback(async () => {
    metadataController.current?.abort();
    const controller = new AbortController();
    metadataController.current = controller;
    const generation = ++metadataGeneration.current;
    readyMetadataGeneration.current = 0;
    setModel({ status: 'loading' });
    try {
      const { data } = await client.modelInfo({ signal: controller.signal });
      if (!controller.signal.aborted && generation === metadataGeneration.current) {
        readyMetadataGeneration.current = generation;
        setModel({ status: 'ready', info: data });
      }
    } catch (error) {
      if (!controller.signal.aborted && generation === metadataGeneration.current) {
        setModel({ status: 'unavailable', error: asApiError(error) });
      }
    }
  }, [client]);

  useEffect(() => {
    void refreshModelInfo();
    return () => {
      metadataGeneration.current += 1;
      readyMetadataGeneration.current = 0;
      metadataController.current?.abort();
      abortRequest();
    };
  }, [abortRequest, refreshModelInfo]);

  useEffect(() => {
    // pagehide also covers back/forward-cache navigation, where React may stay mounted.
    const onPageHide = () => {
      metadataGeneration.current += 1;
      readyMetadataGeneration.current = 0;
      metadataController.current?.abort();
      abortRequest();
      setPrediction(null);
    };
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted) void refreshModelInfo();
    };
    window.addEventListener('pagehide', onPageHide);
    window.addEventListener('pageshow', onPageShow);
    return () => {
      window.removeEventListener('pagehide', onPageHide);
      window.removeEventListener('pageshow', onPageShow);
    };
  }, [abortRequest, refreshModelInfo]);

  // Camera actions can also be invoked directly on the session by the existing UI.
  // A changed/discarded clip must invalidate its in-flight prediction.
  useEffect(() => {
    const current = activeRequest.current;
    if (current && (camera.view.phase !== 'captured' || camera.view.clip !== current.clip)) abortRequest();
  }, [abortRequest, camera.view]);

  const clearPrediction = useCallback(() => {
    abortRequest();
    setPrediction(null);
  }, [abortRequest]);

  const enableCamera = useCallback(() => camera.session.enable(camera.videoRef.current), [camera.session, camera.videoRef]);
  const startRecording = useCallback(() => { clearPrediction(); camera.session.record(); }, [camera.session, clearPrediction]);
  const stopRecording = useCallback(() => camera.session.stop(), [camera.session]);
  const cancel = useCallback(() => { clearPrediction(); camera.session.cancel(); }, [camera.session, clearPrediction]);
  const reset = useCallback(() => { clearPrediction(); camera.session.reset(); }, [camera.session, clearPrediction]);
  const reloadModelInfo = useCallback(() => {
    clearPrediction();
    void refreshModelInfo();
  }, [clearPrediction, refreshModelInfo]);

  const submit = useCallback(async () => {
    const view = camera.view;
    if (view.phase !== 'captured' || model.status !== 'ready' || activeRequest.current
      || readyMetadataGeneration.current !== metadataGeneration.current
      || camera.session.view.phase !== 'captured' || camera.session.view.clip !== view.clip) return;

    const captureId = captureIdFor(view.clip);
    if (prediction?.captureId === captureId
      && (prediction.view.phase === 'submitting' || prediction.view.phase === 'result')) return;

    const controller = new AbortController();
    const request = { clip: view.clip, controller };
    const { info } = model;
    activeRequest.current = request; // synchronous guard against rapid double clicks
    setPrediction({ captureId, view: { phase: 'submitting', artifactKind: info.artifactKind } });
    try {
      const { data, requestId } = await client.predict(view.clip, { signal: controller.signal });
      if (activeRequest.current !== request || controller.signal.aborted
        || camera.session.view.phase !== 'captured' || camera.session.view.clip !== view.clip) return;
      if (data.modelVersion !== info.modelVersion) {
        setPrediction({ captureId, view: { phase: 'error', source: 'api', artifactKind: info.artifactKind,
          error: new InferenceApiError('invalid-response', requestId) } });
        void refreshModelInfo(); // discard the stale result; never resubmit automatically
      } else {
        setPrediction({ captureId, view: { phase: 'result', artifactKind: info.artifactKind, result: data, requestId } });
      }
    } catch (error) {
      if (activeRequest.current === request && !controller.signal.aborted) {
        setPrediction({ captureId, view: { phase: 'error', source: 'api', artifactKind: info.artifactKind,
          error: asApiError(error) } });
      }
    } finally {
      if (activeRequest.current === request) activeRequest.current = null;
    }
  }, [camera.session, camera.view, captureIdFor, client, model, prediction, refreshModelInfo]);

  const state: RecognitionState = prediction !== null && camera.view.phase === 'captured'
    && prediction.captureId === captureIds.current.get(camera.view.clip)
    ? prediction.view : camera.view;

  return {
    state, model, camera, enableCamera, startRecording, stopRecording,
    submit, cancel, reset, reloadModelInfo,
  };
}
