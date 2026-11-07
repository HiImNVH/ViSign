# services/inference-api/tests/contract/test_predictions_contract.py
# Contract test T030/T038: POST /api/v1/predictions voi fixture va predictor kich ban cho moi trang thai response.
import threading
import uuid
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from visign_api.config import Settings
from visign_api.domain.errors import ClipDecodeFailedException
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.domain.prediction import (
    REJECTED_PREDICTION_TEXT,
    PredictionQualityHints,
    PredictionTimings,
)
from visign_api.inference.artifact_loader import LoadedArtifact
from visign_api.inference.predictor import RawPrediction
from visign_api.inference.predictor_registry import PredictorFactory
from visign_api.main import create_app

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
PREDICTIONS_PATH = "/api/v1/predictions"
REQUEST_ID_HEADER = "X-Request-ID"
SAMPLE_CLIP = b"\x1aE\xdf\xa3 fixture camera clip"
WEBM_MEDIA_TYPE = "video/webm;codecs=vp8"
INTERNAL_SECRET = "C:\\noi-bo\\visign_clip_bi-mat.webm"
REQUIRED_RESPONSE_FIELDS = {
    "requestId",
    "text",
    "classLabel",
    "confidence",
    "accepted",
    "modelVersion",
    "processingTimeMs",
}
DIAGNOSTIC_FIELDS = {"timingsMs", "qualityHints"}
SCRIPTED_ACCEPTED = RawPrediction(
    classLabel="SOT_HCM_1",
    displayText="Sốt",
    confidence=0.91,
    timingsMs=PredictionTimings(decode=10, extract=900, infer=5),
    qualityHints=PredictionQualityHints(handsDetectedRatio=0.5, frameCount=46),
)

ScriptedBehavior = Callable[[Path], RawPrediction]


class ScriptedPredictor:
    def __init__(
        self, loaded_artifact: LoadedArtifact, scripted_behavior: ScriptedBehavior
    ) -> None:
        self._loaded_artifact = loaded_artifact
        self._scripted_behavior = scripted_behavior

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        return self._scripted_behavior(clip_path)


def factories_with(
    scripted_behavior: ScriptedBehavior,
) -> Mapping[ArtifactKind, PredictorFactory]:
    def build_scripted(loaded_artifact: LoadedArtifact) -> ScriptedPredictor:
        return ScriptedPredictor(loaded_artifact, scripted_behavior)

    return {kind: build_scripted for kind in ArtifactKind}


def settings_for(artifact_path: Path | None, **overrides: Any) -> Settings:
    return Settings(_env_file=None, model_artifact_path=artifact_path, **overrides)  # type: ignore[call-arg]


def build_client(
    runtime_settings: Settings,
    predictor_factories: Mapping[ArtifactKind, PredictorFactory] | None = None,
) -> TestClient:
    return TestClient(
        create_app(runtime_settings, predictor_factories), raise_server_exceptions=False
    )


def post_clip(
    test_client: TestClient, headers: dict[str, str] | None = None
) -> httpx2.Response:
    return test_client.post(
        PREDICTIONS_PATH,
        files={"clip": ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)},
        headers=headers or {},
    )


@pytest.fixture
def fixture_client() -> Iterator[TestClient]:
    with build_client(settings_for(FIXTURE_ARTIFACTS / "fixture")) as test_client:
        yield test_client


def test_fixture_returns_accepted_contract_response(fixture_client: TestClient) -> None:
    caller_request_id = str(uuid.uuid4())

    prediction_response = post_clip(
        fixture_client, {REQUEST_ID_HEADER: caller_request_id}
    )

    prediction = prediction_response.json()
    assert prediction_response.status_code == 200
    assert set(prediction) == REQUIRED_RESPONSE_FIELDS | DIAGNOSTIC_FIELDS
    assert prediction["accepted"] is True
    assert prediction["classLabel"] == "CAM_ON_HN_1"
    assert prediction["text"] == "Cảm ơn"
    assert prediction["confidence"] == pytest.approx(0.95)
    assert prediction["modelVersion"] == "vsl-fixture-v0.0.1"
    assert prediction["processingTimeMs"] >= 0
    assert prediction["requestId"] == caller_request_id
    assert prediction_response.headers[REQUEST_ID_HEADER] == caller_request_id


def test_diagnostics_are_non_negative_and_bounded(fixture_client: TestClient) -> None:
    prediction = post_clip(fixture_client).json()

    assert all(stage_ms >= 0 for stage_ms in prediction["timingsMs"].values())
    assert 0.0 <= prediction["qualityHints"]["handsDetectedRatio"] <= 1.0
    assert prediction["qualityHints"]["frameCount"] >= 1


def test_missing_request_id_is_generated_and_echoed(fixture_client: TestClient) -> None:
    prediction_response = post_clip(fixture_client)

    generated_request_id = prediction_response.headers[REQUEST_ID_HEADER]
    assert str(uuid.UUID(generated_request_id)) == generated_request_id
    assert prediction_response.json()["requestId"] == generated_request_id


def test_low_confidence_is_rejected_with_http_200() -> None:
    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture-low-confidence")
    ) as low_client:
        prediction_response = post_clip(low_client)

    prediction = prediction_response.json()
    assert prediction_response.status_code == 200
    assert prediction["accepted"] is False
    assert prediction["classLabel"] is None
    assert prediction["text"] == REJECTED_PREDICTION_TEXT
    assert prediction["confidence"] == pytest.approx(0.42)


def test_every_artifact_kind_shares_the_response_schema(tmp_path: Path) -> None:
    # T030: fixture/pilot/full dung cung response; doi artifact khong doi shape cho frontend
    scripted_factories = factories_with(lambda clip_path: SCRIPTED_ACCEPTED)

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), scripted_factories
    ) as scripted_client:
        scripted_prediction = post_clip(scripted_client).json()

    assert set(scripted_prediction) == REQUIRED_RESPONSE_FIELDS | DIAGNOSTIC_FIELDS
    assert scripted_prediction["text"] == "Sốt"


def test_absent_diagnostics_are_omitted() -> None:
    bare_prediction = RawPrediction(
        classLabel="CAM_ON_HN_1",
        displayText="Cảm ơn",
        confidence=0.9,
        timingsMs=None,
        qualityHints=None,
    )
    bare_factories = factories_with(lambda clip_path: bare_prediction)

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), bare_factories
    ) as bare_client:
        prediction = post_clip(bare_client).json()

    assert set(prediction) == REQUIRED_RESPONSE_FIELDS


@pytest.mark.parametrize(
    "request_options",
    [
        {"files": {"other": ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)}},
        {"files": {"clip": ("capture.webm", b"", WEBM_MEDIA_TYPE)}},
        {"data": {"clip": "khong-phai-file"}},
    ],
)
def test_missing_or_empty_clip_is_invalid_request(
    fixture_client: TestClient, request_options: dict[str, Any]
) -> None:
    invalid_response = fixture_client.post(PREDICTIONS_PATH, **request_options)

    assert invalid_response.status_code == 400
    assert invalid_response.json()["code"] == "INVALID_REQUEST"
    assert "detail" not in invalid_response.json()


def test_oversized_clip_is_rejected_before_inference() -> None:
    inference_calls: list[Path] = []

    def record_call(clip_path: Path) -> RawPrediction:
        inference_calls.append(clip_path)
        return SCRIPTED_ACCEPTED

    small_limit_settings = settings_for(FIXTURE_ARTIFACTS / "fixture", max_clip_bytes=8)
    with build_client(
        small_limit_settings, factories_with(record_call)
    ) as limited_client:
        oversized_response = post_clip(limited_client)

    assert oversized_response.status_code == 413
    assert oversized_response.json()["code"] == "CLIP_TOO_LARGE"
    assert inference_calls == []


def test_missing_model_is_model_not_ready() -> None:
    with build_client(settings_for(None)) as degraded_client:
        not_ready_response = post_clip(degraded_client)

    assert not_ready_response.status_code == 503
    assert not_ready_response.json()["code"] == "MODEL_NOT_READY"
    assert not_ready_response.headers["Retry-After"] == "5"


def test_temporary_clip_exists_during_inference_and_is_deleted_after() -> None:
    seen_clips: list[tuple[Path, bool, bytes]] = []

    def inspect_clip(clip_path: Path) -> RawPrediction:
        seen_clips.append((clip_path, clip_path.exists(), clip_path.read_bytes()))
        return SCRIPTED_ACCEPTED

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), factories_with(inspect_clip)
    ) as inspecting_client:
        assert post_clip(inspecting_client).status_code == 200

    clip_path, existed_during_inference, clip_bytes = seen_clips[0]
    assert existed_during_inference is True
    assert clip_bytes == SAMPLE_CLIP
    assert not clip_path.exists()


def test_domain_error_from_predictor_keeps_its_status_and_cleans_up() -> None:
    seen_paths: list[Path] = []

    def fail_decoding(clip_path: Path) -> RawPrediction:
        seen_paths.append(clip_path)
        raise ClipDecodeFailedException()

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), factories_with(fail_decoding)
    ) as failing_client:
        decode_response = post_clip(failing_client)

    assert decode_response.status_code == 422
    assert decode_response.json()["code"] == "CLIP_DECODE_FAILED"
    assert not seen_paths[0].exists()


def test_unexpected_predictor_failure_is_prediction_failed_without_leaks() -> None:
    seen_paths: list[Path] = []

    def crash(clip_path: Path) -> RawPrediction:
        seen_paths.append(clip_path)
        raise RuntimeError(f"khong doc duoc {INTERNAL_SECRET}")

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), factories_with(crash)
    ) as crashing_client:
        crash_response = post_clip(crashing_client)

    assert crash_response.status_code == 500
    assert crash_response.json()["code"] == "PREDICTION_FAILED"
    for leaked_fragment in (INTERNAL_SECRET, "Traceback", "RuntimeError"):
        assert leaked_fragment not in crash_response.text
    assert not seen_paths[0].exists()


def test_concurrent_request_gets_service_busy_with_retry_after() -> None:
    inference_started = threading.Event()
    release_inference = threading.Event()

    def block_until_released(clip_path: Path) -> RawPrediction:
        inference_started.set()
        release_inference.wait(timeout=10)
        return SCRIPTED_ACCEPTED

    busy_settings = settings_for(
        FIXTURE_ARTIFACTS / "fixture", inference_wait_timeout_seconds=0.2
    )
    first_responses: list[httpx2.Response] = []
    with build_client(
        busy_settings, factories_with(block_until_released)
    ) as busy_client:
        first_request = threading.Thread(
            target=lambda: first_responses.append(post_clip(busy_client))
        )
        first_request.start()
        assert inference_started.wait(timeout=10)
        busy_response = post_clip(busy_client)
        release_inference.set()
        first_request.join(timeout=10)

    assert busy_response.status_code == 503
    assert busy_response.json()["code"] == "SERVICE_BUSY"
    assert busy_response.headers["Retry-After"] == "3"
    assert first_responses[0].status_code == 200
