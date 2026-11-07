# services/inference-api/src/visign_api/domain/request_id.py
# Kiem tra request correlation ID dung dinh dang UUID theo header X-Request-ID.
from uuid import UUID


def ensure_uuid(request_id: str) -> None:
    try:
        UUID(request_id)
    except (ValueError, TypeError) as invalid_uuid:
        raise ValueError(
            f"requestId khong phai UUID hop le: {request_id}"
        ) from invalid_uuid
