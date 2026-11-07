# services/inference-api/src/visign_api/inference/worker_thread.py
# Chay ham chan trong threadpool ma khong bo roi worker khi request bi huy (T050). Ca huy thuan cua asyncio
# (task.cancel khi uvicorn tat qua han) lan huy kieu anyio chi lan truyen sau khi thread xong, nen slot suy luan
# va clip tam duoc giu dung bang thoi gian worker con dung.
import asyncio
from collections.abc import Callable
from typing import Any

import anyio
from starlette.concurrency import run_in_threadpool


async def run_to_completion[ArgumentT, ResultT](
    blocking_call: Callable[[ArgumentT], ResultT], call_argument: ArgumentT
) -> ResultT:
    worker_job = asyncio.ensure_future(run_in_threadpool(blocking_call, call_argument))
    try:
        # shield: huy request khong huy future cua worker, worker van chay toi het
        return await asyncio.shield(worker_job)
    except asyncio.CancelledError:
        await wait_for_cancelled_worker(worker_job)
        raise


async def wait_for_cancelled_worker(worker_job: asyncio.Future[Any]) -> None:
    # Scope anyio che chan de huy lap lai cua anyio khong cat ngang luc cho worker
    with anyio.CancelScope(shield=True):
        await asyncio.wait({worker_job})
    # Request da huy nen ket qua/loi cua worker bi bo; doc ra de asyncio khong log "never retrieved"
    if not worker_job.cancelled():
        worker_job.exception()
