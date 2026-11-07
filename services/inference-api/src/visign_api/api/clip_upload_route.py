# services/inference-api/src/visign_api/api/clip_upload_route.py
# Route class cho POST /predictions (T049): chan body vuot gioi han theo Content-Length truoc khi FastAPI parse
# multipart va dem byte thuc nhan cho request chunked; loi mien bi FastAPI boc thanh 400 duoc tra lai dung ma.
from collections.abc import Callable, Coroutine
from http import HTTPStatus
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute

# fastapi.routing nem HTTPException cua Starlette (lop cha), khong phai lop con cua FastAPI
from starlette.exceptions import HTTPException
from starlette.types import Message, Receive

from visign_api.config import Settings
from visign_api.domain.errors import (
    ClipTooLargeException,
    InvalidRequestException,
    ViSignApiException,
)
from visign_api.inference.clip_validator import (
    ensure_declared_length_within_limit,
    max_upload_body_bytes,
)

CONTENT_LENGTH_HEADER = "content-length"
HTTP_REQUEST_MESSAGE = "http.request"

RouteHandler = Callable[[Request], Coroutine[Any, Any, Response]]


class BoundedBodyReceive:
    # Dem byte body da nhan: vuot gioi han thi dung doc ngay, multipart khong spool phan con lai ra dia
    def __init__(self, receive: Receive, max_body_bytes: int) -> None:
        self._receive = receive
        self._max_body_bytes = max_body_bytes
        self._received_bytes = 0

    async def __call__(self) -> Message:
        message = await self._receive()
        if message["type"] == HTTP_REQUEST_MESSAGE:
            self._received_bytes += len(message.get("body", b""))
            if self._received_bytes > self._max_body_bytes:
                raise ClipTooLargeException()
        return message


class ClipUploadRoute(APIRoute):
    def get_route_handler(self) -> RouteHandler:
        parse_and_handle = super().get_route_handler()

        async def guarded_handler(request: Request) -> Response:
            runtime_settings: Settings = request.app.state.settings
            max_body_bytes = max_upload_body_bytes(runtime_settings.max_clip_bytes)
            # Kiem header truoc khi doc byte nao: client khai 10 GiB bi tu choi ngay
            ensure_declared_length_within_limit(
                request.headers.get(CONTENT_LENGTH_HEADER), max_body_bytes
            )
            bounded_request = Request(
                request.scope, BoundedBodyReceive(request.receive, max_body_bytes)
            )
            try:
                return await parse_and_handle(bounded_request)
            except HTTPException as body_error:
                # FastAPI boc moi loi khi doc form thanh HTTPException 400; loi mien goc nam o __cause__
                if isinstance(body_error.__cause__, ViSignApiException):
                    raise body_error.__cause__ from None
                if body_error.status_code == HTTPStatus.BAD_REQUEST:
                    # T050: multipart hong tra ErrorEnvelope INVALID_REQUEST, khong lo {"detail": ...}
                    raise InvalidRequestException() from body_error
                raise

        return guarded_handler
