# services/inference-api/src/visign_api/admin/dependencies.py
# Thanh phan cong cu admin (T079): pipeline inspect cua visign_ai va runner pilot cua P3; thieu thanh phan nao thi
# endpoint tuong ung tra 503 thay vi lam hong ca app. Vong doi gan vao lifespan khi co VISIGN_ADMIN_TOKEN.
import importlib
import importlib.util
import logging
from dataclasses import dataclass

from fastapi import FastAPI

from visign_api.admin.inspection import InspectionService, sweep_stale_inspections
from visign_api.admin.pilot_jobs import PilotJobManager, PilotRunner
from visign_api.config import Settings
from visign_api.inference.feature_extraction import (
    PipelineBinding,
    build_visign_ai_binding,
)
from visign_api.observability import LOGGER_NAME

# Runner pilot do P3 cung cap: module co ham build_pilot_runner() tra doi tuong theo giao dien PilotRunner
PILOT_RUNNER_MODULE = "visign_ai.pilot"
PILOT_RUNNER_FACTORY = "build_pilot_runner"

service_logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class AdminDependencies:
    inspectionPipeline: PipelineBinding | None
    pilotRunner: PilotRunner | None


def load_inspection_pipeline() -> PipelineBinding | None:
    # Can extra serving (visign_ai, MediaPipe); thieu thi inspect tra 503
    if importlib.util.find_spec("visign_ai") is None:
        return None
    try:
        return build_visign_ai_binding()
    except ImportError:
        service_logger.warning("Khong nap duoc pipeline visign_ai cho inspect")
        return None


def load_pilot_runner() -> PilotRunner | None:
    try:
        runner_module = importlib.import_module(PILOT_RUNNER_MODULE)
    except ImportError:
        return None
    build_runner = getattr(runner_module, PILOT_RUNNER_FACTORY, None)
    if not callable(build_runner):
        return None
    pilot_runner: PilotRunner = build_runner()
    return pilot_runner


def build_admin_dependencies() -> AdminDependencies:
    return AdminDependencies(
        inspectionPipeline=load_inspection_pipeline(), pilotRunner=load_pilot_runner()
    )


def install_admin_tools(
    service_app: FastAPI,
    runtime_settings: Settings,
    admin_dependencies: AdminDependencies | None,
) -> None:
    # Thu muc inspect cua tien trinh bi giet cung bi xoa truoc khi nhan request (FR-021)
    sweep_stale_inspections()
    dependencies = admin_dependencies or build_admin_dependencies()
    service_app.state.admin_inspection = InspectionService(
        dependencies.inspectionPipeline,
        runtime_settings.admin_inspect_timeout_seconds,
        runtime_settings.visign_model_dir,
    )
    workspace = runtime_settings.visign_admin_workspace
    service_app.state.pilot_jobs = (
        None
        if workspace is None
        else PilotJobManager(workspace, dependencies.pilotRunner)
    )


def close_admin_tools(service_app: FastAPI) -> None:
    pilot_jobs: PilotJobManager | None = getattr(service_app.state, "pilot_jobs", None)
    if pilot_jobs is not None:
        pilot_jobs.close()
