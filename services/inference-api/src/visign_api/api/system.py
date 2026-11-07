# services/inference-api/src/visign_api/api/system.py
# GET /api/v1/health va /api/v1/model-info: cong bo trang thai san sang va metadata artifact dang phuc vu (T060).
from fastapi import APIRouter, Request, Response

from visign_api.domain.health import HealthResponse
from visign_api.domain.model_version import ModelInfoResponse
from visign_api.inference.predictor_registry import PredictorRegistry

# Health luon phan anh trang thai hien tai, khong de proxy/trinh duyet cache (quy uoc API muc 3)
HEALTH_CACHE_CONTROL = "no-store"

system_router = APIRouter()


def predictor_registry_of(request: Request) -> PredictorRegistry:
    active_registry: PredictorRegistry = request.app.state.predictor_registry
    return active_registry


@system_router.get("/health", response_model=HealthResponse)
async def get_health(request: Request, response: Response) -> HealthResponse:
    response.headers["Cache-Control"] = HEALTH_CACHE_CONTROL
    predictor_registry = predictor_registry_of(request)
    if not predictor_registry.is_ready:
        return HealthResponse(status="degraded", modelReady=False, modelVersion=None)
    active_metadata = predictor_registry.active_predictor.metadata
    return HealthResponse(
        status="ok", modelReady=True, modelVersion=active_metadata.modelVersion
    )


@system_router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info(request: Request) -> ModelInfoResponse:
    # Chua co predictor thi active_predictor raise MODEL_NOT_READY (503 kem Retry-After)
    active_metadata = predictor_registry_of(request).active_predictor.metadata
    return ModelInfoResponse.from_metadata(active_metadata)
