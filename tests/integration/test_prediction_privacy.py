# tests/integration/test_prediction_privacy.py
# Audit quyen rieng tu T066: sau loat request thanh cong/loi, log khong chua noi dung clip, ten file, token, chu dich
# hay nhan lop; API khong de lai file nao tren dia va don clip con sot khi khoi dong (FR-011, FR-019).
import io
import json
import logging
import os
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from visign_api.config import Settings
from visign_api.domain.errors import ClipDecodeFailedException
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.inference.artifact_loader import LoadedArtifact
from visign_api.inference.predictor import RawPrediction
from visign_api.inference.predictor_registry import PredictorFactory
from visign_api.inference.temporary_clip import (
    CLIP_FILE_PREFIX,
    CLIP_FILE_SUFFIX,
    STALE_CLIP_AGE_SECONDS,
)
from visign_api.main import create_app
from visign_api.observability import (
    ALLOWED_CONTEXT_KEYS,
    LOGGER_NAME,
    StructuredJsonFormatter,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ARTIFACTS = (
    REPOSITORY_ROOT
    / "services"
    / "inference-api"
    / "tests"
    / "fixtures"
    / "model-artifacts"
)
PREDICTIONS_PATH = "/api/v1/predictions"
WEBM_MEDIA_TYPE = "video/webm;codecs=vp8"
# Noi dung danh dau trong clip va du lieu ca nhan gia lap: khong duoc xuat hien trong log hay response
PRIVATE_MARKER = "PRIVATE-CLIP-CONTENT-7f3a"
CLIP_BYTES = (
    b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm" + PRIVATE_MARKER.encode()
)
UPLOAD_FILENAME = "nguyen-van-an-0912345678.webm"
AUTH_HEADER_VALUE = "Bearer token-bi-mat-khong-duoc-log"
COOKIE_HEADER_VALUE = "session=cookie-bi-mat"
RECOGNIZED_CONTENT = ("Cảm ơn", "Sốt", "CAM_ON_HN_1", "SOT_HCM_1")
BASE_LOG_KEYS = {"timestamp", "level", "logger", "message", "exception"}
PREDICTION_KEYS = {
    "requestId",
    "text",
    "classLabel",
    "confidence",
    "accepted",
    "modelVersion",
    "processingTimeMs",
    "timingsMs",
    "qualityHints",
}


@dataclass(frozen=True)
class PrivacyRun:
    logText: str
    responses: dict[str, httpx2.Response]
    leftoverFiles: list[str]
    staleClipRemoved: bool
    recentClipKept: bool


class FailingPredictor:
    def __init__(self, loaded_artifact: LoadedArtifact, failure: Exception) -> None:
        self._loaded_artifact = loaded_artifact
        self._failure = failure

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        raise self._failure


def failing_factories(failure: Exception) -> Mapping[ArtifactKind, PredictorFactory]:
    def build_failing(loaded_artifact: LoadedArtifact) -> FailingPredictor:
        return FailingPredictor(loaded_artifact, failure)

    return {ArtifactKind.FIXTURE: build_failing}


def settings_for(artifact_name: str, **overrides: Any) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        model_artifact_path=FIXTURE_ARTIFACTS / artifact_name,
        **overrides,
    )


def sensitive_request(test_client: TestClient, media_type: str) -> httpx2.Response:
    return test_client.post(
        PREDICTIONS_PATH,
        files={"clip": (UPLOAD_FILENAME, CLIP_BYTES, media_type)},
        headers={"Authorization": AUTH_HEADER_VALUE, "Cookie": COOKIE_HEADER_VALUE},
    )


def run_fixture_requests() -> dict[str, httpx2.Response]:
    with TestClient(create_app(settings_for("fixture"))) as fixture_client:
        fixture_responses = {
            "accepted": sensitive_request(fixture_client, WEBM_MEDIA_TYPE),
            "unsupported": sensitive_request(fixture_client, "video/mp4"),
            "malformed": fixture_client.post(
                PREDICTIONS_PATH,
                content=b"--x",
                headers={"Content-Type": "multipart/form-data"},
            ),
            "not-found": fixture_client.get(
                "/api/v1/khong-ton-tai", headers={"Authorization": AUTH_HEADER_VALUE}
            ),
            "method": fixture_client.post("/api/v1/health"),
            "model-info": fixture_client.get("/api/v1/model-info"),
        }
    with TestClient(create_app(settings_for("fixture-low-confidence"))) as low_client:
        fixture_responses["rejected"] = sensitive_request(low_client, WEBM_MEDIA_TYPE)
    with TestClient(
        create_app(settings_for("fixture", max_clip_bytes=8))
    ) as small_client:
        fixture_responses["too-large"] = sensitive_request(
            small_client, WEBM_MEDIA_TYPE
        )
    return fixture_responses


def run_failure_requests() -> dict[str, httpx2.Response]:
    failures: dict[str, Exception] = {
        "decode-failed": ClipDecodeFailedException(),
        "crashed": RuntimeError("loi bat ngo trong predictor"),
    }
    failure_responses = {}
    for scenario_name, failure in failures.items():
        failing_app = create_app(settings_for("fixture"), failing_factories(failure))
        with TestClient(failing_app, raise_server_exceptions=False) as failing_client:
            failure_responses[scenario_name] = sensitive_request(
                failing_client, WEBM_MEDIA_TYPE
            )
    return failure_responses


@contextmanager
def captured_service_logs() -> Iterator[io.StringIO]:
    # Ghi log that cua service bang chinh formatter JSON dang chay production
    log_buffer = io.StringIO()
    capture_handler = logging.StreamHandler(log_buffer)
    capture_handler.setFormatter(StructuredJsonFormatter())
    service_logger = logging.getLogger(LOGGER_NAME)
    service_logger.addHandler(capture_handler)
    try:
        yield log_buffer
    finally:
        service_logger.removeHandler(capture_handler)


def leftover_clip(directory: Path, age_seconds: float) -> Path:
    clip_path = (
        directory / f"{CLIP_FILE_PREFIX}audit{age_seconds:.0f}{CLIP_FILE_SUFFIX}"
    )
    clip_path.write_bytes(CLIP_BYTES)
    backdated = time.time() - age_seconds
    os.utime(clip_path, (backdated, backdated))
    return clip_path


@pytest.fixture(scope="module")
def privacy_run(tmp_path_factory: pytest.TempPathFactory) -> PrivacyRun:
    # Thu muc tam rieng: moi file API ghi (clip tam, spool multipart) deu nam trong day de kiem dem
    api_temp = tmp_path_factory.mktemp("api-temp")
    stale_clip = leftover_clip(api_temp, STALE_CLIP_AGE_SECONDS + 60)
    recent_clip = leftover_clip(api_temp, 5)
    with pytest.MonkeyPatch.context() as patcher, captured_service_logs() as log_buffer:
        patcher.setattr(tempfile, "tempdir", str(api_temp))
        responses = {**run_fixture_requests(), **run_failure_requests()}
    recent_clip_kept = recent_clip.exists()
    recent_clip.unlink(missing_ok=True)
    return PrivacyRun(
        logText=log_buffer.getvalue(),
        responses=responses,
        leftoverFiles=sorted(entry.name for entry in api_temp.iterdir()),
        staleClipRemoved=not stale_clip.exists(),
        recentClipKept=recent_clip_kept,
    )


def text_forms(sensitive_text: str) -> set[str]:
    # Log JSON dung ensure_ascii nen chu co dau co the xuat hien o dang \\uXXXX
    return {sensitive_text, json.dumps(sensitive_text, ensure_ascii=True)[1:-1]}


def test_audit_covers_every_response_outcome(privacy_run: PrivacyRun) -> None:
    observed_statuses = {
        scenario_name: scenario_response.status_code
        for scenario_name, scenario_response in privacy_run.responses.items()
    }

    assert observed_statuses == {
        "accepted": 200,
        "rejected": 200,
        "model-info": 200,
        "malformed": 400,
        "not-found": 404,
        "method": 405,
        "too-large": 413,
        "unsupported": 415,
        "decode-failed": 422,
        "crashed": 500,
    }


def test_logs_use_only_allowlisted_fields(privacy_run: PrivacyRun) -> None:
    log_lines = [
        json.loads(raw_line)
        for raw_line in privacy_run.logText.splitlines()
        if raw_line.strip()
    ]

    assert len(log_lines) >= len(privacy_run.responses)
    for log_line in log_lines:
        assert set(log_line) <= BASE_LOG_KEYS | set(ALLOWED_CONTEXT_KEYS)


@pytest.mark.parametrize(
    "private_text",
    [
        PRIVATE_MARKER,
        UPLOAD_FILENAME,
        "nguyen-van-an",
        "0912345678",
        "token-bi-mat",
        "cookie-bi-mat",
        CLIP_FILE_PREFIX,
        *RECOGNIZED_CONTENT,
    ],
)
def test_logs_never_contain_private_content(
    privacy_run: PrivacyRun, private_text: str
) -> None:
    for text_form in text_forms(private_text):
        assert text_form not in privacy_run.logText


def test_api_leaves_no_file_on_disk(privacy_run: PrivacyRun) -> None:
    # Clip tam va file spool multipart deu da bi xoa sau moi request, ke ca khi loi
    assert privacy_run.leftoverFiles == []


def test_clip_left_by_killed_process_is_swept_at_startup(
    privacy_run: PrivacyRun,
) -> None:
    assert privacy_run.staleClipRemoved is True
    # Clip moi co the thuoc request dang chay cua tien trinh khac nen phai giu nguyen
    assert privacy_run.recentClipKept is True


def test_responses_carry_no_clip_landmark_or_personal_data(
    privacy_run: PrivacyRun,
) -> None:
    prediction = privacy_run.responses["accepted"].json()

    assert set(prediction) == PREDICTION_KEYS
    numeric_values: list[Callable[[], Any]] = [
        prediction["timingsMs"].values,
        prediction["qualityHints"].values,
    ]
    for diagnostic_values in numeric_values:
        assert all(isinstance(value, int | float) for value in diagnostic_values())
    for scenario_response in privacy_run.responses.values():
        assert PRIVATE_MARKER not in scenario_response.text
        assert UPLOAD_FILENAME not in scenario_response.text


def test_model_info_does_not_expose_artifact_location(privacy_run: PrivacyRun) -> None:
    model_info_text = privacy_run.responses["model-info"].text

    assert "model-artifacts" not in model_info_text
    assert "fixtures" not in model_info_text
