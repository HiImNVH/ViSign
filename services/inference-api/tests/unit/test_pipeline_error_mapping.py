# services/inference-api/tests/unit/test_pipeline_error_mapping.py
# Kiem tra anh xa ma loi PipelineError cua visign_ai sang ErrorCode/HTTP status cua API (T037).
import re
from pathlib import Path

import pytest
from visign_api.domain.errors import ERROR_CATALOG, ErrorCode
from visign_api.inference.pipeline_errors import (
    PIPELINE_TO_API_ERROR,
    map_pipeline_error_code,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PIPELINE_SOURCE_DIR = REPOSITORY_ROOT / "ai" / "src" / "visign_ai" / "landmarks"
PIPELINE_ERROR_PATTERN = re.compile(r'PipelineError\(\s*"([A-Z_]+)"')


def collect_raised_pipeline_codes() -> set[str]:
    # Doc thang ma nguon pipeline de ma moi cua P3 khong lot qua ma thieu anh xa
    raised_codes: set[str] = set()
    for pipeline_source in PIPELINE_SOURCE_DIR.glob("*.py"):
        raised_codes.update(
            PIPELINE_ERROR_PATTERN.findall(pipeline_source.read_text(encoding="utf-8"))
        )
    return raised_codes


def test_pipeline_source_is_scanned() -> None:
    assert "CLIP_DECODE_FAILED" in collect_raised_pipeline_codes()


def test_every_raised_pipeline_code_has_explicit_mapping() -> None:
    unmapped_codes = collect_raised_pipeline_codes() - set(PIPELINE_TO_API_ERROR)

    assert unmapped_codes == set(), (
        f"Thieu anh xa cho ma pipeline: {sorted(unmapped_codes)}"
    )


@pytest.mark.parametrize(
    "shared_code",
    [
        "INVALID_REQUEST",
        "UNSUPPORTED_MEDIA_TYPE",
        "CLIP_TOO_LARGE",
        "CLIP_TOO_SHORT",
        "CLIP_TOO_LONG",
        "CLIP_DECODE_FAILED",
        "NO_PERSON_DETECTED",
        "INSUFFICIENT_LANDMARKS",
    ],
)
def test_codes_shared_with_api_catalog_pass_through(shared_code: str) -> None:
    assert map_pipeline_error_code(shared_code) is ErrorCode(shared_code)


def test_invalid_timestamps_becomes_decode_failure_422() -> None:
    # Given clip co PTS hong; Then nguoi dung nhan loi giai ma 422 de quay lai
    mapped_code = map_pipeline_error_code("INVALID_TIMESTAMPS")

    assert mapped_code is ErrorCode.CLIP_DECODE_FAILED
    assert ERROR_CATALOG[mapped_code].statusCode == 422


@pytest.mark.parametrize(
    "configuration_code",
    ["FEATURE_SCHEMA_MISMATCH", "EXTRACTOR_VERSION_MISMATCH", "MODEL_ASSET_MISMATCH"],
)
def test_server_configuration_errors_become_model_not_ready_503(
    configuration_code: str,
) -> None:
    # Loi cau hinh phia server: fail closed, khong do loi cho clip cua nguoi dung
    mapped_code = map_pipeline_error_code(configuration_code)

    assert mapped_code is ErrorCode.MODEL_NOT_READY
    assert ERROR_CATALOG[mapped_code].statusCode == 503


def test_unknown_pipeline_code_fails_closed_as_prediction_failed() -> None:
    mapped_code = map_pipeline_error_code("SOMETHING_NEW")

    assert mapped_code is ErrorCode.PREDICTION_FAILED
    assert ERROR_CATALOG[mapped_code].statusCode == 500
