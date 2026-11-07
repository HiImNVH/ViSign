# services/inference-api/src/visign_api/api/predictions.py
# POST /api/v1/predictions: doc clip co gioi han, giu slot suy luan, chay predictor tren clip tam va ap luat quyet dinh (T038).
import logging
import time
from dataclasses import dataclass

from fastapi import APIRouter, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from visign_api.config import Settings
from visign_api.domain.errors import ClipTooLargeException, InvalidRequestException
from visign_api.domain.model_version import ModelMetadata
from visign_api.domain.prediction import PredictionResponse
from visign_api.inference.coordinator import InferenceCoordinator
from visign_api.inference.prediction_decision import decide_prediction
from visign_api.inference.predictor import RawPrediction
from visign_api.inference.predictor_registry import PredictorRegistry
from visign_api.inference.temporary_clip import open_temporary_clip
from visign_api.observability import LOGGER_NAME

MILLISECONDS_PER_SECOND = 1000

predictions_router = APIRouter()
service_logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class InferenceOutcome:
    metadata: ModelMetadata
    rawPrediction: RawPrediction


@dataclass(frozen=True)
class ResponseContext:
    requestId: str
    processingTimeMs: int


@predictions_router.post("/predictions", response_model=PredictionResponse)
async def create_prediction(request: Request, clip: UploadFile) -> PredictionResponse:
    started_at = time.perf_counter()
    runtime_settings: Settings = request.app.state.settings
    clip_bytes = await read_bounded_clip(clip, runtime_settings.max_clip_bytes)
    inference_outcome = await run_inference(request, clip_bytes)
    response_context = ResponseContext(
        requestId=request.state.request_id,
        processingTimeMs=round(
            (time.perf_counter() - started_at) * MILLISECONDS_PER_SECOND
        ),
    )
    prediction_response = build_prediction_response(inference_outcome, response_context)
    log_prediction(prediction_response)
    return prediction_response


async def read_bounded_clip(clip: UploadFile, max_clip_bytes: int) -> bytes:
    # Chi doc toi da gioi han + 1 byte: clip qua lon bi tu choi ma khong nap ca body vao RAM
    clip_bytes = await clip.read(max_clip_bytes + 1)
    if len(clip_bytes) > max_clip_bytes:
        raise ClipTooLargeException()
    if not clip_bytes:
        raise InvalidRequestException()
    return clip_bytes


async def run_inference(request: Request, clip_bytes: bytes) -> InferenceOutcome:
    predictor_registry: PredictorRegistry = request.app.state.predictor_registry
    coordinator: InferenceCoordinator = request.app.state.inference_coordinator
    # Hoi registry truoc de tra MODEL_NOT_READY ngay, khong bat request doi slot vo ich
    _ = predictor_registry.active_predictor
    async with coordinator.acquire_slot():
        active_predictor = predictor_registry.active_predictor
        # Clip tam ghi trong slot nen dia chi giu toi da mot clip; luon bi xoa du predictor loi
        with open_temporary_clip(clip_bytes) as uploaded_clip:
            raw_prediction = await run_in_threadpool(
                active_predictor.predict, uploaded_clip.path
            )
    return InferenceOutcome(
        metadata=active_predictor.metadata, rawPrediction=raw_prediction
    )


def build_prediction_response(
    inference_outcome: InferenceOutcome, response_context: ResponseContext
) -> PredictionResponse:
    raw_prediction = inference_outcome.rawPrediction
    decision = decide_prediction(
        raw_prediction, inference_outcome.metadata.acceptanceThreshold
    )
    return PredictionResponse(
        requestId=response_context.requestId,
        text=decision.text,
        classLabel=decision.classLabel,
        confidence=raw_prediction.confidence,
        accepted=decision.accepted,
        modelVersion=inference_outcome.metadata.modelVersion,
        processingTimeMs=response_context.processingTimeMs,
        timingsMs=raw_prediction.timingsMs,
        qualityHints=raw_prediction.qualityHints,
    )


def log_prediction(prediction_response: PredictionResponse) -> None:
    # Chi ghi field van hanh trong allowlist T023; khong ghi classLabel, chu hien thi hay clip
    stage_timings = (
        prediction_response.timingsMs.model_dump()
        if prediction_response.timingsMs
        else None
    )
    service_logger.info(
        "Hoan tat nhan dien",
        extra={
            "requestId": prediction_response.requestId,
            "modelVersion": prediction_response.modelVersion,
            "processingTimeMs": prediction_response.processingTimeMs,
            "timingsMs": stage_timings,
            "accepted": prediction_response.accepted,
        },
    )
