"""Kiem trong image API: nap ca ba detector MediaPipe va chay mot frame (T091).

Bat loi thieu thu vien he thong (vi du libEGL.so.1) ma unit test ngoai container khong thay.
Chay: docker run --rm --read-only --tmpfs /tmp <image> python /app/infra/aws/smoke/mediapipe_load.py
hoac truyen file qua stdin: docker run --rm -i <image> python - < infra/aws/smoke/mediapipe_load.py
"""

import os
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

model_dir = Path(os.environ.get("VISIGN_MODEL_DIR", "/app/ai/models"))
frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((240, 320, 3), dtype=np.uint8))
detectors = [
    (vision.HandLandmarker, vision.HandLandmarkerOptions, "hand_landmarker.task"),
    (vision.PoseLandmarker, vision.PoseLandmarkerOptions, "pose_landmarker_full.task"),
    (vision.FaceLandmarker, vision.FaceLandmarkerOptions, "face_landmarker.task"),
]
for detector, options, name in detectors:
    settings = options(base_options=BaseOptions(model_asset_path=str(model_dir / name)),
                       running_mode=vision.RunningMode.VIDEO)
    with detector.create_from_options(settings) as instance:
        instance.detect_for_video(frame, 0)
    print(f"OK {name}")
