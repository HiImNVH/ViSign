# services/inference-api/src/visign_api/inference/feature_extraction.py
# Ranh gioi API voi pipeline chung cua visign_ai: goi process_video, doi loi sang ma API,
# chi giu tensor/mask va chi so chat luong, khong de landmark tho roi khoi adapter (T037, FR-019).
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

import numpy as np
from numpy.typing import NDArray

from visign_api.config import Settings
from visign_api.domain.errors import (
    ModelNotReadyException,
    PredictionFailedException,
    build_api_exception,
)
from visign_api.domain.prediction import PredictionQualityHints
from visign_api.inference.pipeline_errors import map_pipeline_error_code

# Tensor schema v0.3: moi diem gom X, Y va mot co hop le
VALUES_PER_LANDMARK = 3
LEFT_HAND_GROUP = 0
RIGHT_HAND_GROUP = 1

FeaturePipeline = Callable[..., Mapping[str, Any]]


@dataclass(frozen=True)
class PipelineBinding:
    run: FeaturePipeline
    errorType: type[Exception]


@dataclass(frozen=True)
class FeatureSource:
    expectedSchemaVersion: str | None = None
    schemaPath: Path | None = None
    modelDirectory: Path | None = None

    @classmethod
    def from_settings(cls, runtime_settings: Settings) -> Self:
        return cls(
            expectedSchemaVersion=runtime_settings.feature_schema_version,
            schemaPath=runtime_settings.feature_schema_path,
            modelDirectory=runtime_settings.visign_model_dir,
        )


@dataclass(frozen=True)
class ExtractedFeatures:
    tensor: NDArray[np.float32]
    tensorMask: NDArray[np.bool_]
    groupMask: NDArray[np.bool_]
    featureSchemaVersion: str
    inputStatus: str
    qualityHints: PredictionQualityHints
    decodeMs: int
    extractMs: int


class FeatureExtractor:
    def __init__(
        self, pipeline_binding: PipelineBinding, feature_source: FeatureSource
    ) -> None:
        self._pipeline_binding = pipeline_binding
        self._feature_source = feature_source

    def extract(self, clip_path: Path) -> ExtractedFeatures:
        pipeline_result = self._run_pipeline(clip_path)
        ensure_tensor_matches_schema(pipeline_result)
        return build_extracted_features(pipeline_result)

    def _run_pipeline(self, clip_path: Path) -> Mapping[str, Any]:
        try:
            return self._pipeline_binding.run(
                clip_path,
                expected_schema_version=self._feature_source.expectedSchemaVersion,
                schema_path=self._feature_source.schemaPath,
                model_dir=self._feature_source.modelDirectory,
            )
        except self._pipeline_binding.errorType as pipeline_error:
            # Ma goc nam trong __cause__ de log server truy vet; client chi nhan ma on dinh cua API
            pipeline_code = str(getattr(pipeline_error, "code", ""))
            raise build_api_exception(
                map_pipeline_error_code(pipeline_code)
            ) from pipeline_error


def ensure_tensor_matches_schema(pipeline_result: Mapping[str, Any]) -> None:
    feature_schema = pipeline_result["schema"]
    expected_shape = (
        feature_schema["targetFrameCount"],
        VALUES_PER_LANDMARK * len(feature_schema["landmarkOrder"]),
    )
    feature_tensor = np.asarray(pipeline_result["tensor"])
    if feature_tensor.shape != expected_shape:
        # Tensor lech schema la loi cau hinh phuc vu: fail closed thay vi dua du lieu sai vao model
        raise ModelNotReadyException()
    if not np.isfinite(feature_tensor).all():
        raise PredictionFailedException()


def build_extracted_features(pipeline_result: Mapping[str, Any]) -> ExtractedFeatures:
    pipeline_report = pipeline_result["report"]
    stage_timings = pipeline_report["timingsMs"]
    group_mask = np.asarray(pipeline_result["masks"], dtype=bool)
    return ExtractedFeatures(
        tensor=np.asarray(pipeline_result["tensor"], dtype=np.float32),
        tensorMask=np.asarray(pipeline_result["tensor_mask"], dtype=bool),
        groupMask=group_mask,
        featureSchemaVersion=pipeline_result["schema"]["featureSchemaVersion"],
        inputStatus=pipeline_report["inputStatus"],
        qualityHints=PredictionQualityHints(
            handsDetectedRatio=hands_detected_ratio(group_mask),
            frameCount=pipeline_report["decodedFrameCount"],
        ),
        decodeMs=round(stage_timings["decode"]),
        extractMs=round(stage_timings["total"] - stage_timings["decode"]),
    )


def hands_detected_ratio(group_mask: NDArray[np.bool_]) -> float:
    frames_with_any_hand = (
        group_mask[:, LEFT_HAND_GROUP] | group_mask[:, RIGHT_HAND_GROUP]
    )
    return float(frames_with_any_hand.mean())


def build_visign_ai_binding() -> PipelineBinding:
    # Import luoi: chi may phuc vu cai extra serving moi can torch/mediapipe/opencv
    from visign_ai.landmarks.errors import PipelineError
    from visign_ai.landmarks.pipeline import process_video

    return PipelineBinding(run=process_video, errorType=PipelineError)
