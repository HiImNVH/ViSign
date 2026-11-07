# services/inference-api/tests/contract/test_http_routing_contract.py
# Contract test T072: 404/405 dung ErrorEnvelope, 307 giu method/body/Location, X-Request-ID tren moi response,
# 403/304 chua bat (docs/team/backend-http-status-contract.md).
import uuid
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit

import httpx2
import pytest
from fastapi.testclient import TestClient
from visign_api.config import Settings
from visign_api.domain.errors import ERROR_CATALOG, ErrorCode
from visign_api.main import create_app

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
REQUEST_ID_HEADER = "X-Request-ID"
ALLOWED_ORIGIN = "http://localhost:5173"
DISALLOWED_ORIGIN = "https://khong-duoc-phep.example"
# Header EBML + DocType "webm" de qua kiem chu ky T049
SAMPLE_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm routing clip"
WEBM_MEDIA_TYPE = "video/webm;codecs=vp8"


def fixture_app_client(follow_redirects: bool) -> TestClient:
    fixture_settings = Settings(  # type: ignore[call-arg]
        _env_file=None, model_artifact_path=FIXTURE_ARTIFACTS / "fixture"
    )
    return TestClient(create_app(fixture_settings), follow_redirects=follow_redirects)


@pytest.fixture
def routing_client() -> Iterator[TestClient]:
    # Tat tu dong theo redirect de thay duoc 307 that cua router
    with fixture_app_client(follow_redirects=False) as test_client:
        yield test_client


def assert_error_envelope(
    error_response: httpx2.Response, error_code: ErrorCode
) -> None:
    error_definition = ERROR_CATALOG[error_code]
    effective_request_id = error_response.headers[REQUEST_ID_HEADER]
    assert error_response.status_code == error_definition.statusCode
    assert error_response.headers["content-type"].startswith("application/json")
    # So khop ca dict: khong bao gio la {"detail": ...} mac dinh cua FastAPI
    assert error_response.json() == {
        "code": error_code.value,
        "message": error_definition.message,
        "requestId": effective_request_id,
    }
    assert str(uuid.UUID(effective_request_id)) == effective_request_id
    assert "retry-after" not in error_response.headers


def allowed_methods(method_response: httpx2.Response) -> set[str]:
    return {
        allowed_method.strip()
        for allowed_method in method_response.headers["allow"].split(",")
    }


@pytest.mark.parametrize(
    "unknown_path", ["/api/v1/not-found", "/api/v2/health", "/khong-ton-tai"]
)
def test_unknown_route_returns_route_not_found_envelope(
    routing_client: TestClient, unknown_path: str
) -> None:
    not_found_response = routing_client.get(unknown_path)

    assert_error_envelope(not_found_response, ErrorCode.ROUTE_NOT_FOUND)
    # Message co dinh tu catalog, khong lap lai URL tho cua client
    assert unknown_path not in not_found_response.text


def test_caller_request_id_is_echoed_on_route_not_found(
    routing_client: TestClient,
) -> None:
    caller_request_id = str(uuid.uuid4())

    not_found_response = routing_client.get(
        "/api/v1/not-found", headers={REQUEST_ID_HEADER: caller_request_id}
    )

    assert not_found_response.headers[REQUEST_ID_HEADER] == caller_request_id
    assert not_found_response.json()["requestId"] == caller_request_id


@pytest.mark.parametrize(
    ("http_method", "known_path", "expected_allow"),
    [
        ("POST", "/api/v1/health", {"GET"}),
        ("DELETE", "/api/v1/model-info", {"GET"}),
        ("GET", "/api/v1/predictions", {"POST"}),
        ("PUT", "/api/v1/predictions", {"POST"}),
    ],
)
def test_wrong_method_returns_method_not_allowed_with_allow_header(
    routing_client: TestClient,
    http_method: str,
    known_path: str,
    expected_allow: set[str],
) -> None:
    method_response = routing_client.request(http_method, known_path)

    assert_error_envelope(method_response, ErrorCode.METHOD_NOT_ALLOWED)
    # Giu nguyen header Allow do router sinh ra
    assert allowed_methods(method_response) == expected_allow


def test_trailing_slash_redirects_to_canonical_path(routing_client: TestClient) -> None:
    redirect_response = routing_client.get("/api/v1/health/")

    effective_request_id = redirect_response.headers[REQUEST_ID_HEADER]
    assert redirect_response.status_code == 307
    assert urlsplit(redirect_response.headers["location"]).path == "/api/v1/health"
    assert str(uuid.UUID(effective_request_id)) == effective_request_id


def test_redirect_keeps_method_and_body_for_predictions() -> None:
    # 307 (khong phai 302): client lap lai dung POST va body multipart toi path chuan
    with fixture_app_client(follow_redirects=True) as following_client:
        prediction_response = following_client.post(
            "/api/v1/predictions/",
            files={"clip": ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)},
        )

    assert [hop.status_code for hop in prediction_response.history] == [307]
    assert prediction_response.request.method == "POST"
    assert prediction_response.status_code == 200
    assert prediction_response.json()["accepted"] is True


def test_conditional_requests_never_produce_not_modified(
    routing_client: TestClient,
) -> None:
    # 304 chua bat: health luon phan anh trang thai hien tai, model-info chua co ETag
    conditional_headers = {
        "If-None-Match": "*",
        "If-Modified-Since": "Wed, 21 Oct 2015 07:28:00 GMT",
    }

    health_response = routing_client.get("/api/v1/health", headers=conditional_headers)
    model_info_response = routing_client.get(
        "/api/v1/model-info", headers=conditional_headers
    )

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert health_response.headers["cache-control"] == "no-store"
    assert model_info_response.status_code == 200
    assert "etag" not in health_response.headers
    assert "etag" not in model_info_response.headers


def test_disallowed_origin_is_not_reported_as_forbidden(
    routing_client: TestClient,
) -> None:
    # Ngoai le preflight (quy uoc T099): lop CORS tra 400 text, khong phai 403 va khong phai ErrorEnvelope
    preflight_response = routing_client.options(
        "/api/v1/predictions",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )
    simple_response = routing_client.get(
        "/api/v1/health", headers={"Origin": DISALLOWED_ORIGIN}
    )

    assert preflight_response.status_code == 400
    assert "access-control-allow-origin" not in preflight_response.headers
    assert simple_response.status_code == 200
    assert "access-control-allow-origin" not in simple_response.headers


@pytest.mark.parametrize(
    ("http_method", "error_path"),
    [("GET", "/api/v1/not-found"), ("POST", "/api/v1/health")],
)
def test_routing_errors_expose_request_id_to_web_origin(
    routing_client: TestClient, http_method: str, error_path: str
) -> None:
    routing_response = routing_client.request(
        http_method, error_path, headers={"Origin": ALLOWED_ORIGIN}
    )

    exposed_headers = {
        header_name.strip().lower()
        for header_name in routing_response.headers[
            "access-control-expose-headers"
        ].split(",")
    }
    assert routing_response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "x-request-id" in exposed_headers
