# services/inference-api/src/visign_api/api/router.py
# Router cong khai /api/v1; endpoint health/model-info (T060) va predictions (T038) gan vao day.
from fastapi import APIRouter

from visign_api.api.predictions import predictions_router
from visign_api.api.system import system_router

API_V1_PREFIX = "/api/v1"

api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(system_router)
api_v1_router.include_router(predictions_router)
