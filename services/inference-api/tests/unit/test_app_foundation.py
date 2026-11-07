# services/inference-api/tests/unit/test_app_foundation.py
# Kiem tra nen FastAPI T026: release 0.0.1, router /api/v1, X-Request-ID, CORS va anh xa exception.
import logging
import uuid
from collections.abc import Callable, Iterator
from importlib.metadata import version

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from visign_api.api.router import API_V1_PREFIX, api_v1_router
from visign_api.config import Settings
from visign_api.domain.errors import (
    ERROR_CATALOG,
    ClipDecodeFailedException,
    ErrorCode,
    ModelNotReadyException,
    ServiceBusyException,
    ViSignApiException,
)
from visign_api.main import create_app
from visign_api.observability import LOGGER_NAME

REQUEST_ID_HEADER = "X-Request-ID"
VITE_ORIGIN = "http://127.0.0.1:5173"
INTERNAL_SECRET = "C:\\noi-bo\\duong-dan\\bi-mat.py"
PROBE_PATH = f"{API_V1_PREFIX}/test-probe"


def raise_domain_error(error_code: str) -> None:
    domain_errors: dict[str, Callable[[], ViSignApiException]] = {
        "decode": ClipDecodeFailedException,
        "busy": ServiceBusyException,
        "not-ready": ModelNotReadyException,
    }
    raise domain_errors[error_code]()


def build_probe_app() -> FastAPI:
    # Route chi dung trong test de kiem middleware/handler khi chua co endpoint that (T038/T060)
    probe_app = create_app(Settings(_env_file=None))  # type: ignore[call-arg]

    def echo_probe() -> dict[str, str]:
        return {"status": "ok"}

    def domain_error_probe(error_code: str) -> None:
        raise_domain_error(error_code)

    def required_field_probe(clip: str) -> dict[str, str]:
        return {"clip": clip}

    def unexpected_failure_probe() -> None:
        raise RuntimeError(f"khong mo duoc {INTERNAL_SECRET}")

    probe_app.add_api_route(PROBE_PATH, echo_probe, methods=["GET"])
    probe_app.add_api_route(
        f"{PROBE_PATH}/error/{{error_code}}", domain_error_probe, methods=["GET"]
    )
    probe_app.add_api_route(
        f"{PROBE_PATH}/required", required_field_probe, methods=["GET"]
    )
    probe_app.add_api_route(
        f"{PROBE_PATH}/crash", unexpected_failure_probe, methods=["GET"]
    )
    return probe_app


@pytest.fixture
def probe_client() -> Iterator[TestClient]:
    with TestClient(build_probe_app(), raise_server_exceptions=False) as test_client:
        yield test_client


def assert_uuid(candidate: str) -> None:
    assert str(uuid.UUID(candidate)) == candidate


def test_app_publishes_release_from_package_metadata() -> None:
    foundation_app = create_app(Settings(_env_file=None))  # type: ignore[call-arg]

    assert foundation_app.version == version("visign-api") == "0.0.1"


def test_public_router_uses_versioned_prefix() -> None:
    assert API_V1_PREFIX == "/api/v1"
    assert api_v1_router.prefix == API_V1_PREFIX


def test_valid_request_id_is_echoed(probe_client: TestClient) -> None:
    caller_request_id = str(uuid.uuid4())

    probe_response = probe_client.get(
        PROBE_PATH, headers={REQUEST_ID_HEADER: caller_request_id}
    )

    assert probe_response.status_code == 200
    assert probe_response.headers[REQUEST_ID_HEADER] == caller_request_id


@pytest.mark.parametrize("caller_headers", [{}, {REQUEST_ID_HEADER: "khong-phai-uuid"}])
def test_missing_or_invalid_request_id_is_replaced_by_generated_uuid(
    probe_client: TestClient, caller_headers: dict[str, str]
) -> None:
    probe_response = probe_client.get(PROBE_PATH, headers=caller_headers)

    assert_uuid(probe_response.headers[REQUEST_ID_HEADER])
    assert probe_response.headers[REQUEST_ID_HEADER] != caller_headers.get(
        REQUEST_ID_HEADER
    )


@pytest.mark.parametrize(
    ("error_code", "expected_code", "expected_retry_after"),
    [
        ("decode", ErrorCode.CLIP_DECODE_FAILED, None),
        ("busy", ErrorCode.SERVICE_BUSY, "3"),
        ("not-ready", ErrorCode.MODEL_NOT_READY, "5"),
    ],
)
def test_domain_errors_use_catalog_envelope_and_headers(
    probe_client: TestClient,
    error_code: str,
    expected_code: ErrorCode,
    expected_retry_after: str | None,
) -> None:
    caller_request_id = str(uuid.uuid4())

    error_response = probe_client.get(
        f"{PROBE_PATH}/error/{error_code}",
        headers={REQUEST_ID_HEADER: caller_request_id},
    )

    expected_definition = ERROR_CATALOG[expected_code]
    assert error_response.status_code == expected_definition.statusCode
    assert error_response.json() == {
        "code": expected_code.value,
        "message": expected_definition.message,
        "requestId": caller_request_id,
    }
    assert error_response.headers[REQUEST_ID_HEADER] == caller_request_id
    assert error_response.headers.get("Retry-After") == expected_retry_after


def test_request_validation_error_becomes_invalid_request_400(
    probe_client: TestClient,
) -> None:
    invalid_response = probe_client.get(f"{PROBE_PATH}/required")

    assert invalid_response.status_code == 400
    assert invalid_response.json()["code"] == ErrorCode.INVALID_REQUEST.value
    assert "detail" not in invalid_response.json()
    assert (
        invalid_response.json()["requestId"]
        == invalid_response.headers[REQUEST_ID_HEADER]
    )


def test_unexpected_failure_becomes_prediction_failed_without_leaking_internals(
    probe_client: TestClient,
) -> None:
    caller_request_id = str(uuid.uuid4())

    crash_response = probe_client.get(
        f"{PROBE_PATH}/crash", headers={REQUEST_ID_HEADER: caller_request_id}
    )

    assert crash_response.status_code == 500
    assert crash_response.json() == {
        "code": ErrorCode.PREDICTION_FAILED.value,
        "message": ERROR_CATALOG[ErrorCode.PREDICTION_FAILED].message,
        "requestId": caller_request_id,
    }
    assert crash_response.headers[REQUEST_ID_HEADER] == caller_request_id
    for leaked_fragment in (INTERNAL_SECRET, "Traceback", "RuntimeError"):
        assert leaked_fragment not in crash_response.text


def test_cross_origin_server_error_keeps_cors_headers(probe_client: TestClient) -> None:
    # Thieu CORS tren 500 khien trinh duyet chan va FE chi thay loi mang thay vi PREDICTION_FAILED
    crash_response = probe_client.get(
        f"{PROBE_PATH}/crash", headers={"Origin": VITE_ORIGIN}
    )

    assert crash_response.status_code == 500
    assert crash_response.headers["access-control-allow-origin"] == VITE_ORIGIN
    assert crash_response.json()["code"] == ErrorCode.PREDICTION_FAILED.value


def test_cors_allows_vite_origin_and_exposes_correlation_headers(
    probe_client: TestClient,
) -> None:
    preflight_response = probe_client.options(
        PROBE_PATH,
        headers={
            "Origin": VITE_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": REQUEST_ID_HEADER,
        },
    )
    simple_response = probe_client.get(PROBE_PATH, headers={"Origin": VITE_ORIGIN})

    assert preflight_response.status_code == 200
    assert preflight_response.headers["access-control-allow-origin"] == VITE_ORIGIN
    assert "access-control-allow-credentials" not in preflight_response.headers
    exposed_headers = simple_response.headers["access-control-expose-headers"].lower()
    assert "x-request-id" in exposed_headers
    assert "retry-after" in exposed_headers


def test_cors_rejects_unknown_origin(probe_client: TestClient) -> None:
    preflight_response = probe_client.options(
        PROBE_PATH,
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in preflight_response.headers


class RecordingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.captured_records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.captured_records.append(record)


def test_each_request_writes_one_access_log_with_allowed_context(
    probe_client: TestClient,
) -> None:
    recording_handler = RecordingHandler()
    service_logger = logging.getLogger(LOGGER_NAME)
    service_logger.addHandler(recording_handler)
    try:
        caller_request_id = str(uuid.uuid4())
        probe_client.get(PROBE_PATH, headers={REQUEST_ID_HEADER: caller_request_id})
    finally:
        service_logger.removeHandler(recording_handler)

    access_records = [
        record
        for record in recording_handler.captured_records
        if getattr(record, "requestId", None) == caller_request_id
    ]
    assert len(access_records) == 1
    access_record = access_records[0]
    # Field ngu canh duoc gan dong vao LogRecord qua `extra`
    access_context = access_record.__dict__
    assert access_context["method"] == "GET"
    assert access_context["path"] == PROBE_PATH
    assert access_context["statusCode"] == 200
    assert access_context["processingTimeMs"] >= 0
