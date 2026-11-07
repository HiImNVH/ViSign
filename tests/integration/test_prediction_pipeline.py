# tests/integration/test_prediction_pipeline.py
# T064: luong du doan that voi clip dai dien (parity offline/API, nap artifact, du doan qua HTTP, xoa clip tam) va
# doi artifact fixture -> pilot -> full bang khoi dong lai; artifact hong thi degraded, khoi dong lai voi duong dan
# cu la rollback (quickstart Scenario 3).
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from visign_api.config import Settings
from visign_api.inference.feature_extraction import (
    FeatureExtractor,
    FeatureSource,
    build_visign_ai_binding,
)
from visign_api.inference.temporary_clip import open_temporary_clip
from visign_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ARTIFACTS = (
    REPOSITORY_ROOT
    / "services"
    / "inference-api"
    / "tests"
    / "fixtures"
    / "model-artifacts"
)
# Cung bien moi truong voi test parity cua API va P3 de ba noi chay tren cung clip dai dien
REFERENCE_CLIP_VARIABLE = "VISIGN_CP2_REFERENCE_WEBM"
SERVING_EXTRA_REASON = (
    "Can extra serving: uv sync --project services/inference-api --extra serving"
)
SYNTHETIC_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm pipeline clip"
WEBM_MEDIA_TYPE = "video/webm;codecs=vp8"
PARITY_TOLERANCE = 1e-6
REQUIRED_PREDICTION_KEYS = {
    "requestId",
    "text",
    "classLabel",
    "confidence",
    "accepted",
    "modelVersion",
    "processingTimeMs",
}
OPTIONAL_PREDICTION_KEYS = {"timingsMs", "qualityHints"}


@dataclass(frozen=True)
class ServedSnapshot:
    health: dict[str, Any]
    modelInfoStatus: int
    modelInfo: dict[str, Any]
    prediction: httpx2.Response


def serve_once(artifact_directory: Path, clip_bytes: bytes) -> ServedSnapshot:
    # Moi lan goi la mot lan khoi dong API voi MODEL_ARTIFACT_PATH moi: doi va rollback deu bang restart
    artifact_settings = Settings(  # type: ignore[call-arg]
        _env_file=None, model_artifact_path=artifact_directory
    )
    with TestClient(create_app(artifact_settings)) as api_client:
        model_info_response = api_client.get("/api/v1/model-info")
        return ServedSnapshot(
            health=api_client.get("/api/v1/health").json(),
            modelInfoStatus=model_info_response.status_code,
            modelInfo=model_info_response.json(),
            prediction=api_client.post(
                "/api/v1/predictions",
                files={"clip": ("capture.webm", clip_bytes, WEBM_MEDIA_TYPE)},
            ),
        )


def assert_prediction_contract(snapshot: ServedSnapshot) -> None:
    prediction = snapshot.prediction.json()
    prediction_keys = set(prediction)
    assert REQUIRED_PREDICTION_KEYS <= prediction_keys
    assert prediction_keys <= REQUIRED_PREDICTION_KEYS | OPTIONAL_PREDICTION_KEYS
    assert prediction["modelVersion"] == snapshot.modelInfo["modelVersion"]


@pytest.fixture
def api_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Moi file API ghi (clip tam, spool multipart) nam trong thu muc rieng de kiem don dep
    api_temp_directory = tmp_path / "api-temp"
    api_temp_directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(api_temp_directory))
    return api_temp_directory


def test_fixture_swap_keeps_response_schema(api_temp: Path) -> None:
    fixture_snapshot = serve_once(FIXTURE_ARTIFACTS / "fixture", SYNTHETIC_CLIP)
    low_snapshot = serve_once(
        FIXTURE_ARTIFACTS / "fixture-low-confidence", SYNTHETIC_CLIP
    )

    for snapshot in (fixture_snapshot, low_snapshot):
        assert snapshot.health["status"] == "ok"
        assert snapshot.prediction.status_code == 200
        assert_prediction_contract(snapshot)
    assert (
        fixture_snapshot.modelInfo["modelVersion"]
        != low_snapshot.modelInfo["modelVersion"]
    )
    assert fixture_snapshot.prediction.json()["accepted"] is True
    assert low_snapshot.prediction.json()["accepted"] is False
    assert list(api_temp.iterdir()) == []


def test_broken_artifact_degrades_and_previous_path_rolls_back(
    api_temp: Path, tmp_path: Path
) -> None:
    broken_artifact = tmp_path / "broken-artifact"
    broken_artifact.mkdir()
    (broken_artifact / "model_info.json").write_text(
        "{khong-phai-json", encoding="utf-8"
    )

    degraded = serve_once(broken_artifact, SYNTHETIC_CLIP)
    restored = serve_once(FIXTURE_ARTIFACTS / "fixture", SYNTHETIC_CLIP)

    # Khong lui ve fixture: artifact hong -> degraded, model-info va du doan 503 MODEL_NOT_READY
    assert degraded.health == {
        "status": "degraded",
        "modelReady": False,
        "modelVersion": None,
    }
    assert degraded.modelInfoStatus == 503
    assert degraded.prediction.status_code == 503
    assert degraded.prediction.json()["code"] == "MODEL_NOT_READY"
    # Rollback: khoi dong lai voi duong dan artifact truoc do
    assert restored.health["status"] == "ok"
    assert restored.prediction.status_code == 200
    assert list(api_temp.iterdir()) == []


@pytest.fixture(scope="module")
def trained_artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    pytest.importorskip("torch", reason=SERVING_EXTRA_REASON)
    pytest.importorskip("visign_ai.training.train", reason=SERVING_EXTRA_REASON)
    from t036_artifact_builder import FULL_SPEC, PILOT_SPEC, train_artifact

    return {
        "pilot": train_artifact(tmp_path_factory.mktemp("t064-pilot"), PILOT_SPEC),
        "full": train_artifact(tmp_path_factory.mktemp("t064-full"), FULL_SPEC),
    }


@pytest.fixture
def reference_clip() -> Path:
    configured_path = os.environ.get(REFERENCE_CLIP_VARIABLE, "")
    if not configured_path:
        pytest.skip(f"Dat {REFERENCE_CLIP_VARIABLE} toi clip WebM dai dien co nguoi")
    return Path(configured_path)


def test_reference_clip_features_match_offline_extraction(
    reference_clip: Path, api_temp: Path
) -> None:
    pipeline_module = pytest.importorskip(
        "visign_ai.landmarks.pipeline", reason=SERVING_EXTRA_REASON
    )

    offline_result = pipeline_module.process_video(reference_clip)
    with open_temporary_clip(reference_clip.read_bytes()) as uploaded_clip:
        served_features = FeatureExtractor(
            build_visign_ai_binding(), FeatureSource()
        ).extract(uploaded_clip.path)

    np.testing.assert_allclose(
        served_features.tensor, offline_result["tensor"], rtol=0, atol=PARITY_TOLERANCE
    )
    np.testing.assert_array_equal(
        served_features.tensorMask, offline_result["tensor_mask"]
    )
    np.testing.assert_array_equal(served_features.groupMask, offline_result["masks"])
    assert served_features.inputStatus == offline_result["report"]["inputStatus"]
    assert list(api_temp.iterdir()) == []


def test_reference_clip_flows_through_fixture_pilot_and_full(
    reference_clip: Path, trained_artifacts: dict[str, Path], api_temp: Path
) -> None:
    clip_bytes = reference_clip.read_bytes()
    swap_sequence = [
        ("fixture", FIXTURE_ARTIFACTS / "fixture"),
        ("pilot", trained_artifacts["pilot"]),
        ("full", trained_artifacts["full"]),
        ("fixture", FIXTURE_ARTIFACTS / "fixture"),
    ]

    for expected_kind, artifact_directory in swap_sequence:
        snapshot = serve_once(artifact_directory, clip_bytes)
        assert snapshot.health["status"] == "ok"
        assert snapshot.modelInfo["artifactKind"] == expected_kind
        assert snapshot.modelInfo["demoReady"] is False
        assert snapshot.prediction.status_code == 200, snapshot.prediction.text
        assert_prediction_contract(snapshot)
    assert list(api_temp.iterdir()) == []
