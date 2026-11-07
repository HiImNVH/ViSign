# services/inference-api/src/visign_api/main.py
# Diem vao FastAPI: release tu metadata goi, CORS, middleware request, anh xa loi, registry model va router /api/v1 (T026, T060).
import logging
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from visign_api.api.error_handlers import RETRY_AFTER_HEADER, register_error_handlers
from visign_api.api.request_context import REQUEST_ID_HEADER
from visign_api.api.request_middleware import attach_request_context
from visign_api.api.router import api_v1_router
from visign_api.config import Settings, get_settings
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.coordinator import InferenceCoordinator
from visign_api.inference.gru_predictor import GruRuntime
from visign_api.inference.predictor_registry import (
    PredictorFactory,
    PredictorRegistry,
    build_predictor_factories,
)
from visign_api.observability import LOGGER_NAME, configure_logging

SERVICE_TITLE = "ViSign Inference API"
PACKAGE_NAME = "visign-api"
CORS_ALLOWED_METHODS = ["GET", "POST"]
CORS_ALLOWED_HEADERS = [REQUEST_ID_HEADER, "Content-Type"]
CORS_EXPOSED_HEADERS = [REQUEST_ID_HEADER, RETRY_AFTER_HEADER]

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]
PredictorFactories = Mapping[ArtifactKind, PredictorFactory]

service_logger = logging.getLogger(LOGGER_NAME)


def build_predictor_registry(
    runtime_settings: Settings, predictor_factories: PredictorFactories
) -> PredictorRegistry:
    predictor_registry = PredictorRegistry(predictor_factories)
    artifact_path = runtime_settings.model_artifact_path
    if artifact_path is None:
        service_logger.warning(
            "Chua cau hinh MODEL_ARTIFACT_PATH; service chay degraded"
        )
        return predictor_registry
    try:
        predictor_registry.activate(
            artifact_path, runtime_settings.feature_schema_version
        )
    except Exception as load_error:
        # Contract AI-BE: artifact loi khi khoi dong thi degraded, khong suy luan bang fixture thay the
        service_logger.error(
            "Khong nap duoc model artifact; service chay degraded", exc_info=load_error
        )
    return predictor_registry


def build_lifespan(
    runtime_settings: Settings, predictor_factories: PredictorFactories
) -> Lifespan:
    @asynccontextmanager
    async def lifespan(service_app: FastAPI) -> AsyncIterator[None]:
        # Tao coordinator trong event loop dang chay de semaphore khong gan voi loop cu
        service_app.state.settings = runtime_settings
        service_app.state.inference_coordinator = InferenceCoordinator(
            runtime_settings.inference_wait_timeout_seconds
        )
        service_app.state.predictor_registry = build_predictor_registry(
            runtime_settings, predictor_factories
        )
        yield

    return lifespan


def create_app(
    runtime_settings: Settings | None = None,
    predictor_factories: PredictorFactories | None = None,
) -> FastAPI:
    # Mac dinh: fixture + adapter GRU pilot/full; predictor_factories chi de test tiem predictor gia
    active_settings = runtime_settings or get_settings()
    active_factories = (
        build_predictor_factories(
            GruRuntime(modelDirectory=active_settings.visign_model_dir)
        )
        if predictor_factories is None
        else predictor_factories
    )
    configure_logging()
    service_app = FastAPI(
        title=SERVICE_TITLE,
        version=version(PACKAGE_NAME),
        lifespan=build_lifespan(active_settings, active_factories),
    )
    # Middleware them sau nam ngoai: CORS bao ngoai de moi response, ke ca 500, deu co header CORS
    service_app.add_middleware(BaseHTTPMiddleware, dispatch=attach_request_context)
    service_app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=active_settings.cors_allow_credentials,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
        expose_headers=CORS_EXPOSED_HEADERS,
    )
    register_error_handlers(service_app)
    service_app.include_router(api_v1_router)
    return service_app


app = create_app()
