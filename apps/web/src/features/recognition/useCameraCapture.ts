// apps/web/src/features/recognition/useCameraCapture.ts - Noi vong doi React voi phien camera.
import { useEffect, useRef, useState } from 'react';
import { CameraSession, type CameraView } from './cameraSession';

export function useCameraCapture() {
  const [view, setView] = useState<CameraView>({ phase: 'idle' });
  const [session] = useState(() => new CameraSession(setView));
  const videoRef = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    const onPageHide = () => session.reset();
    window.addEventListener('pagehide', onPageHide);
    return () => { window.removeEventListener('pagehide', onPageHide); session.release(); };
  }, [session]);
  return { view, session, videoRef };
}
