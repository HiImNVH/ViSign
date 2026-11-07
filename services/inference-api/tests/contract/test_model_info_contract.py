# services/inference-api/tests/contract/test_model_info_contract.py
# Contract test T055: GET /api/v1/health va /api/v1/model-info cho fixture/pilot/full va trang thai degraded.
import json
import uuid
from collections.abc import Iterator, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from visign_api.config import Settings
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.inference.artifact_loader import MODEL_INFO_FILE, LoadedArtifact
from visign_api.inference.predictor import FixturePredictor, RawPrediction
from visign_api.inference.predictor_registry import PredictorFactory
from visign_api.main import create_app

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
HEALTH_PATH = "/api/v1/health"
MODEL_INFO_PATH = "/api/v1/model-info"
REQUEST_ID_HEADER = "X-Request-ID"
P0_MEANINGS = [
    "GIAY_TO",
    "DAU_BUNG",
    "SOT",
    "NHAN",
    "BAN",
    "CAM_ON",
    "GIUP_DO",
    "XIN_LOI",
    "DAU_DAU",
    "KHONG",
]
MODEL_INFO_FIELDS = {
    "modelVersion",
    "artifactKind",
    "datasetVersion",
    "featureSchemaVersion",
    "extractorVersion",
    "meanings",
    "acceptanceThreshold",
    "macroF1",
    "perMeaningRecall",
    "evaluatedAt",
    "demoReady",
}


class StubModelPredictor:
    # Dung cho pilot/full khi chua co adapter GRU: chi can metadata cho model-info
    def __init__(self, loaded_artifact: LoadedArtifact) -> None:
        self._loaded_artifact = loaded_artifact

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        raise NotImplementedError("Stub chi phuc vu model-info")


STUB_FACTORIES: Mapping[ArtifactKind, PredictorFactory] = {
    ArtifactKind.FIXTURE: FixturePredictor,
    ArtifactKind.PILOT: StubModelPredictor,
    ArtifactKind.FULL: StubModelPredictor,
}


def build_client(
    runtime_settings: Settings,
    predictor_factories: Mapping[ArtifactKind, PredictorFactory] | None = None,
) -> TestClient:
    return TestClient(create_app(runtime_settings, predictor_factories))


def settings_for(artifact_path: Path | None, **overrides: Any) -> Settings:
    return Settings(_env_file=None, model_artifact_path=artifact_path, **overrides)  # type: ignore[call-arg]


def write_model_artifact(
    artifact_directory: Path, artifact_kind: str, **overrides: Any
) -> Path:
    meanings = P0_MEANINGS if artifact_kind == "full" else P0_MEANINGS[:3]
    class_labels = [f"{meaning}_HCM_1" for meaning in meanings]
    model_info: dict[str, Any] = {
        "modelVersion": f"vsl-{artifact_kind}-test",
        "artifactKind": artifact_kind,
        "datasetVersion": "p0-test",
        "featureSchemaVersion": "visign-xy-32-v0.3-draft",
        "extractorVersion": "tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3",
        "meanings": meanings,
        "classLabels": class_labels,
        "meaningMap": dict(zip(class_labels, meanings, strict=True)),
        "displayTextMap": {meaning: meaning.title() for meaning in meanings},
        "acceptanceThreshold": 0.72,
        "macroF1": 0.86,
        "perMeaningRecall": dict.fromkeys(meanings, 0.7),
        "evaluatedAt": "2026-11-07T07:00:00Z",
        "demoReady": True,
    }
    model_info.update(overrides)
    artifact_directory.mkdir(parents=True)
    (artifact_directory / MODEL_INFO_FILE).write_text(
        json.dumps(model_info), encoding="utf-8"
    )
    return artifact_directory


@pytest.fixture
def fixture_client() -> Iterator[TestClient]:
    with build_client(settings_for(FIXTURE_ARTIFACTS / "fixture")) as test_client:
        yield test_client


@pytest.fixture
def degraded_client() -> Iterator[TestClient]:
    with build_client(settings_for(None)) as test_client:
        yield test_client


def test_health_reports_ok_with_fixture_and_disables_cache(
    fixture_client: TestClient,
) -> None:
    caller_request_id = str(uuid.uuid4())

    health_response = fixture_client.get(
        HEALTH_PATH, headers={REQUEST_ID_HEADER: caller_request_id}
    )

    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "modelReady": True,
        "modelVersion": "vsl-fixture-v0.0.1",
    }
    assert health_response.headers["Cache-Control"] == "no-store"
    assert health_response.headers[REQUEST_ID_HEADER] == caller_request_id


def test_health_reports_degraded_without_artifact(degraded_client: TestClient) -> None:
    health_response = degraded_client.get(HEALTH_PATH)

    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "degraded",
        "modelReady": False,
        "modelVersion": None,
    }
    assert health_response.headers["Cache-Control"] == "no-store"


def test_model_info_exposes_fixture_metadata(fixture_client: TestClient) -> None:
    model_info = fixture_client.get(MODEL_INFO_PATH).json()

    assert set(model_info) == MODEL_INFO_FIELDS
    assert model_info["artifactKind"] == "fixture"
    assert model_info["meanings"] == ["CAM_ON", "SOT", "GIAY_TO"]
    assert model_info["featureSchemaVersion"] == "visign-xy-32-v0.3-draft"
    assert (
        model_info["extractorVersion"] == "tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3"
    )
    assert model_info["macroF1"] is None
    assert model_info["perMeaningRecall"] is None
    assert model_info["evaluatedAt"] is None
    assert model_info["demoReady"] is False


def test_model_info_without_artifact_is_model_not_ready(
    degraded_client: TestClient,
) -> None:
    not_ready_response = degraded_client.get(MODEL_INFO_PATH)

    assert not_ready_response.status_code == 503
    assert not_ready_response.json()["code"] == "MODEL_NOT_READY"
    assert not_ready_response.headers["Retry-After"] == "5"
    assert (
        not_ready_response.json()["requestId"]
        == not_ready_response.headers[REQUEST_ID_HEADER]
    )


def test_broken_artifact_degrades_without_fixture_fallback(tmp_path: Path) -> None:
    # Contract AI-BE: artifact loi khi khoi dong thi degraded, khong suy luan bang fixture thay the
    with build_client(settings_for(tmp_path / "missing-artifact")) as broken_client:
        assert broken_client.get(HEALTH_PATH).json()["status"] == "degraded"
        assert broken_client.get(MODEL_INFO_PATH).status_code == 503


def test_feature_schema_mismatch_degrades() -> None:
    mismatched_settings = settings_for(
        FIXTURE_ARTIFACTS / "fixture", feature_schema_version="visign-xy-32-v0.4"
    )

    with build_client(mismatched_settings) as mismatched_client:
        assert mismatched_client.get(HEALTH_PATH).json()["modelReady"] is False


def test_pilot_model_info_is_never_demo_ready(tmp_path: Path) -> None:
    pilot_directory = write_model_artifact(tmp_path / "pilot", "pilot")

    with build_client(settings_for(pilot_directory), STUB_FACTORIES) as pilot_client:
        model_info = pilot_client.get(MODEL_INFO_PATH).json()

    assert model_info["artifactKind"] == "pilot"
    assert model_info["meanings"] == P0_MEANINGS[:3]
    assert model_info["demoReady"] is False


def test_full_model_info_exposes_metrics_and_demo_gate(tmp_path: Path) -> None:
    full_directory = write_model_artifact(tmp_path / "full", "full")

    with build_client(settings_for(full_directory), STUB_FACTORIES) as full_client:
        model_info = full_client.get(MODEL_INFO_PATH).json()

    assert model_info["artifactKind"] == "full"
    assert model_info["meanings"] == P0_MEANINGS
    assert model_info["macroF1"] == pytest.approx(0.86)
    assert model_info["perMeaningRecall"] == dict.fromkeys(P0_MEANINGS, 0.7)
    assert datetime.fromisoformat(model_info["evaluatedAt"]).year == 2026
    assert model_info["demoReady"] is True


def test_full_model_failing_gate_is_not_demo_ready(tmp_path: Path) -> None:
    failing_directory = write_model_artifact(tmp_path / "full", "full", macroF1=0.79)

    with build_client(settings_for(failing_directory), STUB_FACTORIES) as full_client:
        assert full_client.get(MODEL_INFO_PATH).json()["demoReady"] is False
