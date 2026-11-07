# services/inference-api/tests/unit/test_clip_validator.py
# Kiem clip validation T049: MIME, chu ky WebM, Content-Length, thoi luong PTS va do du nguoi/landmark.
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from visign_api.config import DEFAULT_ALLOWED_MIME_TYPES
from visign_api.domain.errors import (
    ClipTooLargeException,
    ClipTooLongException,
    ClipTooShortException,
    InsufficientLandmarksException,
    InvalidRequestException,
    NoPersonDetectedException,
    UnsupportedMediaTypeException,
)
from visign_api.domain.prediction import PredictionQualityHints
from visign_api.inference.clip_validator import (
    MULTIPART_OVERHEAD_BYTES,
    SIGNATURE_SCAN_BYTES,
    DurationWindow,
    ensure_declared_length_within_limit,
    ensure_landmarks_sufficient,
    ensure_supported_media_type,
    ensure_webm_signature,
    max_upload_body_bytes,
    normalize_media_type,
    validate_extracted_clip,
)
from visign_api.inference.feature_extraction import ExtractedFeatures

WEBM_HEADER = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm\x42\x87\x81\x04"
CONTRACT_WINDOW = DurationWindow(minMs=300, maxMs=6000)
TARGET_FRAME_COUNT = 32
LANDMARK_COUNT = 78
SOURCE_FRAME_COUNT = 6


def extracted_features(**overrides: Any) -> ExtractedFeatures:
    feature_fields: dict[str, Any] = {
        "tensor": np.zeros((TARGET_FRAME_COUNT, 3 * LANDMARK_COUNT), dtype=np.float32),
        "tensorMask": np.ones((TARGET_FRAME_COUNT, LANDMARK_COUNT), dtype=bool),
        "groupMask": np.ones((SOURCE_FRAME_COUNT, 4), dtype=bool),
        "featureSchemaVersion": "visign-xy-32-v0.3-draft",
        "inputStatus": "HAS_USABLE_FRAMES",
        "qualityHints": PredictionQualityHints(handsDetectedRatio=1.0, frameCount=46),
        "decodeMs": 20,
        "extractMs": 1500,
        "ptsSpanMs": 1500.0,
    }
    feature_fields.update(overrides)
    return ExtractedFeatures(**feature_fields)


@pytest.mark.parametrize(
    ("raw_media_type", "normalized_media_type"),
    [
        ("video/webm;codecs=vp8", "video/webm;codecs=vp8"),
        ("Video/WebM; codecs=VP9", "video/webm;codecs=vp9"),
        ('video/webm; codecs="vp8, opus"', "video/webm;codecs=vp8,opus"),
        (None, ""),
    ],
)
def test_media_type_is_normalized_before_comparison(
    raw_media_type: str | None, normalized_media_type: str
) -> None:
    assert normalize_media_type(raw_media_type) == normalized_media_type


@pytest.mark.parametrize(
    "browser_media_type",
    ["video/webm", "video/webm;codecs=vp8", "video/webm; codecs=vp9", "VIDEO/WEBM"],
)
def test_browser_webm_media_types_are_accepted(browser_media_type: str) -> None:
    ensure_supported_media_type(browser_media_type, DEFAULT_ALLOWED_MIME_TYPES)


@pytest.mark.parametrize(
    "rejected_media_type",
    [
        "video/mp4",
        "video/x-matroska;codecs=avc1",
        "video/webm;codecs=h264",
        "application/octet-stream",
        "",
        None,
    ],
)
def test_unsupported_media_types_are_rejected(rejected_media_type: str | None) -> None:
    with pytest.raises(UnsupportedMediaTypeException):
        ensure_supported_media_type(rejected_media_type, DEFAULT_ALLOWED_MIME_TYPES)


def test_webm_signature_is_accepted() -> None:
    ensure_webm_signature(WEBM_HEADER + b"cluster data")


@pytest.mark.parametrize(
    "foreign_bytes",
    [
        b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32,
        b"\x1a\x45\xdf\xa3\x9f\x42\x82\x88matroska",
        b"\x1a\x45\xdf\xa3 khong co doctype",
        b"\x89PNG\r\n\x1a\n" + WEBM_HEADER,
        b"\x1a\x45\xdf\xa3" + b"\x00" * SIGNATURE_SCAN_BYTES + b"\x42\x82\x84webm",
        b"",
    ],
)
def test_bytes_without_webm_signature_are_unsupported(foreign_bytes: bytes) -> None:
    # Cung quy tac voi VideoDecoder: EBML o byte 0 va DocType webm trong 4096 byte dau
    with pytest.raises(UnsupportedMediaTypeException):
        ensure_webm_signature(foreign_bytes)


def test_upload_body_limit_adds_multipart_overhead() -> None:
    assert max_upload_body_bytes(10_485_760) == 10_485_760 + MULTIPART_OVERHEAD_BYTES


@pytest.mark.parametrize("declared_length", [None, "0", "100"])
def test_declared_length_within_limit_passes(declared_length: str | None) -> None:
    ensure_declared_length_within_limit(declared_length, 100)


def test_declared_length_over_limit_is_too_large() -> None:
    with pytest.raises(ClipTooLargeException):
        ensure_declared_length_within_limit("101", 100)


@pytest.mark.parametrize("declared_length", ["abc", "-1", "1e3", "²", ""])
def test_malformed_declared_length_is_invalid_request(declared_length: str) -> None:
    with pytest.raises(InvalidRequestException):
        ensure_declared_length_within_limit(declared_length, 100)


@pytest.mark.parametrize("pts_span_ms", [300.0, 1500.0, 6000.0])
def test_duration_inside_window_passes(pts_span_ms: float) -> None:
    validate_extracted_clip(extracted_features(ptsSpanMs=pts_span_ms), CONTRACT_WINDOW)


def test_duration_below_window_is_too_short() -> None:
    with pytest.raises(ClipTooShortException):
        validate_extracted_clip(extracted_features(ptsSpanMs=299.5), CONTRACT_WINDOW)


def test_duration_above_window_is_too_long() -> None:
    # Cua so cau hinh hep hon gioi han cung cua decoder van phai co hieu luc
    stricter_window = DurationWindow(minMs=300, maxMs=5000)

    with pytest.raises(ClipTooLongException):
        validate_extracted_clip(extracted_features(ptsSpanMs=5000.5), stricter_window)


def test_usable_frames_are_sufficient() -> None:
    ensure_landmarks_sufficient(extracted_features())


def test_person_without_usable_frames_has_insufficient_landmarks() -> None:
    # Co vai va mat nhung khong co ban tay: co nguoi, chua du landmark de phan lop
    shoulders_and_face_only: NDArray[np.bool_] = np.zeros(
        (SOURCE_FRAME_COUNT, 4), dtype=bool
    )
    shoulders_and_face_only[:, 2:] = True

    with pytest.raises(InsufficientLandmarksException):
        ensure_landmarks_sufficient(
            extracted_features(
                inputStatus="INSUFFICIENT_LANDMARKS", groupMask=shoulders_and_face_only
            )
        )


def test_partial_points_without_full_groups_still_mean_a_person() -> None:
    partial_points: NDArray[np.bool_] = np.zeros(
        (TARGET_FRAME_COUNT, LANDMARK_COUNT), dtype=bool
    )
    partial_points[:, 50] = True

    with pytest.raises(InsufficientLandmarksException):
        ensure_landmarks_sufficient(
            extracted_features(
                inputStatus="INSUFFICIENT_LANDMARKS",
                groupMask=np.zeros((SOURCE_FRAME_COUNT, 4), dtype=bool),
                tensorMask=partial_points,
            )
        )


def test_nothing_detected_means_no_person() -> None:
    with pytest.raises(NoPersonDetectedException):
        ensure_landmarks_sufficient(
            extracted_features(
                inputStatus="INSUFFICIENT_LANDMARKS",
                groupMask=np.zeros((SOURCE_FRAME_COUNT, 4), dtype=bool),
                tensorMask=np.zeros((TARGET_FRAME_COUNT, LANDMARK_COUNT), dtype=bool),
            )
        )


def test_unknown_input_status_is_never_treated_as_usable() -> None:
    with pytest.raises(InsufficientLandmarksException):
        ensure_landmarks_sufficient(extracted_features(inputStatus="UNKNOWN_STATUS"))
