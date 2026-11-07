# services/inference-api/src/visign_api/domain/prediction.py
# Response prediction voi trang thai accepted/rejected khong the ket hop sai (T020).
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from visign_api.domain.request_id import ensure_uuid

OPTIONAL_DIAGNOSTIC_FIELDS = ("timingsMs", "qualityHints")


class PredictionTimings(BaseModel):
    # Cam field la de chan landmark/frame lot vao response chan doan (FR-019)
    model_config = ConfigDict(extra="forbid")

    decode: int = Field(ge=0)
    extract: int = Field(ge=0)
    infer: int = Field(ge=0)


class PredictionQualityHints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handsDetectedRatio: float = Field(ge=0.0, le=1.0)
    frameCount: int = Field(ge=1)


class PredictionResponse(BaseModel):
    # Khop contracts/openapi.yaml #/components/schemas/PredictionResponse
    requestId: str
    text: str
    classLabel: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    accepted: bool
    modelVersion: str
    processingTimeMs: int = Field(ge=0)
    timingsMs: PredictionTimings | None = None
    qualityHints: PredictionQualityHints | None = None

    @model_validator(mode="after")
    def validate_state_consistency(self) -> "PredictionResponse":
        ensure_uuid(self.requestId)
        if self.accepted:
            ensure_accepted_state(self)
        elif self.classLabel is not None:
            raise ValueError("PredictionResponse bi tu choi phai co classLabel = null")
        return self

    # Khong ghi kieu tra ve de FastAPI giu schema OpenAPI cua model thay vi dict tu do
    @model_serializer(mode="wrap")
    def omit_absent_diagnostics(self, handler: SerializerFunctionWrapHandler):  # type: ignore[no-untyped-def]
        # openapi.yaml cho phep bo qua chan doan nhung khong cho phep gia tri null
        serialized_response: dict[str, Any] = handler(self)
        for diagnostic_field in OPTIONAL_DIAGNOSTIC_FIELDS:
            if serialized_response.get(diagnostic_field) is None:
                serialized_response.pop(diagnostic_field, None)
        return serialized_response


def ensure_accepted_state(accepted_response: PredictionResponse) -> None:
    if not accepted_response.text.strip():
        raise ValueError("PredictionResponse duoc chap nhan phai co text tieng Viet")
    if not accepted_response.classLabel:
        raise ValueError("PredictionResponse duoc chap nhan phai co classLabel")
