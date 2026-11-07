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
from starlette.formparsers import MultiPartParser
from visign_api.config import Settings
from visign_api.domain.errors import (
    ERROR_CATALOG,
    ClipDecodeFailedException,
    ErrorCode,
    build_api_exception,
)
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
# Header EBML + DocType "webm" nhu clip MediaRecorder; phan con lai la du lieu gia
SAMPLE_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm fixture camera clip"
MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + bytes(64)
TEN_GIB = str(10 * 1024**3)
MULTIPART_BOUNDARY = "visign-test-boundary"
ALLOWED_ORIGIN = "http://localhost:5173"
RETRY_AFTER_HEADER = "Retry-After"
MP4_MEDIA_TYPE = "video/mp4"
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


def call_recorder(inference_calls: list[Path]) -> ScriptedBehavior:
    def record_call(clip_path: Path) -> RawPrediction:
        inference_calls.append(clip_path)
        return SCRIPTED_ACCEPTED

    return record_call


def multipart_clip_body(clip_bytes: bytes) -> bytes:
    part_header = (
        f"--{MULTIPART_BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="clip"; filename="capture.webm"\r\n'
        f"Content-Type: {WEBM_MEDIA_TYPE}\r\n\r\n"
    )
    closing = f"\r\n--{MULTIPART_BOUNDARY}--\r\n"
    return part_header.encode() + clip_bytes + closing.encode()


@pytest.mark.parametrize(
    "media_type",
    ["video/mp4", "application/octet-stream", "video/x-matroska;codecs=avc1"],
)
def test_unsupported_media_type_is_rejected_before_inference(media_type: str) -> None:
    inference_calls: list[Path] = []

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"),
        factories_with(call_recorder(inference_calls)),
    ) as recording_client:
        unsupported_response = recording_client.post(
            PREDICTIONS_PATH,
            files={"clip": ("capture.webm", SAMPLE_CLIP, media_type)},
        )

    assert unsupported_response.status_code == 415
    assert unsupported_response.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert inference_calls == []


def test_webm_label_on_foreign_bytes_is_unsupported() -> None:
    inference_calls: list[Path] = []

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"),
        factories_with(call_recorder(inference_calls)),
    ) as recording_client:
        foreign_response = recording_client.post(
            PREDICTIONS_PATH,
            files={"clip": ("capture.webm", MP4_BYTES, WEBM_MEDIA_TYPE)},
        )

    assert foreign_response.status_code == 415
    assert foreign_response.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert inference_calls == []


def test_declared_oversized_body_is_rejected_before_multipart_parsing(
    fixture_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    parsed_bodies: list[MultiPartParser] = []
    original_parse = MultiPartParser.parse

    async def recording_parse(parser: MultiPartParser) -> Any:
        parsed_bodies.append(parser)
        return await original_parse(parser)

    monkeypatch.setattr(MultiPartParser, "parse", recording_parse)

    assert post_clip(fixture_client).status_code == 200
    oversized_response = post_clip(fixture_client, {"Content-Length": TEN_GIB})

    assert oversized_response.status_code == 413
    assert oversized_response.json()["code"] == "CLIP_TOO_LARGE"
    # Chi request hop le dau tien duoc parse; request khai 10 GiB bi chan tu header
    assert len(parsed_bodies) == 1


def test_chunked_body_over_limit_is_rejected_while_streaming(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parse_outcomes: list[str] = []
    original_parse = MultiPartParser.parse

    async def recording_parse(parser: MultiPartParser) -> Any:
        try:
            parsed_form = await original_parse(parser)
        except BaseException:
            parse_outcomes.append("aborted")
            raise
        parse_outcomes.append("completed")
        return parsed_form

    monkeypatch.setattr(MultiPartParser, "parse", recording_parse)
    inference_calls: list[Path] = []
    oversized_body = multipart_clip_body(SAMPLE_CLIP + bytes(100_000))

    def body_chunks() -> Iterator[bytes]:
        yield oversized_body

    small_limit_settings = settings_for(
        FIXTURE_ARTIFACTS / "fixture", max_clip_bytes=1024
    )
    with build_client(
        small_limit_settings, factories_with(call_recorder(inference_calls))
    ) as limited_client:
        chunked_response = limited_client.post(
            PREDICTIONS_PATH,
            content=body_chunks(),
            headers={
                "Content-Type": f"multipart/form-data; boundary={MULTIPART_BOUNDARY}"
            },
        )

    assert "content-length" not in chunked_response.request.headers
    assert chunked_response.status_code == 413
    assert chunked_response.json()["code"] == "CLIP_TOO_LARGE"
    # Bo dem byte cat stream giua chung: multipart khong duoc parse het roi moi bi tu choi
    assert parse_outcomes == ["aborted"]
    assert inference_calls == []


@pytest.mark.parametrize("error_code", list(ErrorCode))
def test_every_error_code_returns_its_catalog_envelope(error_code: ErrorCode) -> None:
    # T045: moi ma loi cung mot envelope; Retry-After chi co khi catalog khai bao; clip tam luon bi xoa
    seen_paths: list[Path] = []

    def raise_error_code(clip_path: Path) -> RawPrediction:
        seen_paths.append(clip_path)
        raise build_api_exception(error_code)

    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), factories_with(raise_error_code)
    ) as failing_client:
        error_response = post_clip(failing_client)

    error_definition = ERROR_CATALOG[error_code]
    expected_retry_after = (
        None
        if error_definition.retryAfterSeconds is None
        else str(error_definition.retryAfterSeconds)
    )
    assert error_response.status_code == error_definition.statusCode
    assert error_response.headers["content-type"].startswith("application/json")
    assert error_response.json() == {
        "code": error_code.value,
        "message": error_definition.message,
        "requestId": error_response.headers[REQUEST_ID_HEADER],
    }
    assert error_response.headers.get(RETRY_AFTER_HEADER) == expected_retry_after
    assert not seen_paths[0].exists()


def truncated_multipart_body() -> bytes:
    return multipart_clip_body(SAMPLE_CLIP).split(
        b"\r\n--" + MULTIPART_BOUNDARY.encode()
    )[0]


@pytest.mark.parametrize(
    ("content_type", "raw_body"),
    [
        ("multipart/form-data", b"--x\r\nkhong co boundary"),
        (
            f"multipart/form-data; boundary={MULTIPART_BOUNDARY}",
            truncated_multipart_body(),
        ),
    ],
)
def test_malformed_multipart_is_invalid_request_envelope(
    fixture_client: TestClient, content_type: str, raw_body: bytes
) -> None:
    # T050: loi parse body tra ErrorEnvelope, khong lo {"detail": ...} cua FastAPI
    malformed_response = fixture_client.post(
        PREDICTIONS_PATH, content=raw_body, headers={"Content-Type": content_type}
    )

    assert malformed_response.status_code == 400
    assert malformed_response.json() == {
        "code": ErrorCode.INVALID_REQUEST.value,
        "message": ERROR_CATALOG[ErrorCode.INVALID_REQUEST].message,
        "requestId": malformed_response.headers[REQUEST_ID_HEADER],
    }


def fixture_post(**request_options: Any) -> httpx2.Response:
    with build_client(settings_for(FIXTURE_ARTIFACTS / "fixture")) as test_client:
        return test_client.post(PREDICTIONS_PATH, **request_options)


def scripted_post(scripted_behavior: ScriptedBehavior) -> httpx2.Response:
    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture"), factories_with(scripted_behavior)
    ) as scripted_client:
        return post_clip(scripted_client)


def crash(clip_path: Path) -> RawPrediction:
    raise RuntimeError("loi bat ngo")


def fail_decoding(clip_path: Path) -> RawPrediction:
    raise ClipDecodeFailedException()


def low_confidence_post() -> httpx2.Response:
    with build_client(
        settings_for(FIXTURE_ARTIFACTS / "fixture-low-confidence")
    ) as low_client:
        return post_clip(low_client)


def not_ready_post() -> httpx2.Response:
    with build_client(settings_for(None)) as degraded_client:
        return post_clip(degraded_client)


RESPONSE_SCENARIOS = {
    "200-accepted": lambda: fixture_post(
        files={"clip": ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)}
    ),
    "200-rejected": low_confidence_post,
    "400-missing-clip": lambda: fixture_post(data={"other": "khong-co-clip"}),
    "400-malformed-body": lambda: fixture_post(
        content=b"--x", headers={"Content-Type": "multipart/form-data"}
    ),
    "413-declared-length": lambda: fixture_post(
        files={"clip": ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)},
        headers={"Content-Length": TEN_GIB},
    ),
    "415-media-type": lambda: fixture_post(
        files={"clip": ("capture.mp4", SAMPLE_CLIP, MP4_MEDIA_TYPE)}
    ),
    "422-decode-failed": lambda: scripted_post(fail_decoding),
    "500-prediction-failed": lambda: scripted_post(crash),
    "503-model-not-ready": not_ready_post,
}


@pytest.mark.parametrize("scenario_name", sorted(RESPONSE_SCENARIOS))
def test_every_response_carries_its_request_id(scenario_name: str) -> None:
    scenario_response = RESPONSE_SCENARIOS[scenario_name]()

    effective_request_id = scenario_response.headers[REQUEST_ID_HEADER]
    assert str(scenario_response.status_code) == scenario_name.split("-")[0]
    assert str(uuid.UUID(effective_request_id)) == effective_request_id
    assert scenario_response.json()["requestId"] == effective_request_id


def test_caller_request_id_is_echoed_on_errors_and_invalid_ids_are_replaced(
    fixture_client: TestClient,
) -> None:
    caller_request_id = str(uuid.uuid4())
    unsupported_clip = {"clip": ("capture.mp4", SAMPLE_CLIP, MP4_MEDIA_TYPE)}

    echoed_response = fixture_client.post(
        PREDICTIONS_PATH,
        files=unsupported_clip,
        headers={REQUEST_ID_HEADER: caller_request_id},
    )
    replaced_response = fixture_client.post(
        PREDICTIONS_PATH,
        files=unsupported_clip,
        headers={REQUEST_ID_HEADER: "khong-phai-uuid"},
    )

    assert echoed_response.headers[REQUEST_ID_HEADER] == caller_request_id
    assert echoed_response.json()["requestId"] == caller_request_id
    replaced_request_id = replaced_response.headers[REQUEST_ID_HEADER]
    assert str(uuid.UUID(replaced_request_id)) == replaced_request_id
    assert replaced_response.json()["requestId"] == replaced_request_id


@pytest.mark.parametrize("scenario_name", ["415-media-type", "503-model-not-ready"])
def test_error_responses_expose_correlation_headers_to_web_origin(
    scenario_name: str,
) -> None:
    # Trinh duyet chi doc duoc X-Request-ID/Retry-After cua response loi khi CORS cho phep
    def with_origin(request_options: dict[str, Any]) -> httpx2.Response:
        return fixture_post(headers={"Origin": ALLOWED_ORIGIN}, **request_options)

    if scenario_name == "415-media-type":
        error_response = with_origin(
            {"files": {"clip": ("capture.mp4", SAMPLE_CLIP, MP4_MEDIA_TYPE)}}
        )
    else:
        with build_client(settings_for(None)) as degraded_client:
            error_response = post_clip(degraded_client, {"Origin": ALLOWED_ORIGIN})

    exposed_headers = {
        header_name.strip().lower()
        for header_name in error_response.headers[
            "access-control-expose-headers"
        ].split(",")
    }
    assert error_response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert {"x-request-id", "retry-after"} <= exposed_headers
