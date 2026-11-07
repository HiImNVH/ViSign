# services/inference-api/tests/unit/test_feature_extraction.py
# Kiem tra adapter dac trung T037: goi pipeline chung, doi loi sang ma API va khong giu landmark tho.
import dataclasses
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from visign_api.config import Settings
from visign_api.domain.errors import (
    ClipDecodeFailedException,
    ErrorCode,
    ModelNotReadyException,
    PredictionFailedException,
)
from visign_api.inference.feature_extraction import (
    ExtractedFeatures,
    FeatureExtractor,
    FeatureSource,
    PipelineBinding,
)

TARGET_FRAME_COUNT = 32
LANDMARK_COUNT = 78
SAMPLED_FRAME_COUNT = 4
DRAFT_SCHEMA_VERSION = "visign-xy-32-v0.3-draft"


class FakePipelineError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def build_pipeline_result(**overrides: Any) -> dict[str, Any]:
    # Hand trai co o frame 0 va 1, tay phai o frame 1 va 2: 3/4 frame co it nhat mot ban tay
    group_mask = np.array(
        [
            [True, False, True, True],
            [True, True, True, True],
            [False, True, True, False],
            [False, False, True, True],
        ]
    )
    pipeline_result: dict[str, Any] = {
        "tensor": np.zeros((TARGET_FRAME_COUNT, LANDMARK_COUNT * 3), dtype=np.float32),
        "tensor_mask": np.ones((TARGET_FRAME_COUNT, LANDMARK_COUNT), dtype=bool),
        "masks": group_mask,
        "coords": np.full(
            (SAMPLED_FRAME_COUNT, LANDMARK_COUNT, 2), 0.5, dtype=np.float32
        ),
        "ambiguous": [{"candidateXY": [[0.1, 0.2]]}],
        "schema": {
            "featureSchemaVersion": DRAFT_SCHEMA_VERSION,
            "targetFrameCount": TARGET_FRAME_COUNT,
            "landmarkOrder": [f"POINT_{index}" for index in range(LANDMARK_COUNT)],
        },
        "report": {
            "frameCount": SAMPLED_FRAME_COUNT,
            "decodedFrameCount": 46,
            "inputStatus": "HAS_USABLE_FRAMES",
            "finiteTensor": True,
            "timingsMs": {"decode": 24.4, "total": 2580.6},
        },
    }
    pipeline_result.update(overrides)
    return pipeline_result


class RecordingPipeline:
    def __init__(self, pipeline_result: Mapping[str, Any] | None = None) -> None:
        self.pipeline_result = pipeline_result or build_pipeline_result()
        self.calls: list[dict[str, Any]] = []

    def __call__(self, path: Path, **options: Any) -> Mapping[str, Any]:
        self.calls.append({"path": path, **options})
        return self.pipeline_result


class FailingPipeline:
    def __init__(self, raised_error: Exception) -> None:
        self.raised_error = raised_error

    def __call__(self, path: Path, **options: Any) -> Mapping[str, Any]:
        raise self.raised_error


def build_extractor(
    pipeline: Any, feature_source: FeatureSource | None = None
) -> FeatureExtractor:
    return FeatureExtractor(
        PipelineBinding(run=pipeline, errorType=FakePipelineError),
        feature_source or FeatureSource(),
    )


def test_pipeline_receives_clip_path_and_feature_source(tmp_path: Path) -> None:
    recording_pipeline = RecordingPipeline()
    feature_source = FeatureSource(
        expectedSchemaVersion=DRAFT_SCHEMA_VERSION,
        schemaPath=tmp_path / "feature_schema.json",
        modelDirectory=tmp_path / "models",
    )

    build_extractor(recording_pipeline, feature_source).extract(tmp_path / "clip.webm")

    assert recording_pipeline.calls == [
        {
            "path": tmp_path / "clip.webm",
            "expected_schema_version": DRAFT_SCHEMA_VERSION,
            "schema_path": tmp_path / "feature_schema.json",
            "model_dir": tmp_path / "models",
        }
    ]


def test_features_keep_tensor_mask_and_quality_hints_only(tmp_path: Path) -> None:
    extracted = build_extractor(RecordingPipeline()).extract(tmp_path / "clip.webm")

    assert isinstance(extracted, ExtractedFeatures)
    assert extracted.tensor.shape == (TARGET_FRAME_COUNT, LANDMARK_COUNT * 3)
    assert extracted.tensorMask.shape == (TARGET_FRAME_COUNT, LANDMARK_COUNT)
    assert extracted.groupMask.shape == (SAMPLED_FRAME_COUNT, 4)
    assert extracted.featureSchemaVersion == DRAFT_SCHEMA_VERSION
    assert extracted.inputStatus == "HAS_USABLE_FRAMES"
    assert extracted.qualityHints.handsDetectedRatio == pytest.approx(0.75)
    assert extracted.qualityHints.frameCount == 46
    assert (extracted.decodeMs, extracted.extractMs) == (24, 2556)


def test_raw_landmarks_never_leave_the_adapter(tmp_path: Path) -> None:
    # FR-019: toa do landmark va ung vien tay khong duoc di vao ket qua phuc vu response/log
    extracted = build_extractor(RecordingPipeline()).extract(tmp_path / "clip.webm")

    kept_fields = {field.name for field in dataclasses.fields(extracted)}
    assert kept_fields == {
        "tensor",
        "tensorMask",
        "groupMask",
        "featureSchemaVersion",
        "inputStatus",
        "qualityHints",
        "decodeMs",
        "extractMs",
    }


@pytest.mark.parametrize(
    ("pipeline_code", "expected_exception", "expected_code"),
    [
        ("INVALID_TIMESTAMPS", ClipDecodeFailedException, ErrorCode.CLIP_DECODE_FAILED),
        ("CLIP_TOO_SHORT", None, ErrorCode.CLIP_TOO_SHORT),
        ("FEATURE_SCHEMA_MISMATCH", ModelNotReadyException, ErrorCode.MODEL_NOT_READY),
        ("MODEL_ASSET_MISMATCH", ModelNotReadyException, ErrorCode.MODEL_NOT_READY),
        ("SOMETHING_NEW", PredictionFailedException, ErrorCode.PREDICTION_FAILED),
    ],
)
def test_pipeline_errors_become_stable_api_errors(
    tmp_path: Path,
    pipeline_code: str,
    expected_exception: type[Exception] | None,
    expected_code: ErrorCode,
) -> None:
    pipeline_error = FakePipelineError(pipeline_code)

    with pytest.raises(Exception) as raised:
        build_extractor(FailingPipeline(pipeline_error)).extract(tmp_path / "clip.webm")

    assert getattr(raised.value, "code", None) is expected_code
    if expected_exception is not None:
        assert isinstance(raised.value, expected_exception)
    # Giu ma goc cua pipeline trong chuoi exception de log server truy vet duoc
    assert raised.value.__cause__ is pipeline_error


def test_non_pipeline_errors_are_not_swallowed(tmp_path: Path) -> None:
    with pytest.raises(MemoryError):
        build_extractor(FailingPipeline(MemoryError())).extract(tmp_path / "clip.webm")


def test_tensor_shape_mismatch_fails_closed_as_model_not_ready(tmp_path: Path) -> None:
    wrong_shape_result = build_pipeline_result(
        tensor=np.zeros((16, 234), dtype=np.float32)
    )

    with pytest.raises(ModelNotReadyException):
        build_extractor(RecordingPipeline(wrong_shape_result)).extract(
            tmp_path / "clip.webm"
        )


def test_non_finite_tensor_is_reported_as_prediction_failure(tmp_path: Path) -> None:
    broken_tensor: NDArray[np.float32] = np.zeros(
        (TARGET_FRAME_COUNT, LANDMARK_COUNT * 3), dtype=np.float32
    )
    broken_tensor[0, 0] = np.nan

    with pytest.raises(PredictionFailedException):
        build_extractor(
            RecordingPipeline(build_pipeline_result(tensor=broken_tensor))
        ).extract(tmp_path / "clip.webm")


def test_feature_source_is_built_from_settings(tmp_path: Path) -> None:
    configured_settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        feature_schema_version=DRAFT_SCHEMA_VERSION,
        feature_schema_path=tmp_path / "feature_schema.json",
        visign_model_dir=tmp_path / "models",
    )

    assert FeatureSource.from_settings(configured_settings) == FeatureSource(
        expectedSchemaVersion=DRAFT_SCHEMA_VERSION,
        schemaPath=tmp_path / "feature_schema.json",
        modelDirectory=tmp_path / "models",
    )


def test_importing_adapter_does_not_load_heavy_ai_stack() -> None:
    # Moi truong API/CI khong cai torch/mediapipe; visign_ai chi duoc import trong factory
    probe = (
        "import sys, visign_api.inference.feature_extraction; "
        "heavy = [name for name in ('visign_ai', 'torch', 'mediapipe', 'cv2', 'av') if name in sys.modules]; "
        "print(','.join(heavy))"
    )

    imported_heavy_modules = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    ).stdout.strip()

    assert imported_heavy_modules == ""
