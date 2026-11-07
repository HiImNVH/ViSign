# services/inference-api/tests/unit/test_observability.py
# Kiem tra log JSON co cau truc, chi ghi field duoc phep va khong lam lo payload (T023).
import json
import logging
from types import TracebackType
from typing import Any

import pytest
from visign_api.observability import (
    LOGGER_NAME,
    StructuredJsonFormatter,
    configure_logging,
)

ExceptionInfo = tuple[type[BaseException], BaseException, TracebackType | None]


def build_record(
    message: str,
    level: int = logging.INFO,
    exception_info: ExceptionInfo | None = None,
    **context: Any,
) -> logging.LogRecord:
    log_record = logging.LogRecord(
        LOGGER_NAME, level, __file__, 1, message, None, exception_info
    )
    for context_key, context_value in context.items():
        setattr(log_record, context_key, context_value)
    return log_record


def format_record(log_record: logging.LogRecord) -> dict[str, Any]:
    formatted_line: dict[str, Any] = json.loads(
        StructuredJsonFormatter().format(log_record)
    )
    return formatted_line


def test_required_observability_fields_are_emitted() -> None:
    # Given ngu canh request day du; Then log co du field T023 yeu cau
    log_line = format_record(
        build_record(
            "Hoan tat nhan dien",
            requestId="0b9f2c1e-4c2a-4d8e-9a51-6f0f8f7d1a10",
            modelVersion="vsl-fixture-v0.0.1",
            processingTimeMs=120,
            timingsMs={"decode": 10, "extract": 90, "infer": 20},
            accepted=False,
            errorCode="CLIP_DECODE_FAILED",
        )
    )

    assert log_line["requestId"] == "0b9f2c1e-4c2a-4d8e-9a51-6f0f8f7d1a10"
    assert log_line["modelVersion"] == "vsl-fixture-v0.0.1"
    assert log_line["processingTimeMs"] == 120
    assert log_line["timingsMs"] == {"decode": 10, "extract": 90, "infer": 20}
    assert log_line["accepted"] is False
    assert log_line["errorCode"] == "CLIP_DECODE_FAILED"


@pytest.mark.parametrize(
    "payload_key",
    [
        "clip",
        "videoBytes",
        "frames",
        "landmarks",
        "coords",
        "tensor",
        "classLabel",
        "filename",
    ],
)
def test_payload_and_biometric_keys_are_never_emitted(payload_key: str) -> None:
    log_record = build_record("Nhan request")
    setattr(log_record, payload_key, [0.1, 0.2])

    assert payload_key not in format_record(log_record)


@pytest.mark.parametrize(
    ("python_level", "expected_level"),
    [
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (logging.WARNING, "WARN"),
        (logging.ERROR, "ERROR"),
        (logging.CRITICAL, "ERROR"),
    ],
)
def test_levels_use_core_log_vocabulary(python_level: int, expected_level: str) -> None:
    assert format_record(build_record("x", python_level))["level"] == expected_level


def test_vietnamese_text_stays_ascii_safe_for_windows_consoles() -> None:
    # Windows chuyen huong stdout bang cp1252; log co dau khong duoc lam roi dong log
    vietnamese_message = "Không thể giải mã video."

    formatted_line = StructuredJsonFormatter().format(build_record(vietnamese_message))

    formatted_line.encode("cp1252")
    assert json.loads(formatted_line)["message"] == vietnamese_message


def test_exception_trace_is_included_for_debugging() -> None:
    try:
        raise RuntimeError("loi gia lap")
    except RuntimeError as simulated_failure:
        exception_info: ExceptionInfo = (
            RuntimeError,
            simulated_failure,
            simulated_failure.__traceback__,
        )

    log_line = format_record(build_record("That bai", logging.ERROR, exception_info))

    assert "RuntimeError: loi gia lap" in log_line["exception"]


def test_configure_logging_is_idempotent() -> None:
    # Goi nhieu lan (reload app, test) khong duoc nhan doi handler
    first_logger = configure_logging()
    second_logger = configure_logging()

    assert first_logger is second_logger
    assert len(second_logger.handlers) == 1
    assert isinstance(second_logger.handlers[0].formatter, StructuredJsonFormatter)
    assert second_logger.propagate is False
