# services/inference-api/tests/unit/test_prediction_cleanup.py
# T050: huy request giua luc suy luan khong duoc tra slot som (2 luot suy luan song song, vuot RAM)
# hay xoa clip tam khi worker con doc; ca hai chi duoc tra sau khi worker xong.
import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import Request
from visign_api.api.predictions import run_inference
from visign_api.domain.errors import ServiceBusyException
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.inference.artifact_loader import LoadedArtifact
from visign_api.inference.coordinator import InferenceCoordinator
from visign_api.inference.predictor import RawPrediction
from visign_api.inference.predictor_registry import PredictorRegistry

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
SAMPLE_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm cleanup clip"
WORKER_WAIT_SECONDS = 5
SETTLE_SECONDS = 0.2
SLOT_PROBE_TIMEOUT_SECONDS = 0.1


class WorkerGate:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.seen_paths: list[Path] = []
        self.clip_existed_at_end: bool | None = None


class BlockingPredictor:
    def __init__(
        self, loaded_artifact: LoadedArtifact, worker_gate: WorkerGate
    ) -> None:
        self._loaded_artifact = loaded_artifact
        self._worker_gate = worker_gate

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        self._worker_gate.seen_paths.append(clip_path)
        self._worker_gate.started.set()
        self._worker_gate.release.wait(WORKER_WAIT_SECONDS)
        self._worker_gate.clip_existed_at_end = clip_path.exists()
        return RawPrediction(
            classLabel="CAM_ON_HN_1",
            displayText="Cảm ơn",
            confidence=0.9,
            timingsMs=None,
            qualityHints=None,
        )


def blocking_registry(worker_gate: WorkerGate) -> PredictorRegistry:
    def build_blocking(loaded_artifact: LoadedArtifact) -> BlockingPredictor:
        return BlockingPredictor(loaded_artifact, worker_gate)

    predictor_registry = PredictorRegistry({ArtifactKind.FIXTURE: build_blocking})
    predictor_registry.activate(FIXTURE_ARTIFACTS / "fixture", None)
    return predictor_registry


def request_with(
    predictor_registry: PredictorRegistry, coordinator: InferenceCoordinator
) -> Request:
    app_state = SimpleNamespace(
        predictor_registry=predictor_registry, inference_coordinator=coordinator
    )
    return cast(Request, SimpleNamespace(app=SimpleNamespace(state=app_state)))


async def slot_is_free(coordinator: InferenceCoordinator) -> bool:
    try:
        async with coordinator.acquire_slot():
            return True
    except ServiceBusyException:
        return False


async def wait_until(worker_event: threading.Event) -> None:
    while not worker_event.is_set():
        await asyncio.sleep(0.01)


def test_cancelled_request_keeps_slot_and_clip_until_worker_finishes() -> None:
    worker_gate = WorkerGate()
    predictor_registry = blocking_registry(worker_gate)
    observations: dict[str, Any] = {}

    async def scenario() -> None:
        coordinator = InferenceCoordinator(SLOT_PROBE_TIMEOUT_SECONDS)
        inference_task = asyncio.ensure_future(
            run_inference(request_with(predictor_registry, coordinator), SAMPLE_CLIP)
        )
        await wait_until(worker_gate.started)
        inference_task.cancel()
        await asyncio.sleep(SETTLE_SECONDS)
        observations["request-left-early"] = inference_task.done()
        observations["clip-kept"] = worker_gate.seen_paths[0].exists()
        observations["slot-free-while-worker-runs"] = await slot_is_free(coordinator)
        worker_gate.release.set()
        with pytest.raises(asyncio.CancelledError):
            await inference_task
        observations["slot-free-after-worker"] = await slot_is_free(coordinator)

    asyncio.run(scenario())

    assert observations == {
        "request-left-early": False,
        "clip-kept": True,
        "slot-free-while-worker-runs": False,
        "slot-free-after-worker": True,
    }
    assert worker_gate.clip_existed_at_end is True
    assert not worker_gate.seen_paths[0].exists()
