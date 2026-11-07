import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .errors import PipelineError


def resolve_model_dir(path=None):
    return Path(
        path
        or os.environ.get(
            "VISIGN_MODEL_DIR", Path(__file__).resolve().parents[3] / "models"
        )
    )


def extractor_identity(schema, model_dir=None):
    model_dir = resolve_model_dir(model_dir)
    assets = {}
    for filename in schema["modelFiles"].values():
        try:
            assets[filename] = hashlib.sha256(
                (model_dir / filename).read_bytes()
            ).hexdigest()
        except OSError as exc:
            raise PipelineError(
                "MODEL_ASSET_MISMATCH", f"Không đọc được detector {filename}."
            ) from exc
    expected = json.loads(
        (
            Path(__file__).resolve().parents[3] / "configs/download-manifest.json"
        ).read_text("utf-8-sig")
    )
    if {item["name"] for item in expected} != set(assets):
        raise PipelineError("MODEL_ASSET_MISMATCH", "Danh sách detector không khớp.")
    for item in expected:
        if assets.get(item["name"]) != item["sha256"].lower():
            raise PipelineError(
                "MODEL_ASSET_MISMATCH", "Hash detector không khớp bản đã tải."
            )
    digest = hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest()[
        :16
    ]
    return {
        "version": f"tasks-hand-pose-face-{mp.__version__}-{digest}",
        "sha256": assets,
    }


def group_masks(valid):
    """Group pose flag means shoulders available, not all six arm points."""
    return np.column_stack(
        [
            valid[:, :21].all(axis=1),
            valid[:, 21:42].all(axis=1),
            valid[:, 42:44].all(axis=1),
            valid[:, 48:].all(axis=1),
        ]
    )


def extract(frames, timestamps, schema, model_dir=None):
    model_dir = resolve_model_dir(model_dir)
    n, count = len(frames), len(schema["landmarkOrder"])
    coords = np.full((n, count, 2), np.nan, dtype=np.float32)
    valid = np.zeros((n, count), dtype=bool)
    visibility = np.full((n, count), np.nan, np.float32)
    presence = np.full((n, count), np.nan, np.float32)
    hand_scores = np.full((n, 2), np.nan, np.float32)
    ambiguous = []
    detector_specs = (
        (vision.HandLandmarker, vision.HandLandmarkerOptions, "hand", {"num_hands": 2}),
        (vision.PoseLandmarker, vision.PoseLandmarkerOptions, "pose", {}),
        (vision.FaceLandmarker, vision.FaceLandmarkerOptions, "face", {}),
    )
    detector_args = [
        (detector, options, model_dir / schema["modelFiles"][name], kwargs)
        for detector, options, name, kwargs in detector_specs
    ]
    with ExitStack() as stack:
        if schema.get("detectorExecution") == "parallel-by-group":
            pool = stack.enter_context(ThreadPoolExecutor(max_workers=3))
            futures = [
                pool.submit(_detect_sequence, args, frames, timestamps)
                for args in detector_args
            ]
            groups = [future.result() for future in futures]
            results = zip(*groups)
        else:
            detectors = [
                stack.enter_context(_create_detector(*args)) for args in detector_args
            ]
            results = (
                _detect_frame(detectors, frame, stamp)
                for frame, stamp in zip(frames, timestamps)
            )
        for i, (hand, pose, face) in enumerate(results):
            # Keep the highest-scoring candidate for each side; expose collisions explicitly.
            for landmarks, handedness in zip(hand.hand_landmarks, hand.handedness):
                label = handedness[0].category_name
                slot = 0 if label == "Left" else 1
                score = handedness[0].score
                if np.isfinite(hand_scores[i, slot]):
                    ambiguous.append(
                        {
                            "frame": i,
                            "side": label,
                            "reason": "duplicate side candidates",
                            "candidateXY": [[p.x, p.y] for p in landmarks],
                            "candidateScore": float(score),
                            "previousXY": coords[
                                i, slot * 21 : (slot + 1) * 21
                            ].tolist(),
                            "previousScore": float(hand_scores[i, slot]),
                        }
                    )
                    if score <= hand_scores[i, slot]:
                        continue
                hand_scores[i, slot] = score
                coords[i, slot * 21 : (slot + 1) * 21] = [(p.x, p.y) for p in landmarks]
                valid[i, slot * 21 : (slot + 1) * 21] = np.isfinite(
                    coords[i, slot * 21 : (slot + 1) * 21]
                ).all(axis=1)
            if pose.pose_landmarks:
                points = pose.pose_landmarks[0]
                for j, k in enumerate(schema["poseIndices"], start=42):
                    p = points[k]
                    coords[i, j] = [p.x, p.y]
                    visibility[i, j], presence[i, j] = p.visibility, p.presence
                    valid[i, j] = (
                        p.visibility >= schema["poseMinVisibility"]
                        and p.presence >= schema["poseMinPresence"]
                        and 0 <= p.x <= 1
                        and 0 <= p.y <= 1
                    )
            if face.face_landmarks:
                coords[i, 48:] = [
                    (face.face_landmarks[0][k].x, face.face_landmarks[0][k].y)
                    for k in schema["faceIndices"]
                ]
                valid[i, 48:] = np.isfinite(coords[i, 48:]).all(axis=1)
    return coords, valid, visibility, presence, hand_scores, ambiguous


def _detect_frame(detectors, frame, timestamp):
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame))
    return [detector.detect_for_video(image, int(timestamp)) for detector in detectors]


def _create_detector(detector, options, model_path, kwargs):
    base = python.BaseOptions(model_asset_buffer=model_path.read_bytes())
    return detector.create_from_options(
        options(base_options=base, running_mode=vision.RunningMode.VIDEO, **kwargs)
    )


def _detect_sequence(detector_args, frames, timestamps):
    # Initialize and close on the same worker. Tracking state stays local to this clip.
    with _create_detector(*detector_args) as detector:
        return [
            detector.detect_for_video(
                mp.Image(
                    image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame)
                ),
                int(timestamp),
            )
            for frame, timestamp in zip(frames, timestamps)
        ]
