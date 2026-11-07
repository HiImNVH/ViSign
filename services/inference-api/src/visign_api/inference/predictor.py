# services/inference-api/src/visign_api/inference/predictor.py
# Giao dien predictor chung cho fixture/pilot/full va fixture predictor cho ket qua co dinh (T037, T030).
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from visign_api.domain.model_version import ModelMetadata
from visign_api.domain.prediction import PredictionQualityHints, PredictionTimings
from visign_api.inference.artifact_loader import LoadedArtifact

FIXTURE_DEFAULT_CONFIDENCE = 0.95
# Gia tri chan doan co dinh cua fixture, khong phai so do; chi de FE/E2E kiem shape response
FIXTURE_TIMINGS_MS = {"decode": 12, "extract": 35, "infer": 8}
FIXTURE_QUALITY_HINTS = {"handsDetectedRatio": 0.92, "frameCount": 30}


@dataclass(frozen=True)
class RawPrediction:
    classLabel: str
    displayText: str
    confidence: float
    timingsMs: PredictionTimings | None
    qualityHints: PredictionQualityHints | None


class Predictor(Protocol):
    @property
    def metadata(self) -> ModelMetadata: ...

    def predict(self, clip_path: Path) -> RawPrediction: ...


class FixturePredictor:
    def __init__(self, loaded_artifact: LoadedArtifact) -> None:
        self._loaded_artifact = loaded_artifact
        configured_response = loaded_artifact.fixtureResponse
        configured_label = (
            configured_response.classLabel if configured_response else None
        )
        configured_confidence = (
            configured_response.confidence if configured_response else None
        )
        self._class_label = configured_label or loaded_artifact.metadata.classLabels[0]
        self._confidence = (
            FIXTURE_DEFAULT_CONFIDENCE
            if configured_confidence is None
            else configured_confidence
        )

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        # Fixture khong doc clip: ket qua co dinh chi de kiem giao tiep FE/BE, khong phai bang chung nhan dien
        meaning_id = self.metadata.meaningMap[self._class_label]
        return RawPrediction(
            classLabel=self._class_label,
            displayText=self._loaded_artifact.displayTextMap[meaning_id],
            confidence=self._confidence,
            timingsMs=PredictionTimings(**FIXTURE_TIMINGS_MS),
            qualityHints=PredictionQualityHints(**FIXTURE_QUALITY_HINTS),
        )
