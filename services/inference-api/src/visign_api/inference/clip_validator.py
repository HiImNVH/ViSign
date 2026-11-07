# services/inference-api/src/visign_api/inference/clip_validator.py
# Kiem clip tai ranh gioi API (T049): MIME, Content-Length va chu ky WebM truoc khi giu slot; thoi luong PTS va do du
# nguoi/landmark sau khi trich dac trung. Probe codec VP8/VP9 va giai ma do VideoDecoder dung chung dam nhan.
from collections.abc import Iterable
from dataclasses import dataclass

from visign_api.domain.errors import (
    ClipTooLargeException,
    ClipTooLongException,
    ClipTooShortException,
    InsufficientLandmarksException,
    InvalidRequestException,
    NoPersonDetectedException,
    UnsupportedMediaTypeException,
)
from visign_api.inference.feature_extraction import ExtractedFeatures

# Cung quy tac voi VideoDecoder cua visign_ai: EBML o byte 0 va DocType "webm" trong 4096 byte dau
EBML_MAGIC = b"\x1a\x45\xdf\xa3"
WEBM_DOCTYPE_ELEMENT = b"\x42\x82\x84webm"
SIGNATURE_SCAN_BYTES = 4096
# Phan bao multipart (boundary, header cua part) duoc cong them vao gioi han clip khi kiem body
MULTIPART_OVERHEAD_BYTES = 64 * 1024
# Gia tri inputStatus cua pipeline khi co frame du vai va it nhat mot ban tay (CLI T017 dung cung quy tac)
USABLE_INPUT_STATUS = "HAS_USABLE_FRAMES"


@dataclass(frozen=True)
class DurationWindow:
    minMs: int
    maxMs: int


def normalize_media_type(raw_media_type: str | None) -> str:
    # Bo khoang trang, dau nhay va chu hoa: 'video/webm; codecs="vp8"' trung 'video/webm;codecs=vp8'
    return "".join((raw_media_type or "").split()).replace('"', "").lower()


def ensure_supported_media_type(
    raw_media_type: str | None, allowed_media_types: Iterable[str]
) -> None:
    normalized_allowlist = {
        normalize_media_type(allowed_type) for allowed_type in allowed_media_types
    }
    if normalize_media_type(raw_media_type) not in normalized_allowlist:
        raise UnsupportedMediaTypeException()


def ensure_webm_signature(clip_bytes: bytes) -> None:
    # Nhan MIME do client khai; byte dau moi cho biet that su la WebM truoc khi ton slot suy luan
    clip_header = clip_bytes[:SIGNATURE_SCAN_BYTES]
    if (
        not clip_header.startswith(EBML_MAGIC)
        or WEBM_DOCTYPE_ELEMENT not in clip_header
    ):
        raise UnsupportedMediaTypeException()


def max_upload_body_bytes(max_clip_bytes: int) -> int:
    return max_clip_bytes + MULTIPART_OVERHEAD_BYTES


def ensure_declared_length_within_limit(
    declared_length: str | None, max_body_bytes: int
) -> None:
    # Thieu Content-Length (chunked) thi bo dem byte khi doc stream chan thay
    if declared_length is None:
        return
    if not (declared_length.isascii() and declared_length.isdigit()):
        raise InvalidRequestException()
    if int(declared_length) > max_body_bytes:
        raise ClipTooLargeException()


def validate_extracted_clip(
    extracted_features: ExtractedFeatures, duration_window: DurationWindow
) -> None:
    ensure_duration_within_window(extracted_features.ptsSpanMs, duration_window)
    ensure_landmarks_sufficient(extracted_features)


def ensure_duration_within_window(
    pts_span_ms: float, duration_window: DurationWindow
) -> None:
    # Thoi luong do tu PTS da giai ma, khong tin so client gui (contract AI-BE)
    if pts_span_ms < duration_window.minMs:
        raise ClipTooShortException()
    if pts_span_ms > duration_window.maxMs:
        raise ClipTooLongException()


def ensure_landmarks_sufficient(extracted_features: ExtractedFeatures) -> None:
    # Chi phan lop khi pipeline bao co frame dung duoc; trang thai la cung coi la khong dung duoc
    if extracted_features.inputStatus == USABLE_INPUT_STATUS:
        return
    has_any_detection = bool(
        extracted_features.groupMask.any() or extracted_features.tensorMask.any()
    )
    if not has_any_detection:
        raise NoPersonDetectedException()
    raise InsufficientLandmarksException()
