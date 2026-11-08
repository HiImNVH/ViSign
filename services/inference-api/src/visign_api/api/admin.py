# services/inference-api/src/visign_api/api/admin.py
# Router /api/admin cua cong cu noi bo (T079-T080): chi gan khi co VISIGN_ADMIN_TOKEN; moi request phai co Bearer
# token dung (so sanh hang thoi gian, khong log). Inspect nhan multipart "video" va tra ZIP bao cao.
import hmac

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import Response

from visign_api.admin.errors import ADMIN_UNAUTHORIZED, AdminApiException
from visign_api.admin.inspection import InspectionService
from visign_api.api.clip_upload_route import ClipUploadRoute
from visign_api.api.pilot import pilot_router
from visign_api.api.predictions import read_bounded_clip
from visign_api.config import Settings

ADMIN_PREFIX = "/api/admin"
BEARER_PREFIX = "Bearer "
REPORT_FILENAME = "visign-inspect.zip"


def require_admin_token(request: Request) -> None:
    runtime_settings: Settings = request.app.state.settings
    expected_token = runtime_settings.visign_admin_token
    authorization = request.headers.get("authorization", "")
    # RFC 7235: ten scheme khong phan biet hoa/thuong (T112); token van so sanh chinh xac
    scheme, _, provided_token = authorization.partition(" ")
    if expected_token is None or scheme.lower() != BEARER_PREFIX.strip().lower():
        raise AdminApiException(ADMIN_UNAUTHORIZED)
    if not hmac.compare_digest(
        provided_token.encode(), expected_token.get_secret_value().encode()
    ):
        raise AdminApiException(ADMIN_UNAUTHORIZED)


# Route class chung voi /predictions: chan body qua 10 MiB theo Content-Length truoc khi parse multipart
inspect_router = APIRouter(route_class=ClipUploadRoute)


@inspect_router.post("/inspect", response_class=Response)
async def inspect_clip(request: Request, video: UploadFile) -> Response:
    runtime_settings: Settings = request.app.state.settings
    clip_bytes = await read_bounded_clip(video, runtime_settings.max_clip_bytes)
    inspection: InspectionService = request.app.state.admin_inspection
    report_zip = await inspection.inspect(clip_bytes)
    return Response(
        content=report_zip,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{REPORT_FILENAME}"'},
    )


admin_router = APIRouter(
    prefix=ADMIN_PREFIX, dependencies=[Depends(require_admin_token)]
)
admin_router.include_router(inspect_router)
admin_router.include_router(pilot_router)
