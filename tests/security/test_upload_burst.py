# tests/security/test_upload_burst.py
# Audit T092 (ghi chu T024-T025): mot dot upload dong thoi; trong luc tai dia chi giu dung mot clip tam (cua request
# dang suy luan), cac request phai cho slot nhan 503 va khong de lai file nao sau khi xong.
import tempfile
import threading
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx2
import pytest
from fastapi.testclient import TestClient
from visign_api.config import Settings
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.domain.prediction import PredictionQualityHints, PredictionTimings
from visign_api.inference.artifact_loader import LoadedArtifact
from visign_api.inference.predictor import RawPrediction
from visign_api.inference.predictor_registry import PredictorFactory
from visign_api.main import create_app

FIXTURE_ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "inference-api"
    / "tests"
    / "fixtures"
    / "model-artifacts"
    / "fixture"
)
PREDICTIONS_PATH = "/api/v1/predictions"
WEBM_MEDIA_TYPE = "video/webm;codecs=vp8"
# 1,5 MiB: vuot nguong 1 MiB cua parser multipart nen file spool cung duoc ghi xuong thu muc tam
BURST_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm" + bytes(
    3 * 1024 * 1024 // 2
)
BUSY_REQUEST_COUNT = 11
SLOT_WAIT_SECONDS = 0.5
SAMPLE_INTERVAL_SECONDS = 0.005
BURST_DEADLINE_SECONDS = 10
ACCEPTED_PREDICTION = RawPrediction(
    classLabel="SOT_HCM_1",
    displayText="Sốt",
    confidence=0.91,
    timingsMs=PredictionTimings(decode=10, extract=900, infer=5),
    qualityHints=PredictionQualityHints(handsDetectedRatio=0.5, frameCount=46),
)


class BlockingPredictor:
    # Giu slot cho toi khi test cho phep, de cac request con lai chac chan phai cho slot
    def __init__(
        self,
        loaded_artifact: LoadedArtifact,
        started: threading.Event,
        release: threading.Event,
    ) -> None:
        self._loaded_artifact = loaded_artifact
        self._started = started
        self._release = release

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        self._started.set()
        self._release.wait(timeout=10)
        return ACCEPTED_PREDICTION


def blocking_factories(
    started: threading.Event, release: threading.Event
) -> Mapping[ArtifactKind, PredictorFactory]:
    def build_blocking(loaded_artifact: LoadedArtifact) -> BlockingPredictor:
        return BlockingPredictor(loaded_artifact, started, release)

    return {kind: build_blocking for kind in ArtifactKind}


def post_burst_clip(test_client: TestClient) -> httpx2.Response:
    return test_client.post(
        PREDICTIONS_PATH,
        files={"clip": ("capture.webm", BURST_CLIP, WEBM_MEDIA_TYPE)},
    )


def count_clips(directory: Path) -> int:
    return len(list(directory.glob("visign_clip_*")))


def test_upload_burst_keeps_one_clip_on_disk_and_leaves_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api_temp = tmp_path / "api-temp"
    api_temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(api_temp))
    started, release = threading.Event(), threading.Event()
    burst_settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        model_artifact_path=FIXTURE_ARTIFACT,
        inference_wait_timeout_seconds=SLOT_WAIT_SECONDS,
    )

    with (
        TestClient(
            create_app(burst_settings, blocking_factories(started, release))
        ) as burst_client,
        ThreadPoolExecutor(max_workers=BUSY_REQUEST_COUNT + 1) as request_pool,
    ):
        active_request = request_pool.submit(post_burst_clip, burst_client)
        assert started.wait(timeout=10)
        busy_requests = [
            request_pool.submit(post_burst_clip, burst_client)
            for _ in range(BUSY_REQUEST_COUNT)
        ]
        # Co han chot: neu hoi quy lam request cho slot mai mai, test bao loi thay vi treo
        deadline = time.monotonic() + BURST_DEADLINE_SECONDS
        clip_counts = [count_clips(api_temp)]
        while (
            not all(busy_request.done() for busy_request in busy_requests)
            and time.monotonic() < deadline
        ):
            time.sleep(SAMPLE_INTERVAL_SECONDS)
            clip_counts.append(count_clips(api_temp))
        release.set()
        busy_responses = [busy_request.result() for busy_request in busy_requests]
        active_response = active_request.result()

    assert [response.status_code for response in busy_responses] == [
        503
    ] * BUSY_REQUEST_COUNT
    assert {response.json()["code"] for response in busy_responses} == {"SERVICE_BUSY"}
    assert active_response.status_code == 200
    # Clip chi duoc ghi khi da giu slot: suot dot tai chi co clip cua request dang suy luan
    assert set(clip_counts) == {1}
    # Sau dot tai: khong con clip tam hay file spool multipart nao
    assert list(api_temp.iterdir()) == []
