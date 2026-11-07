# services/inference-api/src/visign_api/domain/health.py
# Response GET /api/v1/health: trang thai dich vu va model dang nap (T060).
from typing import Literal

from pydantic import BaseModel

HealthStatus = Literal["ok", "degraded"]


class HealthResponse(BaseModel):
    # Khop contracts/openapi.yaml #/components/schemas/HealthResponse; modelVersion optional + nullable
    status: HealthStatus
    modelReady: bool
    modelVersion: str | None = None
