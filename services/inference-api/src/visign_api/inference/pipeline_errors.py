# services/inference-api/src/visign_api/inference/pipeline_errors.py
# Anh xa ma loi PipelineError cua visign_ai sang ErrorCode on dinh cua API (T037).
from visign_api.domain.errors import ErrorCode

# Ma goc cua pipeline duoc giu trong log/report cua CLI; adapter chi tra ma da anh xa qua HTTP
PIPELINE_TO_API_ERROR: dict[str, ErrorCode] = {
    "INVALID_REQUEST": ErrorCode.INVALID_REQUEST,
    "UNSUPPORTED_MEDIA_TYPE": ErrorCode.UNSUPPORTED_MEDIA_TYPE,
    "CLIP_TOO_LARGE": ErrorCode.CLIP_TOO_LARGE,
    "CLIP_TOO_SHORT": ErrorCode.CLIP_TOO_SHORT,
    "CLIP_TOO_LONG": ErrorCode.CLIP_TOO_LONG,
    "CLIP_DECODE_FAILED": ErrorCode.CLIP_DECODE_FAILED,
    "NO_PERSON_DETECTED": ErrorCode.NO_PERSON_DETECTED,
    "INSUFFICIENT_LANDMARKS": ErrorCode.INSUFFICIENT_LANDMARKS,
    # PTS hong la loi noi dung clip, nguoi dung quay lai duoc
    "INVALID_TIMESTAMPS": ErrorCode.CLIP_DECODE_FAILED,
    # Lech schema, extractor hoac detector la loi cau hinh server: fail closed, khong do cho clip
    "FEATURE_SCHEMA_MISMATCH": ErrorCode.MODEL_NOT_READY,
    "EXTRACTOR_VERSION_MISMATCH": ErrorCode.MODEL_NOT_READY,
    "MODEL_ASSET_MISMATCH": ErrorCode.MODEL_NOT_READY,
}


def map_pipeline_error_code(pipeline_error_code: str) -> ErrorCode:
    # Ma chua biet di vao 500 khong lo chi tiet; test quet ma nguon de ma moi phai co anh xa
    return PIPELINE_TO_API_ERROR.get(pipeline_error_code, ErrorCode.PREDICTION_FAILED)
