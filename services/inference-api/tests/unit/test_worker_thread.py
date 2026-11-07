# services/inference-api/tests/unit/test_worker_thread.py
# T050: request bi huy khong duoc bo roi thread suy luan; ham chi tra quyen dieu khien khi worker da xong.
import asyncio
import gc
import threading
from collections.abc import Callable, Coroutine
from typing import Any

import anyio
import pytest
from visign_api.inference.worker_thread import run_to_completion

WORKER_WAIT_SECONDS = 5
SETTLE_SECONDS = 0.2

GuardedCall = Callable[[], Coroutine[Any, Any, None]]
CancelStrategy = Callable[["BlockingWorker", GuardedCall], Coroutine[Any, Any, None]]


class BlockingWorker:
    def __init__(self) -> None:
        self.release = threading.Event()
        self.finished = threading.Event()

    def __call__(self, worker_input: str) -> str:
        self.release.wait(WORKER_WAIT_SECONDS)
        self.finished.set()
        return worker_input.upper()


async def cancel_natively(
    blocking_worker: BlockingWorker, guarded_call: GuardedCall
) -> None:
    # Huy thuan cua asyncio (vi du uvicorn huy task khi tat may qua han); worker chi duoc tha sau khi huy
    guarded_task = asyncio.ensure_future(guarded_call())
    await asyncio.sleep(SETTLE_SECONDS)
    guarded_task.cancel()
    await asyncio.sleep(SETTLE_SECONDS)
    blocking_worker.release.set()
    with pytest.raises(asyncio.CancelledError):
        await guarded_task


async def cancel_through_anyio_scope(
    blocking_worker: BlockingWorker, guarded_call: GuardedCall
) -> None:
    # Huy kieu anyio (task group/cancel scope cua Starlette) duoc giao lap lai toi khi task roi scope
    with anyio.CancelScope() as cancel_scope:
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(guarded_call)
            await asyncio.sleep(SETTLE_SECONDS)
            # Hen tha worker sau lenh huy: thu tu huy -> tha duoc bao dam
            asyncio.get_running_loop().call_later(
                SETTLE_SECONDS, blocking_worker.release.set
            )
            cancel_scope.cancel()
    assert cancel_scope.cancelled_caught


@pytest.mark.parametrize(
    "cancel_strategy", [cancel_natively, cancel_through_anyio_scope]
)
def test_cancelled_request_waits_for_worker_before_leaving(
    cancel_strategy: CancelStrategy,
) -> None:
    blocking_worker = BlockingWorker()
    timeline: list[str] = []

    async def guarded_call() -> None:
        try:
            await run_to_completion(blocking_worker, "clip")
        finally:
            # Noi slot va clip tam duoc tra lai: chi duoc chay sau khi worker da xong
            timeline.append(f"left-after-worker={blocking_worker.finished.is_set()}")

    asyncio.run(cancel_strategy(blocking_worker, guarded_call))

    assert timeline == ["left-after-worker=True"]


def test_result_is_returned_when_not_cancelled() -> None:
    def shout(worker_input: str) -> str:
        return worker_input.upper()

    assert asyncio.run(run_to_completion(shout, "clip")) == "CLIP"


def test_worker_error_propagates_when_not_cancelled() -> None:
    def fail(worker_input: str) -> str:
        raise ValueError(f"loi khi doc {worker_input}")

    with pytest.raises(ValueError, match="loi khi doc clip"):
        asyncio.run(run_to_completion(fail, "clip"))


class FailingAfterCancelWorker(BlockingWorker):
    def __call__(self, worker_input: str) -> str:
        super().__call__(worker_input)
        raise ValueError("worker loi sau khi request da huy")


def test_worker_error_after_cancel_is_not_reported_as_unretrieved(
    caplog: pytest.LogCaptureFixture,
) -> None:
    failing_worker = FailingAfterCancelWorker()

    async def guarded_call() -> None:
        await run_to_completion(failing_worker, "clip")

    asyncio.run(cancel_natively(failing_worker, guarded_call))
    gc.collect()

    # Loi cua worker sau khi huy da duoc doc ra, asyncio khong log "never retrieved"
    assert "never retrieved" not in caplog.text
