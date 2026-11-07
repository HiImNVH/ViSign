# tests/security/test_api_security.py
# Audit bao mat T092 (FR-027): security header tren moi response, tat docs mac dinh, CORS khong cho credential,
# ten file client khong quyet dinh noi luu va so field form bi gioi han.
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from visign_api.api.security_headers import served_documentation_pages
from visign_api.config import Settings
from visign_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ARTIFACT = (
    REPOSITORY_ROOT
    / "services"
    / "inference-api"
    / "tests"
    / "fixtures"
    / "model-artifacts"
    / "fixture"
)
PREDICTIONS_PATH = "/api/v1/predictions"
ALLOWED_ORIGIN = "http://localhost:5173"
WEBM_MEDIA_TYPE = "video/webm;codecs=vp8"
SAMPLE_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm security clip"
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
STRICT_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "x-frame-options": "DENY",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
}
# Vuot gioi han 1000 field mac dinh cua parser multipart
EXCESSIVE_FIELD_COUNT = 1001

Scenario = Callable[[TestClient], httpx2.Response]


def settings_with(**overrides: Any) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None, model_artifact_path=FIXTURE_ARTIFACT, **overrides
    )


@pytest.fixture
def api_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    api_temp_directory = tmp_path / "api-temp"
    api_temp_directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(api_temp_directory))
    return api_temp_directory


@pytest.fixture
def security_client(api_temp: Path) -> Iterator[TestClient]:
    with TestClient(create_app(settings_with()), follow_redirects=False) as test_client:
        yield test_client


def post_clip(
    test_client: TestClient, clip_part: tuple[str, bytes, str]
) -> httpx2.Response:
    return test_client.post(PREDICTIONS_PATH, files={"clip": clip_part})


RESPONSE_SCENARIOS: dict[str, Scenario] = {
    "200-health": lambda client: client.get("/api/v1/health"),
    "200-model-info": lambda client: client.get("/api/v1/model-info"),
    "200-prediction": lambda client: post_clip(
        client, ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)
    ),
    "307-trailing-slash": lambda client: client.get("/api/v1/health/"),
    "404-unknown-route": lambda client: client.get("/api/v1/khong-ton-tai"),
    "404-outside-api": lambda client: client.get("/khong-ton-tai"),
    "405-wrong-method": lambda client: client.post("/api/v1/health"),
    "415-media-type": lambda client: post_clip(
        client, ("capture.mp4", SAMPLE_CLIP, "video/mp4")
    ),
}


def assert_strict_headers(api_response: httpx2.Response) -> None:
    for header_name, expected_value in STRICT_HEADERS.items():
        assert api_response.headers[header_name] == expected_value
    # Ket qua nhan dien la du lieu nguoi dung: khong cho trinh duyet hay proxy luu lai
    assert "no-store" in api_response.headers["cache-control"]


@pytest.mark.parametrize("scenario_name", sorted(RESPONSE_SCENARIOS))
def test_every_response_carries_strict_security_headers(
    security_client: TestClient, scenario_name: str
) -> None:
    scenario_response = RESPONSE_SCENARIOS[scenario_name](security_client)

    assert str(scenario_response.status_code) == scenario_name.split("-")[0]
    assert_strict_headers(scenario_response)


@pytest.mark.parametrize("docs_path", DOCS_PATHS)
def test_api_docs_are_disabled_by_default(
    security_client: TestClient, docs_path: str
) -> None:
    docs_response = security_client.get(docs_path)

    assert docs_response.status_code == 404
    assert docs_response.json()["code"] == "ROUTE_NOT_FOUND"
    # Docs tat thi path nay chi la 404 thuong, khong duoc mien CSP nhu trang docs that
    assert_strict_headers(docs_response)


def test_api_docs_can_be_enabled_for_local_development(api_temp: Path) -> None:
    with TestClient(create_app(settings_with(api_docs_enabled=True))) as docs_client:
        page_responses = [docs_client.get(page) for page in ("/docs", "/redoc")]
        schema_response = docs_client.get("/openapi.json")
        health_response = docs_client.get("/api/v1/health")

    assert [response.status_code for response in page_responses] == [200, 200]
    assert schema_response.status_code == 200
    # Chi trang HTML docs can tai script nen duoc mien CSP; schema JSON va API van giu header chat
    for page_response in page_responses:
        assert "content-security-policy" not in page_response.headers
    assert_strict_headers(schema_response)
    assert_strict_headers(health_response)


def test_documentation_pages_follow_fastapi_routes() -> None:
    # FastAPI chi dang ky trang docs khi co openapi_url; trang redirect OAuth2 di kem Swagger UI
    assert served_documentation_pages(FastAPI(openapi_url=None)) == frozenset()
    assert served_documentation_pages(FastAPI(docs_url=None)) == {"/redoc"}
    assert served_documentation_pages(FastAPI()) == {
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    }


def test_cors_never_allows_credentials(security_client: TestClient) -> None:
    simple_response = security_client.get(
        "/api/v1/health", headers={"Origin": ALLOWED_ORIGIN}
    )
    preflight_response = security_client.options(
        PREDICTIONS_PATH,
        headers={"Origin": ALLOWED_ORIGIN, "Access-Control-Request-Method": "POST"},
    )

    assert simple_response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert preflight_response.status_code == 200
    for cors_response in (simple_response, preflight_response):
        assert "access-control-allow-credentials" not in cors_response.headers


def test_client_filename_cannot_choose_storage_location(
    security_client: TestClient, api_temp: Path, tmp_path: Path
) -> None:
    escape_target = tmp_path / "ghi-de-ngoai-thu-muc-tam.webm"
    hostile_names = [
        "../../ghi-de.webm",
        "..\\..\\windows\\win.ini",
        str(escape_target),
        "clip\x00.webm",
    ]

    hostile_responses = [
        post_clip(security_client, (hostile_name, SAMPLE_CLIP, WEBM_MEDIA_TYPE))
        for hostile_name in hostile_names
    ]

    # Ten file bi bo qua: API tu dat ten clip tam ngau nhien va xoa sau khi phuc vu
    assert [response.status_code for response in hostile_responses] == [200] * 4
    assert not escape_target.exists()
    assert list(api_temp.iterdir()) == []


def test_excessive_form_fields_are_rejected(security_client: TestClient) -> None:
    flood_fields = {f"field{index}": "x" for index in range(EXCESSIVE_FIELD_COUNT)}

    flood_response = security_client.post(
        PREDICTIONS_PATH,
        data=flood_fields,
        files={"clip": ("capture.webm", SAMPLE_CLIP, WEBM_MEDIA_TYPE)},
    )

    assert flood_response.status_code == 400
    assert flood_response.json()["code"] == "INVALID_REQUEST"
