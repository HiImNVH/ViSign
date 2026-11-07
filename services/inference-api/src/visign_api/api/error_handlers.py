# services/inference-api/src/visign_api/api/error_handlers.py
# Anh xa exception sang ErrorEnvelope on dinh; loi bat ngo tra 500 khong lo traceback hay duong dan (T026);
# 404/405 cua router dung chung ErrorEnvelope va giu header Allow (T073).
import logging
from http import HTTPStatus

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from visign_api.api.request_context import REQUEST_ID_HEADER, get_request_id
from visign_api.domain.errors import (
    ErrorCode,
    ErrorEnvelope,
    InvalidRequestException,
    PredictionFailedException,
    ViSignApiException,
    build_api_exception,
)
from visign_api.observability import LOGGER_NAME

RETRY_AFTER_HEADER = "Retry-After"
# Router Starlette nem HTTPException cho route la va sai method; doi sang ma on dinh cua catalog
ROUTING_ERROR_BY_STATUS: dict[int, ErrorCode] = {
    HTTPStatus.NOT_FOUND: ErrorCode.ROUTE_NOT_FOUND,
    HTTPStatus.METHOD_NOT_ALLOWED: ErrorCode.METHOD_NOT_ALLOWED,
}
# Header do router sinh ra phai giu tren response loi (Allow cua 405 theo RFC 9110)
PRESERVED_ROUTING_HEADERS = ("Allow",)

service_logger = logging.getLogger(LOGGER_NAME)


def build_error_response(
    api_error: ViSignApiException, request_id: str
) -> JSONResponse:
    error_envelope = ErrorEnvelope(
        code=api_error.code, message=api_error.message, requestId=request_id
    )
    response_headers = {REQUEST_ID_HEADER: request_id}
    if api_error.retryAfterSeconds is not None:
        response_headers[RETRY_AFTER_HEADER] = str(api_error.retryAfterSeconds)
    return JSONResponse(
        status_code=api_error.statusCode,
        content=error_envelope.model_dump(mode="json"),
        headers=response_headers,
    )


def respond_to_unexpected_error(
    request: Request, unexpected_error: Exception
) -> JSONResponse:
    request_id = get_request_id(request)
    # Traceback chi o log server; client chi nhan ma on dinh va message trong catalog
    service_logger.error(
        "Loi khong mong doi khi xu ly request",
        exc_info=unexpected_error,
        extra={
            "requestId": request_id,
            "errorCode": PredictionFailedException().code.value,
        },
    )
    return build_error_response(PredictionFailedException(), request_id)


async def handle_domain_error(
    request: Request, raised_error: Exception
) -> JSONResponse:
    if not isinstance(raised_error, ViSignApiException):
        return respond_to_unexpected_error(request, raised_error)
    request_id = get_request_id(request)
    service_logger.warning(
        "Request bi tu choi voi ma loi on dinh",
        extra={"requestId": request_id, "errorCode": raised_error.code.value},
    )
    return build_error_response(raised_error, request_id)


async def handle_validation_error(
    request: Request, raised_error: Exception
) -> JSONResponse:
    # Thieu/sai field cua request la 400 INVALID_REQUEST, khong tra shape {"detail": ...} cua FastAPI
    return await handle_domain_error(request, InvalidRequestException())


async def handle_routing_error(request: Request, raised_error: Exception) -> Response:
    if not isinstance(raised_error, StarletteHTTPException):
        return respond_to_unexpected_error(request, raised_error)
    routing_code = ROUTING_ERROR_BY_STATUS.get(raised_error.status_code)
    if routing_code is None:
        # Status chua co ma on dinh trong catalog: giu hanh vi mac dinh cua FastAPI
        return await http_exception_handler(request, raised_error)
    error_response = await handle_domain_error(
        request, build_api_exception(routing_code)
    )
    router_headers = raised_error.headers or {}
    for header_name in PRESERVED_ROUTING_HEADERS:
        if header_name in router_headers:
            error_response.headers[header_name] = router_headers[header_name]
    return error_response


async def handle_unexpected_error(
    request: Request, raised_error: Exception
) -> JSONResponse:
    return respond_to_unexpected_error(request, raised_error)


def register_error_handlers(service_app: FastAPI) -> None:
    service_app.add_exception_handler(ViSignApiException, handle_domain_error)
    service_app.add_exception_handler(RequestValidationError, handle_validation_error)
    service_app.add_exception_handler(StarletteHTTPException, handle_routing_error)
    # Luoi cuoi cho loi phat sinh ngoai middleware request; duong chinh nam trong request_middleware
    service_app.add_exception_handler(Exception, handle_unexpected_error)
