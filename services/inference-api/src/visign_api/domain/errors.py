# services/inference-api/src/visign_api/domain/errors.py
# Error catalog on dinh, ErrorEnvelope va exception domain theo contracts/openapi.yaml (T021).
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, model_validator

from visign_api.domain.request_id import ensure_uuid

SERVICE_BUSY_RETRY_AFTER_SECONDS = 3
MODEL_NOT_READY_RETRY_AFTER_SECONDS = 5


class ErrorCode(StrEnum):
    # Thu tu khop enum ErrorEnvelope.code trong openapi.yaml de drift test so sanh truc tiep
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    CLIP_TOO_LARGE = "CLIP_TOO_LARGE"
    CLIP_TOO_SHORT = "CLIP_TOO_SHORT"
    CLIP_TOO_LONG = "CLIP_TOO_LONG"
    NO_PERSON_DETECTED = "NO_PERSON_DETECTED"
    INSUFFICIENT_LANDMARKS = "INSUFFICIENT_LANDMARKS"
    CLIP_DECODE_FAILED = "CLIP_DECODE_FAILED"
    SERVICE_BUSY = "SERVICE_BUSY"
    MODEL_NOT_READY = "MODEL_NOT_READY"
    PREDICTION_FAILED = "PREDICTION_FAILED"


@dataclass(frozen=True)
class ErrorDefinition:
    statusCode: int
    message: str
    retryAfterSeconds: int | None = None


ERROR_CATALOG: dict[ErrorCode, ErrorDefinition] = {
    ErrorCode.INVALID_REQUEST: ErrorDefinition(400, "Yêu cầu không hợp lệ hoặc thiếu dữ liệu video."),
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: ErrorDefinition(
        415, "Định dạng video không được hỗ trợ. Vui lòng gửi video WebM."
    ),
    ErrorCode.CLIP_TOO_LARGE: ErrorDefinition(413, "Dung lượng video vượt quá giới hạn cho phép."),
    ErrorCode.CLIP_TOO_SHORT: ErrorDefinition(422, "Đoạn video quá ngắn để nhận diện ký hiệu."),
    ErrorCode.CLIP_TOO_LONG: ErrorDefinition(
        422, "Đoạn video quá dài so với giới hạn của ký hiệu đơn lẻ."
    ),
    ErrorCode.NO_PERSON_DETECTED: ErrorDefinition(422, "Không phát hiện người trong khung hình camera."),
    ErrorCode.INSUFFICIENT_LANDMARKS: ErrorDefinition(
        422, "Không phát hiện đủ các điểm khớp bàn tay/cơ thể để nhận diện."
    ),
    ErrorCode.CLIP_DECODE_FAILED: ErrorDefinition(
        422, "Không thể giải mã video. Tệp có thể bị hỏng hoặc thiếu timestamp."
    ),
    ErrorCode.SERVICE_BUSY: ErrorDefinition(
        503,
        "Hệ thống đang bận xử lý yêu cầu khác. Vui lòng thử lại sau.",
        SERVICE_BUSY_RETRY_AFTER_SECONDS,
    ),
    ErrorCode.MODEL_NOT_READY: ErrorDefinition(
        503, "Mô hình nhận diện chưa sẵn sàng.", MODEL_NOT_READY_RETRY_AFTER_SECONDS
    ),
    ErrorCode.PREDICTION_FAILED: ErrorDefinition(500, "Xử lý nhận diện thất bại do lỗi không xác định."),
}


class ErrorEnvelope(BaseModel):
    # Khop contracts/openapi.yaml #/components/schemas/ErrorEnvelope
    code: ErrorCode
    message: str
    requestId: str

    @model_validator(mode="after")
    def validate_request_id(self) -> "ErrorEnvelope":
        ensure_uuid(self.requestId)
        return self


class ViSignApiException(Exception):
    # Status va message lay tu catalog de client chi re nhanh theo code on dinh
    def __init__(self, code: ErrorCode) -> None:
        error_definition = ERROR_CATALOG[code]
        super().__init__(error_definition.message)
        self.code = code
        self.statusCode = error_definition.statusCode
        self.message = error_definition.message
        self.retryAfterSeconds = error_definition.retryAfterSeconds


class InvalidRequestException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.INVALID_REQUEST)


class UnsupportedMediaTypeException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.UNSUPPORTED_MEDIA_TYPE)


class ClipTooLargeException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.CLIP_TOO_LARGE)


class ClipTooShortException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.CLIP_TOO_SHORT)


class ClipTooLongException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.CLIP_TOO_LONG)


class NoPersonDetectedException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.NO_PERSON_DETECTED)


class InsufficientLandmarksException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.INSUFFICIENT_LANDMARKS)


class ClipDecodeFailedException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.CLIP_DECODE_FAILED)


class ServiceBusyException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.SERVICE_BUSY)


class ModelNotReadyException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.MODEL_NOT_READY)


class PredictionFailedException(ViSignApiException):
    def __init__(self) -> None:
        super().__init__(ErrorCode.PREDICTION_FAILED)
