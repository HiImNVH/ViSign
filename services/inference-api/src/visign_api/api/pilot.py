# services/inference-api/src/visign_api/api/pilot.py
# /api/admin/pilot (T079-T080, contracts/admin-tools.md): doc trang thai va lich su TrainingRun; prepare/train tra 202
# kem TrainingRun, tu choi 409 khi co job dang chay, 503 khi chua cau hinh workspace hoac runner.
from fastapi import APIRouter, Request, status

from visign_api.admin.errors import ADMIN_UNAVAILABLE, AdminApiException
from visign_api.admin.pilot_jobs import PilotJobManager, TrainingRun

pilot_router = APIRouter(prefix="/pilot")


def pilot_jobs(request: Request) -> PilotJobManager:
    job_manager: PilotJobManager | None = request.app.state.pilot_jobs
    if job_manager is None:
        raise AdminApiException(ADMIN_UNAVAILABLE)
    return job_manager


@pilot_router.get("", response_model=TrainingRun)
def read_pilot(request: Request) -> TrainingRun:
    return pilot_jobs(request).current()


@pilot_router.get("/history", response_model=list[TrainingRun])
def read_pilot_history(request: Request) -> list[TrainingRun]:
    return pilot_jobs(request).history()


@pilot_router.post(
    "/prepare", status_code=status.HTTP_202_ACCEPTED, response_model=TrainingRun
)
def prepare_pilot(request: Request) -> TrainingRun:
    return pilot_jobs(request).prepare()


@pilot_router.post(
    "/train", status_code=status.HTTP_202_ACCEPTED, response_model=TrainingRun
)
def train_pilot(request: Request) -> TrainingRun:
    return pilot_jobs(request).train()
