# services/inference-api/tests/unit/test_routing_error_handler.py
# T073: handler loi dinh tuyen chi doi 404/405 sang ErrorEnvelope; status khac giu mac dinh FastAPI, loi la thanh 500.
import asyncio
import json

from fastapi import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from visign_api.api.error_handlers import handle_routing_error
from visign_api.domain.errors import ERROR_CATALOG, ErrorCode

TEAPOT_STATUS = 418


def bare_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/health",
            "headers": [],
            "query_string": b"",
            "state": {},
        }
    )


def test_method_not_allowed_keeps_router_allow_header() -> None:
    routing_error = StarletteHTTPException(405, headers={"Allow": "GET"})

    error_response = asyncio.run(handle_routing_error(bare_request(), routing_error))

    assert error_response.status_code == 405
    assert error_response.headers["Allow"] == "GET"
    assert json.loads(error_response.body)["code"] == ErrorCode.METHOD_NOT_ALLOWED.value


def test_unmapped_http_status_keeps_framework_default() -> None:
    # Chua co ma on dinh cho status nay: khong tu bia ma moi (D3), giu hanh vi FastAPI
    teapot_error = StarletteHTTPException(TEAPOT_STATUS, detail="teapot")

    default_response = asyncio.run(handle_routing_error(bare_request(), teapot_error))

    assert default_response.status_code == TEAPOT_STATUS
    assert json.loads(default_response.body) == {"detail": "teapot"}


def test_non_http_exception_becomes_safe_prediction_failure() -> None:
    unexpected_response = asyncio.run(
        handle_routing_error(bare_request(), RuntimeError("C:\\noi-bo\\bi-mat"))
    )

    error_body = json.loads(unexpected_response.body)
    assert unexpected_response.status_code == 500
    assert error_body["code"] == ErrorCode.PREDICTION_FAILED.value
    assert error_body["message"] == ERROR_CATALOG[ErrorCode.PREDICTION_FAILED].message
    assert "bi-mat" not in unexpected_response.body.decode()
