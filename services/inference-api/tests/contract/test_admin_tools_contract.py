# services/inference-api/tests/contract/test_admin_tools_contract.py
# T078: cong cu admin noi bo (contracts/admin-tools.md): tat thi 404, sai token 401 khong lo token, inspect gioi han
# byte/mot lan/timeout va don file o moi nhanh, pilot chi mot job hoat dong, loi da lam sach va lich su doc lai duoc.
import io
import json
import logging
import os
import tempfile
import threading
import time
import zipfile
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import Any

import httpx2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from visign_api.admin.dependencies import AdminDependencies
from visign_api.admin.pilot_jobs import (
    PilotInputError,
    PilotProgress,
    PreparedPilot,
    TrainedPilot,
)
from visign_api.config import Settings
from visign_api.inference.feature_extraction import PipelineBinding
from visign_api.main import create_app

FIXTURE_ARTIFACT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts" / "fixture"
)
ADMIN_TOKEN = "test-admin-token-0123456789"
WRONG_TOKEN = "wrong-admin-token-9876543210"
INSPECT_PATH = "/api/admin/inspect"
PILOT_PATH = "/api/admin/pilot"
WEBM_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm" + bytes(256)
MP4_CLIP = b"\x00\x00\x00\x18ftypmp42" + bytes(256)
TEN_GIB = str(10 * 1024**3)
WAIT_SECONDS = 10
INTERNAL_PATH = "C:\\noi-bo\\pilot\\bi-mat.csv"


class FakePipelineError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ScriptedPipeline:
    # Pipeline gia: ghi clip nhan duoc, co the cho, nem loi hoac tra ket qua co mang landmark
    def __init__(self) -> None:
        self.release = threading.Event()
        self.release.set()
        self.started = threading.Event()
        self.raised: Exception | None = None
        self.seen: list[tuple[str, bool]] = []

    def __call__(self, clip_path: Path, **options: Any) -> Mapping[str, Any]:
        self.seen.append((clip_path.suffix, clip_path.is_file()))
        self.started.set()
        assert self.release.wait(WAIT_SECONDS)
        if self.raised is not None:
            raise self.raised
        return {
            "report": {
                # Ghi ca duong dan: bao cao khong duoc lo thu muc tam cua may chu du pipeline doi cach ghi
                "sourceName": str(clip_path),
                "inputStatus": "HAS_USABLE_FRAMES",
                "featureSchemaVersion": "visign-xy-32-v0.3",
            },
            "schema": {"featureSchemaVersion": "visign-xy-32-v0.3"},
            "coords": np.zeros((4, 78, 2), dtype=np.float32),
            "point_valid": np.ones((4, 78), dtype=bool),
            "tensor": np.zeros((32, 234), dtype=np.float32),
        }


class ScriptedPilotRunner:
    # Runner gia: moi buoc cho tin hieu cua test de kiem trang thai giua chung
    def __init__(self) -> None:
        self.prepare_gate = threading.Event()
        self.train_gate = threading.Event()
        self.prepare_done = threading.Event()
        self.prepare_error: Exception | None = None
        self.accuracy = 0.5
        self.workspaces: list[Path] = []

    def prepare(self, workspace: Path, progress: PilotProgress) -> PreparedPilot:
        self.workspaces.append(workspace)
        try:
            assert self.prepare_gate.wait(WAIT_SECONDS)
            if self.prepare_error is not None:
                raise self.prepare_error
            return PreparedPilot(
                datasetVersion="pilot-giayto-nhan-v1",
                featureSchemaVersion="visign-xy-32-v0.3",
                sampleTotal=12,
                accepted=10,
            )
        finally:
            self.prepare_done.set()

    def train(self, workspace: Path, progress: PilotProgress) -> TrainedPilot:
        progress.epoch(1, 3)
        assert self.train_gate.wait(WAIT_SECONDS)
        progress.epoch(3, 3)
        progress.evaluating()
        return TrainedPilot(
            epochs=3,
            accuracy=self.accuracy,
            macroF1=0.4,
            wandbRunId="offline-run-1",
            wandbMode="offline",
            wandbUrl=None,
        )


def admin_settings(workspace: Path | None, **overrides: Any) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        model_artifact_path=FIXTURE_ARTIFACT,
        visign_admin_token=ADMIN_TOKEN,
        visign_admin_workspace=workspace,
        **overrides,
    )


def auth(token: str = ADMIN_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    api_temp_directory = tmp_path / "api-temp"
    api_temp_directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(api_temp_directory))
    return api_temp_directory


@pytest.fixture
def pipeline() -> ScriptedPipeline:
    return ScriptedPipeline()


@pytest.fixture
def runner() -> ScriptedPilotRunner:
    return ScriptedPilotRunner()


AdminClientFactory = Callable[..., TestClient]


@pytest.fixture
def admin_client(
    api_temp: Path,
    tmp_path: Path,
    pipeline: ScriptedPipeline,
    runner: ScriptedPilotRunner,
) -> Iterator[TestClient]:
    dependencies = AdminDependencies(
        inspectionPipeline=PipelineBinding(run=pipeline, errorType=FakePipelineError),
        pilotRunner=runner,
    )
    with TestClient(
        create_app(admin_settings(tmp_path / "admin"), admin_dependencies=dependencies),
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client
    # Thoat cac job dang cho de thread nen ket thuc
    runner.prepare_gate.set()
    runner.train_gate.set()
    pipeline.release.set()


def inspect(
    test_client: TestClient,
    clip_bytes: bytes = WEBM_CLIP,
    headers: dict[str, str] | None = None,
) -> httpx2.Response:
    return test_client.post(
        INSPECT_PATH,
        files={"video": ("capture.webm", clip_bytes, "video/webm")},
        headers=headers if headers is not None else auth(),
    )


def wait_until(condition: Callable[[], bool]) -> None:
    deadline = time.monotonic() + WAIT_SECONDS
    while not condition():
        assert time.monotonic() < deadline, "het thoi gian cho"
        time.sleep(0.02)


def pilot_phase(test_client: TestClient) -> str:
    phase: str = test_client.get(PILOT_PATH, headers=auth()).json()["phase"]
    return phase


# --- Bat/tat va xac thuc ---


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", PILOT_PATH),
        ("GET", f"{PILOT_PATH}/history"),
        ("POST", f"{PILOT_PATH}/prepare"),
        ("POST", f"{PILOT_PATH}/train"),
        ("POST", INSPECT_PATH),
    ],
)
def test_admin_tool_is_404_when_token_is_absent(method: str, path: str) -> None:
    disabled_settings = Settings(  # type: ignore[call-arg]
        _env_file=None, model_artifact_path=FIXTURE_ARTIFACT
    )
    with TestClient(create_app(disabled_settings)) as test_client:
        response = test_client.request(method, path, headers=auth())

    assert response.status_code == 404
    assert response.json()["code"] == "ROUTE_NOT_FOUND"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        auth(WRONG_TOKEN),
        {"Authorization": f"Basic {ADMIN_TOKEN}"},
        {"Authorization": "Bearer "},
        {"Authorization": f"Bearer {ADMIN_TOKEN}x"},
    ],
)
def test_missing_or_invalid_token_is_401_without_leaking(
    admin_client: TestClient,
    headers: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    response = admin_client.get(PILOT_PATH, headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "ADMIN_UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"
    for leaked in (ADMIN_TOKEN, WRONG_TOKEN):
        assert leaked not in response.text
        assert leaked not in caplog.text


def test_short_admin_token_is_rejected_at_startup() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, visign_admin_token="ngan-qua")  # type: ignore[call-arg]


# --- Inspect ---


def test_inspect_returns_zip_report_and_leaves_no_file(
    admin_client: TestClient, pipeline: ScriptedPipeline, api_temp: Path
) -> None:
    response = inspect(admin_client)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    assert "no-store" in response.headers["cache-control"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as report_zip:
        assert sorted(report_zip.namelist()) == ["landmarks.npz", "report.json"]
        report = json.loads(report_zip.read("report.json"))
        landmarks = np.load(io.BytesIO(report_zip.read("landmarks.npz")))
        assert sorted(landmarks.files) == ["coords", "point_valid", "tensor"]
    # Ten file tam khong lo ra bao cao; clip ton tai khi pipeline doc, bi xoa sau response
    assert report["sourceName"] == "clip.webm"
    assert report["inputStatus"] == "HAS_USABLE_FRAMES"
    assert pipeline.seen == [(".webm", True)]
    assert list(api_temp.iterdir()) == []


def test_inspect_accepts_mp4_by_signature(
    admin_client: TestClient, pipeline: ScriptedPipeline
) -> None:
    response = inspect(admin_client, MP4_CLIP)

    assert response.status_code == 200
    assert pipeline.seen == [(".mp4", True)]


def test_inspect_rejects_declared_oversized_clip_before_running(
    admin_client: TestClient, pipeline: ScriptedPipeline
) -> None:
    response = inspect(admin_client, headers={**auth(), "Content-Length": TEN_GIB})

    assert response.status_code == 413
    assert response.json()["code"] == "CLIP_TOO_LARGE"
    assert pipeline.seen == []


def test_inspect_rejects_unknown_media_without_running(
    admin_client: TestClient, pipeline: ScriptedPipeline, api_temp: Path
) -> None:
    response = inspect(admin_client, b"khong phai video")

    assert response.status_code == 415
    assert response.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert pipeline.seen == []
    assert list(api_temp.iterdir()) == []


def test_second_inspection_while_one_runs_is_409(
    admin_client: TestClient, pipeline: ScriptedPipeline, api_temp: Path
) -> None:
    pipeline.release.clear()
    first_responses: list[httpx2.Response] = []
    first = threading.Thread(
        target=lambda: first_responses.append(inspect(admin_client))
    )
    first.start()
    assert pipeline.started.wait(WAIT_SECONDS)

    second = inspect(admin_client)
    pipeline.release.set()
    first.join(WAIT_SECONDS)

    assert second.status_code == 409
    assert second.json()["code"] == "ADMIN_JOB_ACTIVE"
    assert first_responses[0].status_code == 200
    assert list(api_temp.iterdir()) == []


def test_inspection_timeout_is_504_and_worker_still_cleans_up(
    api_temp: Path, tmp_path: Path, pipeline: ScriptedPipeline
) -> None:
    pipeline.release.clear()
    dependencies = AdminDependencies(
        inspectionPipeline=PipelineBinding(run=pipeline, errorType=FakePipelineError),
        pilotRunner=None,
    )
    timeout_settings = admin_settings(
        tmp_path / "admin", admin_inspect_timeout_seconds=0.3
    )
    with TestClient(
        create_app(timeout_settings, admin_dependencies=dependencies)
    ) as test_client:
        timed_out = inspect(test_client)
        # Worker van giu luot kiem tra toi khi xong: khong chay chong
        while_running = inspect(test_client)
        pipeline.release.set()
        wait_until(lambda: not list(api_temp.iterdir()))
        wait_until(lambda: inspect(test_client).status_code == 200)

    assert timed_out.status_code == 504
    assert timed_out.json()["code"] == "ADMIN_TIMEOUT"
    assert while_running.status_code == 409
    assert list(api_temp.iterdir()) == []


@pytest.mark.parametrize(
    ("raised", "status", "code"),
    [
        (FakePipelineError("CLIP_TOO_LONG"), 422, "CLIP_TOO_LONG"),
        (RuntimeError(f"khong doc duoc {INTERNAL_PATH}"), 500, "PREDICTION_FAILED"),
    ],
)
def test_failed_inspection_returns_stable_code_and_cleans_up(
    admin_client: TestClient,
    pipeline: ScriptedPipeline,
    api_temp: Path,
    raised: Exception,
    status: int,
    code: str,
) -> None:
    pipeline.raised = raised

    response = inspect(admin_client)

    assert response.status_code == status
    assert response.json()["code"] == code
    for leaked in (INTERNAL_PATH, "Traceback", "RuntimeError"):
        assert leaked not in response.text
    assert list(api_temp.iterdir()) == []


def test_stale_inspection_directories_are_swept_at_startup(
    api_temp: Path, tmp_path: Path
) -> None:
    stale = api_temp / "visign_inspect_cu"
    fresh = api_temp / "visign_inspect_moi"
    for directory in (stale, fresh):
        directory.mkdir()
        (directory / "clip.webm").write_bytes(WEBM_CLIP)
    old_time = time.time() - 20 * 60
    os.utime(stale, (old_time, old_time))

    with TestClient(
        create_app(
            admin_settings(tmp_path / "admin"),
            admin_dependencies=AdminDependencies(None, None),
        )
    ):
        pass

    assert not stale.exists()
    assert fresh.exists()


def test_inspection_without_pipeline_is_503(api_temp: Path, tmp_path: Path) -> None:
    with TestClient(
        create_app(
            admin_settings(tmp_path / "admin"),
            admin_dependencies=AdminDependencies(None, None),
        )
    ) as test_client:
        response = inspect(test_client)

    assert response.status_code == 503
    assert response.json()["code"] == "ADMIN_UNAVAILABLE"


# --- Pilot ---


def test_pilot_starts_idle_with_empty_history(admin_client: TestClient) -> None:
    state = admin_client.get(PILOT_PATH, headers=auth())
    history = admin_client.get(f"{PILOT_PATH}/history", headers=auth())

    assert state.status_code == 200
    assert state.json()["phase"] == "idle"
    assert state.json()["runId"] is None
    assert history.json() == []


def test_single_pilot_job_runs_from_prepare_to_complete(
    admin_client: TestClient, runner: ScriptedPilotRunner
) -> None:
    started = admin_client.post(f"{PILOT_PATH}/prepare", headers=auth())
    concurrent_prepare = admin_client.post(f"{PILOT_PATH}/prepare", headers=auth())
    train_while_preparing = admin_client.post(f"{PILOT_PATH}/train", headers=auth())
    runner.prepare_gate.set()
    wait_until(lambda: pilot_phase(admin_client) == "ready")
    prepared = admin_client.get(PILOT_PATH, headers=auth()).json()
    training = admin_client.post(f"{PILOT_PATH}/train", headers=auth())
    concurrent_train = admin_client.post(f"{PILOT_PATH}/train", headers=auth())
    runner.train_gate.set()
    wait_until(lambda: pilot_phase(admin_client) == "complete")
    complete = admin_client.get(PILOT_PATH, headers=auth()).json()
    history = admin_client.get(f"{PILOT_PATH}/history", headers=auth()).json()

    assert started.status_code == 202
    assert started.json()["phase"] == "preparing"
    assert started.json()["runId"]
    for rejected in (concurrent_prepare, train_while_preparing, concurrent_train):
        assert rejected.status_code == 409
        assert rejected.json()["code"] == "ADMIN_JOB_ACTIVE"
    assert prepared["sampleTotal"] == 12 and prepared["accepted"] == 10
    assert prepared["datasetVersion"] == "pilot-giayto-nhan-v1"
    assert training.status_code == 202 and training.json()["phase"] == "training"
    assert complete["runId"] == started.json()["runId"]
    assert complete["epoch"] == 3 and complete["epochs"] == 3
    assert complete["metrics"] == {"accuracy": 0.5, "macroF1": 0.4}
    assert complete["wandbMode"] == "offline"
    assert complete["error"] is None
    assert [run["runId"] for run in history] == [complete["runId"]]
    # Moi run co thu muc rieng trong workspace, ten khong chua thong tin ca nhan
    assert runner.workspaces[0].name == complete["runId"]


def test_train_requires_a_prepared_pilot(admin_client: TestClient) -> None:
    response = admin_client.post(f"{PILOT_PATH}/train", headers=auth())

    assert response.status_code == 409
    assert response.json()["code"] == "ADMIN_PILOT_NOT_READY"


@pytest.mark.parametrize(
    "raised",
    [
        PilotInputError(f"thieu hash trong {INTERNAL_PATH}"),
        RuntimeError(f"token={ADMIN_TOKEN} tai {INTERNAL_PATH}"),
    ],
)
def test_failed_pilot_job_reports_only_a_sanitized_error(
    admin_client: TestClient, runner: ScriptedPilotRunner, raised: Exception
) -> None:
    runner.prepare_error = raised
    runner.prepare_gate.set()

    admin_client.post(f"{PILOT_PATH}/prepare", headers=auth())
    wait_until(lambda: pilot_phase(admin_client) == "failed")
    state = admin_client.get(PILOT_PATH, headers=auth())
    history = admin_client.get(f"{PILOT_PATH}/history", headers=auth())

    assert state.json()["error"]
    for response in (state, history):
        for leaked in (INTERNAL_PATH, ADMIN_TOKEN, "Traceback"):
            assert leaked not in response.text


def test_pilot_unavailable_without_runner_or_workspace(
    api_temp: Path, tmp_path: Path
) -> None:
    with TestClient(
        create_app(
            admin_settings(tmp_path / "admin"),
            admin_dependencies=AdminDependencies(None, None),
        )
    ) as without_runner:
        prepare = without_runner.post(f"{PILOT_PATH}/prepare", headers=auth())
        state = without_runner.get(PILOT_PATH, headers=auth())
    with TestClient(
        create_app(
            admin_settings(None),
            admin_dependencies=AdminDependencies(None, ScriptedPilotRunner()),
        )
    ) as without_workspace:
        no_workspace = without_workspace.get(PILOT_PATH, headers=auth())

    assert prepare.status_code == 503
    assert prepare.json()["code"] == "ADMIN_UNAVAILABLE"
    assert state.status_code == 200
    assert no_workspace.status_code == 503


def test_interrupted_run_is_failed_after_restart_and_history_persists(
    api_temp: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "admin"
    runner = ScriptedPilotRunner()
    dependencies = AdminDependencies(None, runner)
    with TestClient(
        create_app(admin_settings(workspace), admin_dependencies=dependencies)
    ) as first_process:
        started = first_process.post(f"{PILOT_PATH}/prepare", headers=auth()).json()
    # Tien trinh cu da dung khi job dang chay; worker cu chay xong muon khong duoc ghi de trang thai
    runner.prepare_gate.set()
    assert runner.prepare_done.wait(WAIT_SECONDS)

    with TestClient(
        create_app(
            admin_settings(workspace),
            admin_dependencies=AdminDependencies(None, ScriptedPilotRunner()),
        )
    ) as second_process:
        state = second_process.get(PILOT_PATH, headers=auth()).json()
        history = second_process.get(f"{PILOT_PATH}/history", headers=auth()).json()

    assert state["runId"] == started["runId"]
    assert state["phase"] == "failed"
    assert state["error"]
    assert [run["runId"] for run in history] == [started["runId"]]


def test_run_left_active_by_a_crash_is_failed_on_startup(
    api_temp: Path, tmp_path: Path
) -> None:
    # Tien trinh bi giet cung: khong chay lifespan close, file trang thai van ghi training
    runs_directory = tmp_path / "admin" / "runs"
    runs_directory.mkdir(parents=True)
    crashed_run = {
        "runId": "pilot-20261108-010000-abc123",
        "phase": "training",
        "sampleTotal": 12,
        "accepted": 10,
        "updatedAt": "2026-11-08T01:00:00Z",
    }
    (runs_directory / f"{crashed_run['runId']}.json").write_text(
        json.dumps(crashed_run), encoding="utf-8"
    )

    with TestClient(
        create_app(
            admin_settings(tmp_path / "admin"),
            admin_dependencies=AdminDependencies(None, ScriptedPilotRunner()),
        )
    ) as restarted:
        state = restarted.get(PILOT_PATH, headers=auth()).json()

    assert state["runId"] == crashed_run["runId"]
    assert state["phase"] == "failed"
    assert state["error"]


def test_invalid_runner_result_fails_the_run_instead_of_hanging(
    admin_client: TestClient, runner: ScriptedPilotRunner
) -> None:
    # Runner tra metric ngoai [0, 1]: run thanh failed, khong ket o training sau khi thread loi
    runner.accuracy = 2.0
    runner.prepare_gate.set()
    runner.train_gate.set()
    admin_client.post(f"{PILOT_PATH}/prepare", headers=auth())
    wait_until(lambda: pilot_phase(admin_client) == "ready")

    admin_client.post(f"{PILOT_PATH}/train", headers=auth())
    wait_until(lambda: pilot_phase(admin_client) in {"failed", "complete"})

    assert pilot_phase(admin_client) == "failed"
