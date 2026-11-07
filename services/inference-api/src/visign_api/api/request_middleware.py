# services/inference-api/src/visign_api/api/request_middleware.py
# Middleware gan X-Request-ID, ghi mot dong access log va doi loi bat ngo thanh 500 ben trong CORS (T026).
import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from visign_api.api.error_handlers import respond_to_unexpected_error
from visign_api.api.request_context import REQUEST_ID_HEADER, resolve_request_id
from visign_api.observability import LOGGER_NAME

MILLISECONDS_PER_SECOND = 1000

service_logger = logging.getLogger(LOGGER_NAME)


async def attach_request_context(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as unexpected_error:  # noqa: BLE001 - luoi an toan duy nhat giu header CORS cho loi 500
        # Bat o day thay vi de ServerErrorMiddleware xu ly, vi response tu lop ngoai cung khong co header CORS
        response = respond_to_unexpected_error(request, unexpected_error)
    response.headers[REQUEST_ID_HEADER] = request_id
    log_completed_request(request, response, started_at)
    return response


def log_completed_request(
    request: Request, response: Response, started_at: float
) -> None:
    elapsed_ms = round((time.perf_counter() - started_at) * MILLISECONDS_PER_SECOND)
    service_logger.info(
        "Hoan tat request",
        extra={
            "requestId": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
            "statusCode": response.status_code,
            "processingTimeMs": elapsed_ms,
        },
    )
