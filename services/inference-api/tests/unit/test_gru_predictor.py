# services/inference-api/tests/unit/test_gru_predictor.py
# Kiem adapter GRU T037 bang extractor/classifier gia: top-1 theo thu tu classLabels, timings va fail closed.
import dataclasses
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from visign_api.config import Settings
from visign_api.domain.errors import (
    ClipDecodeFailedException,
    ClipTooShortException,
    InsufficientLandmarksException,
    NoPersonDetectedException,
    PredictionFailedException,
    ViSignApiException,
)
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.domain.prediction import PredictionQualityHints
from visign_api.inference import gru_predictor
from visign_api.inference.artifact_loader import (
    MODEL_INFO_FILE,
    ArtifactRejectedError,
    LoadedArtifact,
)
from visign_api.inference.clip_validator import DurationWindow
from visign_api.inference.feature_extraction import ExtractedFeatures
from visign_api.inference.gru_predictor import (
    GruComponents,
    GruPredictor,
    GruRuntime,
    load_gru_predictor,
)
from visign_api.inference.predictor import FixturePredictor, Predictor
from visign_api.inference.predictor_registry import (
    PredictorRegistry,
    build_predictor_factories,
)

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
CLIP_PATH = Path("uploaded-clip.webm")
TARGET_FRAME_COUNT = 32
LANDMARK_COUNT = 78
PILOT_CLASS_LABELS = ["SOT_HCM_1", "CAM_ON_HN_1", "NHAN_HCM_1"]
PILOT_MEANING_MAP = {"SOT_HCM_1": "SOT", "CAM_ON_HN_1": "CAM_ON", "NHAN_HCM_1": "NHAN"}
PILOT_DISPLAY_TEXTS = {"SOT": "Sốt", "CAM_ON": "Cảm ơn", "NHAN": "Nhận"}
CONTRACT_WINDOW = DurationWindow(minMs=300, maxMs=6000)

ExtractionBehavior = Callable[[Path], ExtractedFeatures]


def pilot_artifact() -> LoadedArtifact:
    pilot_metadata = ModelMetadata(
        modelVersion="pilot-gru-test-v1",
        artifactKind=ArtifactKind.PILOT,
        datasetVersion="pilot-v1",
        featureSchemaVersion="visign-xy-32-v0.3-draft",
        extractorVersion="tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3",
        meanings=list(PILOT_DISPLAY_TEXTS),
        classLabels=list(PILOT_CLASS_LABELS),
        meaningMap=dict(PILOT_MEANING_MAP),
        acceptanceThreshold=0.7,
    )
    return LoadedArtifact(
        directory=Path("pilot-artifact"),
        metadata=pilot_metadata,
        displayTextMap=dict(PILOT_DISPLAY_TEXTS),
        fixtureResponse=None,
    )


def extracted_features() -> ExtractedFeatures:
    return ExtractedFeatures(
        tensor=np.full(
            (TARGET_FRAME_COUNT, 3 * LANDMARK_COUNT), 0.25, dtype=np.float32
        ),
        tensorMask=np.ones((TARGET_FRAME_COUNT, LANDMARK_COUNT), dtype=bool),
        groupMask=np.ones((TARGET_FRAME_COUNT, 4), dtype=bool),
        featureSchemaVersion="visign-xy-32-v0.3-draft",
        inputStatus="HAS_USABLE_FRAMES",
        qualityHints=PredictionQualityHints(handsDetectedRatio=0.75, frameCount=46),
        decodeMs=21,
        extractMs=1480,
        ptsSpanMs=1500.0,
        detectedAnyLandmark=True,
    )


class StubExtractor:
    def __init__(self, extraction_behavior: ExtractionBehavior) -> None:
        self._extraction_behavior = extraction_behavior

    def extract(self, clip_path: Path) -> ExtractedFeatures:
        return self._extraction_behavior(clip_path)


class StubClassifier:
    def __init__(self, class_probabilities: NDArray[np.float32]) -> None:
        self._class_probabilities = class_probabilities
        self.seen_tensors: list[NDArray[np.float32]] = []

    def class_probabilities(
        self, feature_tensor: NDArray[np.float32]
    ) -> NDArray[np.float32]:
        self.seen_tensors.append(feature_tensor)
        return self._class_probabilities


def predictor_with(
    stub_classifier: StubClassifier, extraction_behavior: ExtractionBehavior
) -> GruPredictor:
    gru_components = GruComponents(
        featureExtractor=StubExtractor(extraction_behavior),
        classifier=stub_classifier,
        durationWindow=CONTRACT_WINDOW,
    )
    return GruPredictor(pilot_artifact(), gru_components)


def test_top_probability_maps_to_trained_class_order() -> None:
    served_features = extracted_features()
    stub_classifier = StubClassifier(np.array([0.1, 0.75, 0.15], dtype=np.float32))

    raw_prediction = predictor_with(
        stub_classifier, lambda clip_path: served_features
    ).predict(CLIP_PATH)

    # Chi so 1 trong classLabels da train la CAM_ON_HN_1, khong phai thu tu bang chu cai
    assert raw_prediction.classLabel == "CAM_ON_HN_1"
    assert raw_prediction.displayText == "Cảm ơn"
    assert raw_prediction.confidence == pytest.approx(0.75)
    assert stub_classifier.seen_tensors == [served_features.tensor]
    assert raw_prediction.qualityHints == served_features.qualityHints


def test_stage_timings_come_from_extraction_and_inference() -> None:
    stub_classifier = StubClassifier(np.array([0.6, 0.3, 0.1], dtype=np.float32))

    raw_prediction = predictor_with(
        stub_classifier, lambda clip_path: extracted_features()
    ).predict(CLIP_PATH)

    assert raw_prediction.timingsMs is not None
    assert raw_prediction.timingsMs.decode == 21
    assert raw_prediction.timingsMs.extract == 1480
    assert raw_prediction.timingsMs.infer >= 0


def test_gru_predictor_satisfies_predictor_protocol() -> None:
    stub_classifier = StubClassifier(np.array([1.0, 0.0, 0.0], dtype=np.float32))
    served_predictor: Predictor = predictor_with(
        stub_classifier, lambda clip_path: extracted_features()
    )

    assert served_predictor.metadata.artifactKind is ArtifactKind.PILOT


@pytest.mark.parametrize(
    "invalid_probabilities",
    [
        np.array([0.5, 0.5], dtype=np.float32),
        np.array([[0.1, 0.8, 0.1]], dtype=np.float32),
        np.array([0.2, np.nan, 0.8], dtype=np.float32),
        np.array([-0.1, 0.6, 0.5], dtype=np.float32),
        np.array([0.1, 1.2, 0.0], dtype=np.float32),
    ],
)
def test_invalid_class_probabilities_fail_closed(
    invalid_probabilities: NDArray[np.float32],
) -> None:
    # Dau ra lech so lop hoac khong phai xac suat: 500 an toan thay vi gan nham nghia
    stub_classifier = StubClassifier(invalid_probabilities)

    with pytest.raises(PredictionFailedException):
        predictor_with(stub_classifier, lambda clip_path: extracted_features()).predict(
            CLIP_PATH
        )


def test_extraction_failure_skips_classification() -> None:
    def fail_decoding(clip_path: Path) -> ExtractedFeatures:
        raise ClipDecodeFailedException()

    stub_classifier = StubClassifier(np.array([1.0, 0.0, 0.0], dtype=np.float32))

    with pytest.raises(ClipDecodeFailedException):
        predictor_with(stub_classifier, fail_decoding).predict(CLIP_PATH)
    assert stub_classifier.seen_tensors == []


NO_DETECTION = {
    "inputStatus": "INSUFFICIENT_LANDMARKS",
    "groupMask": np.zeros((TARGET_FRAME_COUNT, 4), dtype=bool),
    "tensorMask": np.zeros((TARGET_FRAME_COUNT, LANDMARK_COUNT), dtype=bool),
    "detectedAnyLandmark": False,
}


@pytest.mark.parametrize(
    ("feature_overrides", "expected_error"),
    [
        ({"inputStatus": "INSUFFICIENT_LANDMARKS"}, InsufficientLandmarksException),
        (NO_DETECTION, NoPersonDetectedException),
        ({"ptsSpanMs": 120.0}, ClipTooShortException),
    ],
)
def test_unusable_clip_is_rejected_before_classification(
    feature_overrides: dict[str, Any], expected_error: type[ViSignApiException]
) -> None:
    # T049: clip khong nguoi tung duoc GRU tra "Cam on" accepted; phai chan truoc khi phan lop
    unusable_features = dataclasses.replace(extracted_features(), **feature_overrides)
    stub_classifier = StubClassifier(np.array([0.05, 0.9, 0.05], dtype=np.float32))

    with pytest.raises(expected_error):
        predictor_with(stub_classifier, lambda clip_path: unusable_features).predict(
            CLIP_PATH
        )
    assert stub_classifier.seen_tensors == []


def test_missing_serving_extra_rejects_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # May chi cai goi API (khong co torch/visign_ai) phai degraded thay vi crash khi nap pilot/full
    monkeypatch.setattr(
        gru_predictor, "SERVING_EXTRA_MODULES", ("visign_goi_khong_ton_tai",)
    )

    # Phai bi chan ngay buoc kiem goi, truoc khi cham toi file artifact hay import torch
    with pytest.raises(ArtifactRejectedError, match="visign_goi_khong_ton_tai"):
        load_gru_predictor(pilot_artifact(), GruRuntime(modelDirectory=None))


def write_pilot_model_info(artifact_directory: Path) -> Path:
    model_info = json.loads(
        (FIXTURE_ARTIFACTS / "fixture" / MODEL_INFO_FILE).read_text(encoding="utf-8")
    )
    model_info["artifactKind"] = ArtifactKind.PILOT.value
    artifact_directory.mkdir(parents=True)
    (artifact_directory / MODEL_INFO_FILE).write_text(
        json.dumps(model_info), encoding="utf-8"
    )
    return artifact_directory


def test_default_factories_cover_every_artifact_kind() -> None:
    predictor_factories = build_predictor_factories(GruRuntime(modelDirectory=None))

    assert set(predictor_factories) == set(ArtifactKind)
    assert predictor_factories[ArtifactKind.FIXTURE] is FixturePredictor


def test_pilot_without_weights_is_rejected_and_fixture_keeps_serving(
    tmp_path: Path,
) -> None:
    # Khong co model.pt/feature_schema.json: adapter GRU tu choi, registry giu predictor cu
    predictor_registry = PredictorRegistry(
        build_predictor_factories(GruRuntime(modelDirectory=None))
    )
    predictor_registry.activate(FIXTURE_ARTIFACTS / "fixture", None)

    with pytest.raises(ArtifactRejectedError):
        predictor_registry.activate(write_pilot_model_info(tmp_path / "pilot"), None)

    assert isinstance(predictor_registry.active_predictor, FixturePredictor)
    assert predictor_registry.active_artifact_directory == FIXTURE_ARTIFACTS / "fixture"


def test_runtime_takes_detector_directory_and_duration_window_from_settings(
    tmp_path: Path,
) -> None:
    configured_settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        visign_model_dir=tmp_path / "detectors",
        min_duration_ms=500,
        max_duration_ms=5000,
    )

    gru_runtime = GruRuntime.from_settings(configured_settings)

    assert gru_runtime.modelDirectory == tmp_path / "detectors"
    assert gru_runtime.durationWindow == DurationWindow(minMs=500, maxMs=5000)
