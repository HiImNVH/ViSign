import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from pathlib import Path
from threading import Lock

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .errors import PipelineError
from .sequence_transform import schema_digest


def resolve_model_dir(path=None):
    return Path(
        path
        or os.environ.get(
            "VISIGN_MODEL_DIR", Path(__file__).resolve().parents[3] / "models"
        )
    )


def _read_model(model_dir, filename):
    try:
        return (model_dir / filename).read_bytes()
    except OSError as exc:
        raise PipelineError(
            "MODEL_ASSET_MISMATCH", f"Không đọc được detector {filename}."
        ) from exc


def extractor_identity(schema, model_dir=None):
    directory = resolve_model_dir(model_dir)
    return _verify_models(schema, lambda filename: _read_model(directory, filename))


def _verify_models(schema, read_model):
    assets = {}
    for filename in schema["modelFiles"].values():
        assets[filename] = hashlib.sha256(read_model(filename)).hexdigest()
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


class PreparedDetectors:
    """One unused detector set leased by the context that prepared it."""

    def __init__(self, detectors, schema, directory):
        self._detectors = detectors
        self._schema_hash = schema_digest(schema)
        self._directory = directory
        self._available = True
        self._lock = Lock()

    @contextmanager
    def _claim(self, schema, directory):
        if schema_digest(schema) != self._schema_hash:
            raise PipelineError(
                "FEATURE_SCHEMA_MISMATCH", "Schema không khớp bộ detector đã chuẩn bị."
            )
        if directory.resolve() != self._directory:
            raise PipelineError(
                "MODEL_ASSET_MISMATCH", "Thư mục không khớp bộ detector đã chuẩn bị."
            )
        with self._lock:
            if not self._available:
                raise RuntimeError("Prepared detectors may only be used for one clip")
            self._available = False
            yield self._detectors


@contextmanager
def prepare_detectors(schema, model_dir=None):
    """Open fresh verified detectors. Keep the context open through extraction."""
    directory = resolve_model_dir(model_dir).resolve()
    models = {
        filename: _read_model(directory, filename)
        for filename in schema["modelFiles"].values()
    }
    identity = _verify_models(schema, models.__getitem__)
    if identity["version"] != schema["extractorVersion"]:
        raise PipelineError(
            "EXTRACTOR_VERSION_MISMATCH", "Extractor khác phiên bản schema đã khóa."
        )
    with ExitStack() as stack:
        detectors = [
            stack.enter_context(_create_detector(*args))
            for args in _detector_args(schema, models.__getitem__)
        ]
        prepared = PreparedDetectors(detectors, schema, directory)
        try:
            yield prepared
        finally:
            with prepared._lock:
                prepared._available = False
                stack.close()


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


def extract(frames, timestamps, schema, model_dir=None, *, prepared_detectors=None):
    model_dir = resolve_model_dir(model_dir)
    n, count = len(frames), len(schema["landmarkOrder"])
    coords = np.full((n, count, 2), np.nan, dtype=np.float32)
    valid = np.zeros((n, count), dtype=bool)
    visibility = np.full((n, count), np.nan, np.float32)
    presence = np.full((n, count), np.nan, np.float32)
    hand_scores = np.full((n, 2), np.nan, np.float32)
    ambiguous = []
    with ExitStack() as stack:
        if prepared_detectors is None:
            detector_args = _detector_args(
                schema, lambda filename: model_dir / filename
            )
        else:
            detectors = stack.enter_context(
                prepared_detectors._claim(schema, model_dir)
            )
        if schema.get("detectorExecution") == "parallel-by-group":
            pool = stack.enter_context(ThreadPoolExecutor(max_workers=3))
            if prepared_detectors is None:
                futures = [
                    pool.submit(_detect_new_sequence, args, frames, timestamps)
                    for args in detector_args
                ]
            else:
                futures = [
                    pool.submit(_detect_sequence, detector, frames, timestamps)
                    for detector in detectors
                ]
            groups = [future.result() for future in futures]
            results = zip(*groups)
        else:
            if prepared_detectors is None:
                detectors = [
                    stack.enter_context(_create_detector(*args))
                    for args in detector_args
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


def _detector_args(schema, model_for):
    specs = (
        (vision.HandLandmarker, vision.HandLandmarkerOptions, "hand", {"num_hands": 2}),
        (vision.PoseLandmarker, vision.PoseLandmarkerOptions, "pose", {}),
        (vision.FaceLandmarker, vision.FaceLandmarkerOptions, "face", {}),
    )
    return [
        (detector, options, model_for(schema["modelFiles"][name]), kwargs)
        for detector, options, name, kwargs in specs
    ]


def _create_detector(detector, options, model, kwargs):
    data = model.read_bytes() if isinstance(model, Path) else model
    base = python.BaseOptions(model_asset_buffer=data)
    return detector.create_from_options(
        options(base_options=base, running_mode=vision.RunningMode.VIDEO, **kwargs)
    )


def _detect_new_sequence(detector_args, frames, timestamps):
    # Initialize and close on the same worker. Tracking state stays local to this clip.
    with _create_detector(*detector_args) as detector:
        return _detect_sequence(detector, frames, timestamps)


def _detect_sequence(detector, frames, timestamps):
    return [
        detector.detect_for_video(
            mp.Image(
                image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame)
            ),
            int(timestamp),
        )
        for frame, timestamp in zip(frames, timestamps)
    ]
