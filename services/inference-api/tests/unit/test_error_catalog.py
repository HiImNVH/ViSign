# services/inference-api/tests/unit/test_error_catalog.py
# Kiem tra error catalog va ErrorEnvelope khop contracts/openapi.yaml (T021).
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError
from visign_api.domain.errors import (
    ERROR_CATALOG,
    ClipDecodeFailedException,
    ErrorCode,
    ErrorEnvelope,
    ModelNotReadyException,
    PredictionFailedException,
    ServiceBusyException,
    ViSignApiException,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
OPENAPI_CONTRACT_PATH = (
    REPOSITORY_ROOT / "specs" / "001-vsl-recognition-mvp" / "contracts" / "openapi.yaml"
)

# Status HTTP lay tu cac response duoc khai bao trong openapi.yaml
EXPECTED_STATUS_BY_CODE = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: 415,
    ErrorCode.CLIP_TOO_LARGE: 413,
    ErrorCode.CLIP_TOO_SHORT: 422,
    ErrorCode.CLIP_TOO_LONG: 422,
    ErrorCode.NO_PERSON_DETECTED: 422,
    ErrorCode.INSUFFICIENT_LANDMARKS: 422,
    ErrorCode.CLIP_DECODE_FAILED: 422,
    ErrorCode.SERVICE_BUSY: 503,
    ErrorCode.MODEL_NOT_READY: 503,
    ErrorCode.PREDICTION_FAILED: 500,
}


def load_contract_error_codes() -> list[str]:
    openapi_contract: dict[str, Any] = yaml.safe_load(
        OPENAPI_CONTRACT_PATH.read_text(encoding="utf-8")
    )
    error_code_schema = openapi_contract["components"]["schemas"]["ErrorEnvelope"][
        "properties"
    ]["code"]
    return list(error_code_schema["enum"])


def test_error_codes_match_openapi_enum_in_order() -> None:
    assert [error_code.value for error_code in ErrorCode] == load_contract_error_codes()


def test_every_error_code_has_catalog_entry_with_contract_status() -> None:
    assert set(ERROR_CATALOG) == set(ErrorCode)
    for error_code, expected_status in EXPECTED_STATUS_BY_CODE.items():
        assert ERROR_CATALOG[error_code].statusCode == expected_status


def test_every_catalog_message_is_non_empty_and_hides_internals() -> None:
    for error_definition in ERROR_CATALOG.values():
        assert error_definition.message.strip()
        assert "Exception" not in error_definition.message
        assert "Traceback" not in error_definition.message


def test_exception_takes_status_and_message_from_catalog() -> None:
    decode_failure = ClipDecodeFailedException()

    assert isinstance(decode_failure, ViSignApiException)
    assert decode_failure.code is ErrorCode.CLIP_DECODE_FAILED
    assert decode_failure.statusCode == 422
    assert decode_failure.message == ERROR_CATALOG[ErrorCode.CLIP_DECODE_FAILED].message
    assert decode_failure.retryAfterSeconds is None


@pytest.mark.parametrize(
    "unavailable_exception", [ServiceBusyException, ModelNotReadyException]
)
def test_unavailable_errors_suggest_positive_retry_after(
    unavailable_exception: Callable[[], ViSignApiException],
) -> None:
    # openapi.yaml: Retry-After la so nguyen >= 1
    unavailable_error = unavailable_exception()

    assert unavailable_error.statusCode == 503
    assert unavailable_error.retryAfterSeconds is not None
    assert unavailable_error.retryAfterSeconds >= 1


def test_prediction_failed_has_no_retry_hint() -> None:
    assert PredictionFailedException().retryAfterSeconds is None


def test_error_envelope_serializes_contract_fields() -> None:
    request_id = str(uuid.uuid4())

    error_envelope = ErrorEnvelope(
        code=ErrorCode.SERVICE_BUSY, message="Bận", requestId=request_id
    )

    assert error_envelope.model_dump(mode="json") == {
        "code": "SERVICE_BUSY",
        "message": "Bận",
        "requestId": request_id,
    }


@pytest.mark.parametrize(
    "invalid_fields",
    [
        {"code": "UNKNOWN_CODE", "message": "x", "requestId": str(uuid.uuid4())},
        {"code": "SERVICE_BUSY", "message": "x", "requestId": "not-a-uuid"},
    ],
)
def test_error_envelope_rejects_invalid_fields(invalid_fields: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        ErrorEnvelope(**invalid_fields)
