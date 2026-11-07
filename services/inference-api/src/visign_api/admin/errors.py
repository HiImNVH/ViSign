# services/inference-api/src/visign_api/admin/errors.py
# Loi cua cong cu admin (T079, contracts/admin-tools.md): cung hinh dang envelope {code, message, requestId} nhung
# ma rieng ADMIN_*, khong vao catalog /api/v1; message tieng Viet on dinh, khong lo token, duong dan hay traceback.
import logging
from dataclasses import dataclass
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from visign_api.api.request_context import REQUEST_ID_HEADER, get_request_id
from visign_api.observability import LOGGER_NAME

WWW_AUTHENTICATE_HEADER = "WWW-Authenticate"

service_logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class AdminErrorDefinition:
    statusCode: int
    code: str
    message: str


ADMIN_UNAUTHORIZED = AdminErrorDefinition(
    HTTPStatus.UNAUTHORIZED, "ADMIN_UNAUTHORIZED", "Mã admin không hợp lệ."
)
ADMIN_JOB_ACTIVE = AdminErrorDefinition(
    HTTPStatus.CONFLICT, "ADMIN_JOB_ACTIVE", "Đang có một công việc admin khác chạy."
)
ADMIN_PILOT_NOT_READY = AdminErrorDefinition(
    HTTPStatus.CONFLICT,
    "ADMIN_PILOT_NOT_READY",
    "Pilot chưa được chuẩn bị xong; hãy chạy bước chuẩn bị trước.",
)
ADMIN_UNAVAILABLE = AdminErrorDefinition(
    HTTPStatus.SERVICE_UNAVAILABLE,
    "ADMIN_UNAVAILABLE",
    "Môi trường admin chưa đủ để chạy yêu cầu này.",
)
ADMIN_TIMEOUT = AdminErrorDefinition(
    HTTPStatus.GATEWAY_TIMEOUT,
    "ADMIN_TIMEOUT",
    "Kiểm tra clip quá thời gian cho phép.",
)


class AdminApiException(Exception):
    def __init__(self, definition: AdminErrorDefinition) -> None:
        super().__init__(definition.code)
        self.definition = definition


async def handle_admin_error(request: Request, raised_error: Exception) -> JSONResponse:
    if not isinstance(raised_error, AdminApiException):
        raise raised_error
    definition = raised_error.definition
    request_id = get_request_id(request)
    service_logger.warning(
        "Request admin bi tu choi voi ma loi on dinh",
        extra={"requestId": request_id, "errorCode": definition.code},
    )
    response_headers = {REQUEST_ID_HEADER: request_id}
    if definition == ADMIN_UNAUTHORIZED:
        # RFC 6750: client biet can Bearer token, khong neu ly do (thieu, sai dang hay sai gia tri)
        response_headers[WWW_AUTHENTICATE_HEADER] = "Bearer"
    return JSONResponse(
        status_code=definition.statusCode,
        content={
            "code": definition.code,
            "message": definition.message,
            "requestId": request_id,
        },
        headers=response_headers,
    )


def register_admin_error_handler(service_app: FastAPI) -> None:
    service_app.add_exception_handler(AdminApiException, handle_admin_error)
