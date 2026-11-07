# services/inference-api/tests/unit/test_predictor_registry.py
# Kiem tra fixture predictor va registry: fail closed, giu predictor dang chay khi candidate loi (T037).
import json
from pathlib import Path

import pytest
from visign_api.domain.errors import ModelNotReadyException
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.artifact_loader import (
    MODEL_INFO_FILE,
    ArtifactRejectedError,
    LoadedArtifact,
    load_artifact,
)
from visign_api.inference.predictor import (
    FIXTURE_DEFAULT_CONFIDENCE,
    FixturePredictor,
    Predictor,
)
from visign_api.inference.predictor_registry import (
    FIXTURE_PREDICTOR_FACTORIES,
    PredictorRegistry,
)

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
CLIP_PATH = Path("unused-clip.webm")


def copy_fixture_as(target_directory: Path, artifact_kind: str) -> Path:
    model_info = json.loads(
        (FIXTURE_ARTIFACTS / "fixture" / MODEL_INFO_FILE).read_text(encoding="utf-8")
    )
    model_info["artifactKind"] = artifact_kind
    target_directory.mkdir(parents=True)
    (target_directory / MODEL_INFO_FILE).write_text(
        json.dumps(model_info), encoding="utf-8"
    )
    return target_directory


def test_fixture_predictor_returns_first_class_with_default_confidence() -> None:
    fixture_predictor = FixturePredictor(
        load_artifact(FIXTURE_ARTIFACTS / "fixture", None)
    )

    raw_prediction = fixture_predictor.predict(CLIP_PATH)

    assert raw_prediction.classLabel == "CAM_ON_HN_1"
    assert raw_prediction.displayText == "Cảm ơn"
    assert raw_prediction.confidence == FIXTURE_DEFAULT_CONFIDENCE
    assert raw_prediction.timingsMs is not None
    assert raw_prediction.qualityHints is not None
    assert fixture_predictor.predict(CLIP_PATH) == raw_prediction


def test_low_confidence_fixture_returns_configured_response() -> None:
    fixture_predictor = FixturePredictor(
        load_artifact(FIXTURE_ARTIFACTS / "fixture-low-confidence", None)
    )

    raw_prediction = fixture_predictor.predict(CLIP_PATH)

    assert raw_prediction.classLabel == "SOT_HCM_1"
    assert raw_prediction.displayText == "Sốt"
    assert raw_prediction.confidence == pytest.approx(0.42)


def test_fixture_predictor_satisfies_predictor_protocol() -> None:
    fixture_predictor: Predictor = FixturePredictor(
        load_artifact(FIXTURE_ARTIFACTS / "fixture", None)
    )

    assert fixture_predictor.metadata.artifactKind is ArtifactKind.FIXTURE


def test_registry_without_artifact_is_not_ready() -> None:
    predictor_registry = PredictorRegistry(FIXTURE_PREDICTOR_FACTORIES)

    assert predictor_registry.is_ready is False
    assert predictor_registry.active_artifact_directory is None
    with pytest.raises(ModelNotReadyException):
        _ = predictor_registry.active_predictor


def test_registry_activates_fixture_artifact() -> None:
    predictor_registry = PredictorRegistry(FIXTURE_PREDICTOR_FACTORIES)

    predictor_registry.activate(FIXTURE_ARTIFACTS / "fixture", None)

    assert predictor_registry.is_ready is True
    assert (
        predictor_registry.active_predictor.metadata.modelVersion
        == "vsl-fixture-v0.0.1"
    )
    assert predictor_registry.active_artifact_directory == FIXTURE_ARTIFACTS / "fixture"


def test_failed_candidate_keeps_previous_predictor(tmp_path: Path) -> None:
    # Rollback trong tien trinh: candidate loi khong duoc thay predictor dang phuc vu
    predictor_registry = PredictorRegistry(FIXTURE_PREDICTOR_FACTORIES)
    predictor_registry.activate(FIXTURE_ARTIFACTS / "fixture", None)

    with pytest.raises(ArtifactRejectedError):
        predictor_registry.activate(tmp_path / "missing-artifact", None)

    assert (
        predictor_registry.active_predictor.metadata.modelVersion
        == "vsl-fixture-v0.0.1"
    )
    assert predictor_registry.active_artifact_directory == FIXTURE_ARTIFACTS / "fixture"


def test_pilot_without_registered_predictor_fails_closed_without_fixture_fallback(
    tmp_path: Path,
) -> None:
    # Contract AI-BE: artifact loi khi khoi dong thi degraded, khong suy luan bang fixture thay the
    predictor_registry = PredictorRegistry(FIXTURE_PREDICTOR_FACTORIES)

    with pytest.raises(ArtifactRejectedError):
        predictor_registry.activate(copy_fixture_as(tmp_path / "pilot", "pilot"), None)

    assert predictor_registry.is_ready is False


def test_factory_failure_keeps_previous_predictor() -> None:
    # Factory nap trong so that bai (vi du model.pt hong) chi voi candidate thu hai
    def factory_rejecting_configured_response(
        loaded_artifact: LoadedArtifact,
    ) -> Predictor:
        if loaded_artifact.fixtureResponse is not None:
            raise ArtifactRejectedError("trong so model khong doc duoc")
        return FixturePredictor(loaded_artifact)

    predictor_registry = PredictorRegistry(
        {ArtifactKind.FIXTURE: factory_rejecting_configured_response}
    )
    predictor_registry.activate(FIXTURE_ARTIFACTS / "fixture", None)

    with pytest.raises(ArtifactRejectedError):
        predictor_registry.activate(FIXTURE_ARTIFACTS / "fixture-low-confidence", None)

    assert (
        predictor_registry.active_predictor.metadata.modelVersion
        == "vsl-fixture-v0.0.1"
    )
