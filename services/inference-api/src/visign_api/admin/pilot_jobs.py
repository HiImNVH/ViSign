# services/inference-api/src/visign_api/admin/pilot_jobs.py
# Job pilot noi bo (T079, FR-022): chi mot job o preparing/training/evaluating; trang thai TrainingRun luu theo runId
# trong workspace local; loi chi tra thong bao on dinh. Job dang do khi tien trinh dung thi thanh failed.
import logging
import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from visign_api.admin.errors import (
    ADMIN_JOB_ACTIVE,
    ADMIN_PILOT_NOT_READY,
    ADMIN_UNAVAILABLE,
    AdminApiException,
)
from visign_api.observability import LOGGER_NAME

PilotPhase = Literal[
    "idle", "preparing", "ready", "training", "evaluating", "complete", "failed"
]
WandbMode = Literal["online", "offline"]
ACTIVE_PHASES = frozenset({"preparing", "training", "evaluating"})
RUNS_DIRECTORY = "runs"
RUN_STATE_SUFFIX = ".json"
INPUT_ERROR_MESSAGE = (
    "Bản bàn giao pilot không đạt kiểm tra; xem báo cáo trong workspace."
)
FAILURE_MESSAGE = "Công việc pilot thất bại; xem log máy chủ."
INTERRUPTED_MESSAGE = "Tiến trình API dừng khi công việc pilot đang chạy."

service_logger = logging.getLogger(LOGGER_NAME)


def utc_now() -> datetime:
    return datetime.now(UTC)


class PilotMetrics(BaseModel):
    accuracy: float | None = Field(default=None, ge=0, le=1)
    macroF1: float | None = Field(default=None, ge=0, le=1)


class TrainingRun(BaseModel):
    # data-model.md TrainingRun; error chi la thong bao on dinh, khong co duong dan hay traceback
    runId: str | None
    phase: PilotPhase
    datasetVersion: str | None = None
    featureSchemaVersion: str | None = None
    sampleTotal: int = Field(default=0, ge=0)
    accepted: int = Field(default=0, ge=0)
    epoch: int | None = None
    epochs: int | None = None
    metrics: PilotMetrics | None = None
    wandbRunId: str | None = None
    wandbMode: WandbMode | None = None
    wandbUrl: str | None = None
    updatedAt: datetime
    error: str | None = None


class PilotInputError(ValueError):
    """Ban ban giao pilot khong dat kiem tra (hash, manifest, schema, coverage)."""


@dataclass(frozen=True)
class PreparedPilot:
    datasetVersion: str
    featureSchemaVersion: str
    sampleTotal: int
    accepted: int


@dataclass(frozen=True)
class TrainedPilot:
    epochs: int
    accuracy: float | None
    macroF1: float | None
    wandbRunId: str | None
    wandbMode: WandbMode | None
    wandbUrl: str | None


class PilotProgress:
    # Runner bao tien do; job manager doi thanh trang thai doc lai duoc qua GET /pilot
    def __init__(
        self,
        on_epoch: Callable[[int, int], None],
        on_evaluating: Callable[[], None],
    ) -> None:
        self._on_epoch = on_epoch
        self._on_evaluating = on_evaluating

    def epoch(self, done: int, total: int) -> None:
        self._on_epoch(done, total)

    def evaluating(self) -> None:
        self._on_evaluating()


class PilotRunner(Protocol):
    # Phan train/evaluate thuoc P3; API chi dieu phoi, khoa job va luu trang thai
    def prepare(self, workspace: Path, progress: PilotProgress) -> PreparedPilot: ...

    def train(self, workspace: Path, progress: PilotProgress) -> TrainedPilot: ...


def new_run_id(created_at: datetime) -> str:
    # Ngau nhien, khong chua ten nguoi hay secret
    return f"pilot-{created_at:%Y%m%d-%H%M%S}-{secrets.token_hex(3)}"


class PilotJobManager:
    def __init__(
        self,
        workspace: Path,
        runner: PilotRunner | None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._runs_directory = workspace / RUNS_DIRECTORY
        self._runs_directory.mkdir(parents=True, exist_ok=True)
        self._runner = runner
        self._clock = clock
        self._lock = threading.Lock()
        self._closed = False
        self._current = self._recover_latest_run()

    def current(self) -> TrainingRun:
        with self._lock:
            return self._current

    def history(self) -> list[TrainingRun]:
        stored_runs = []
        for state_path in self._runs_directory.glob(f"*{RUN_STATE_SUFFIX}"):
            try:
                stored_runs.append(
                    TrainingRun.model_validate_json(state_path.read_bytes())
                )
            except (OSError, ValidationError):
                continue
        return sorted(stored_runs, key=lambda run: run.updatedAt, reverse=True)

    def prepare(self) -> TrainingRun:
        runner = self._require_runner()
        with self._lock:
            if self._current.phase in ACTIVE_PHASES:
                raise AdminApiException(ADMIN_JOB_ACTIVE)
            created_at = self._clock()
            preparing = TrainingRun(
                runId=new_run_id(created_at), phase="preparing", updatedAt=created_at
            )
            self._replace_locked(preparing)
        self._start(lambda run_id: self._run_prepare(runner, run_id), preparing)
        return preparing

    def train(self) -> TrainingRun:
        runner = self._require_runner()
        with self._lock:
            if self._current.phase in ACTIVE_PHASES:
                raise AdminApiException(ADMIN_JOB_ACTIVE)
            if self._current.phase != "ready":
                raise AdminApiException(ADMIN_PILOT_NOT_READY)
            training = self._current.model_copy(
                update={"phase": "training", "epoch": None, "updatedAt": self._clock()}
            )
            self._replace_locked(training)
        self._start(lambda run_id: self._run_train(runner, run_id), training)
        return training

    def close(self) -> None:
        # Tat app: job dang chay thanh failed ngay; cap nhat ve sau cua worker cu bi bo qua
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._current.phase in ACTIVE_PHASES:
                self._persist(self._interrupted(self._current))

    def _require_runner(self) -> PilotRunner:
        if self._runner is None:
            raise AdminApiException(ADMIN_UNAVAILABLE)
        return self._runner

    def _start(self, job: Callable[[str], None], run: TrainingRun) -> None:
        run_id = run.runId
        assert run_id is not None
        # Thread daemon: train dai khong giu tien trinh song khi tat; trang thai da ghi failed o close()
        threading.Thread(
            target=job, args=(run_id,), name="visign-pilot", daemon=True
        ).start()

    def _run_prepare(self, runner: PilotRunner, run_id: str) -> None:
        # Kiem ket qua cua runner trong cung khoi try: gia tri sai cung thanh failed, run khong ket o preparing
        try:
            prepared = runner.prepare(
                self._run_directory(run_id), self._progress(run_id)
            )
            sample_total = max(int(prepared.sampleTotal), 0)
            ready_changes = {
                "phase": "ready",
                "datasetVersion": str(prepared.datasetVersion),
                "featureSchemaVersion": str(prepared.featureSchemaVersion),
                "sampleTotal": sample_total,
                "accepted": min(max(int(prepared.accepted), 0), sample_total),
            }
        except Exception as job_error:  # noqa: BLE001 - loi cua runner thanh failed, thread khong chet im
            self._fail(run_id, job_error)
            return
        self._update(run_id, **ready_changes)

    def _run_train(self, runner: PilotRunner, run_id: str) -> None:
        try:
            trained = runner.train(self._run_directory(run_id), self._progress(run_id))
            epochs = int(trained.epochs)
            complete_changes = {
                "phase": "complete",
                "epochs": epochs,
                "metrics": PilotMetrics(
                    accuracy=trained.accuracy, macroF1=trained.macroF1
                ),
                "wandbRunId": trained.wandbRunId,
                "wandbMode": trained.wandbMode
                if trained.wandbMode in ("online", "offline")
                else None,
                "wandbUrl": trained.wandbUrl,
            }
        except Exception as job_error:  # noqa: BLE001 - loi cua runner thanh failed, thread khong chet im
            self._fail(run_id, job_error)
            return
        with self._lock:
            reported_epoch = self._current.epoch
        complete_changes["epoch"] = (
            reported_epoch if reported_epoch is not None else epochs
        )
        self._update(run_id, **complete_changes)

    def _progress(self, run_id: str) -> PilotProgress:
        def record_epoch(done: int, total: int) -> None:
            self._update(run_id, epoch=max(int(done), 0), epochs=max(int(total), 1))

        return PilotProgress(
            on_epoch=record_epoch,
            on_evaluating=lambda: self._update(run_id, phase="evaluating"),
        )

    def _fail(self, run_id: str, job_error: Exception) -> None:
        # Chi tiet (co the chua duong dan) nam o log may chu; client chi thay thong bao on dinh
        service_logger.error("Job pilot that bai", exc_info=job_error)
        message = (
            INPUT_ERROR_MESSAGE
            if isinstance(job_error, PilotInputError)
            else FAILURE_MESSAGE
        )
        self._update(run_id, phase="failed", error=message)

    def _update(self, run_id: str, **changes: Any) -> None:
        with self._lock:
            if self._closed or self._current.runId != run_id:
                return
            self._replace_locked(
                self._current.model_copy(update={**changes, "updatedAt": self._clock()})
            )

    def _replace_locked(self, run: TrainingRun) -> None:
        self._current = run
        self._persist(run)

    def _persist(self, run: TrainingRun) -> None:
        if run.runId is None:
            return
        state_path = self._runs_directory / f"{run.runId}{RUN_STATE_SUFFIX}"
        staging_path = state_path.with_suffix(".tmp")
        staging_path.write_text(run.model_dump_json(), encoding="utf-8")
        staging_path.replace(state_path)

    def _run_directory(self, run_id: str) -> Path:
        run_directory = self._runs_directory / run_id
        run_directory.mkdir(exist_ok=True)
        return run_directory

    def _interrupted(self, run: TrainingRun) -> TrainingRun:
        return run.model_copy(
            update={
                "phase": "failed",
                "error": INTERRUPTED_MESSAGE,
                "updatedAt": self._clock(),
            }
        )

    def _recover_latest_run(self) -> TrainingRun:
        stored_runs = self.history()
        if not stored_runs:
            return TrainingRun(runId=None, phase="idle", updatedAt=self._clock())
        latest = stored_runs[0]
        if latest.phase in ACTIVE_PHASES:
            # Worker cua tien trinh truoc khong con: job dang do khong the tiep tuc
            latest = self._interrupted(latest)
            self._persist(latest)
        return latest
