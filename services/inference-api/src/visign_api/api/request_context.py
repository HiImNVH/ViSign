# services/inference-api/src/visign_api/api/request_context.py
# Xac dinh request correlation ID: nhan UUID hop le tu header X-Request-ID, tao moi khi thieu hoac sai.
import uuid

from fastapi import Request

REQUEST_ID_HEADER = "X-Request-ID"


def resolve_request_id(raw_request_id: str | None) -> str:
    if raw_request_id:
        try:
            return str(uuid.UUID(raw_request_id))
        except ValueError:
            # Gia tri sai dinh dang khong lam hong request; server thay bang UUID moi theo quy uoc API
            return str(uuid.uuid4())
    return str(uuid.uuid4())


def get_request_id(request: Request) -> str:
    stored_request_id: str | None = getattr(request.state, "request_id", None)
    return stored_request_id or resolve_request_id(
        request.headers.get(REQUEST_ID_HEADER)
    )
