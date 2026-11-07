# services/inference-api/src/visign_api/inference/coordinator.py
# Gioi han mot luot suy luan dong thoi; cho slot qua timeout thi tra SERVICE_BUSY (T026).
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from visign_api.domain.errors import ServiceBusyException

# MVP chi chay mot model tren mot may demo nen chi mot request duoc suy luan tai mot thoi diem
SINGLE_INFERENCE_SLOT = 1


class InferenceCoordinator:
    def __init__(self, wait_timeout_seconds: float) -> None:
        if wait_timeout_seconds <= 0:
            raise ValueError("wait_timeout_seconds phai lon hon 0")
        self._wait_timeout_seconds = wait_timeout_seconds
        self._inference_slot = asyncio.Semaphore(SINGLE_INFERENCE_SLOT)

    @asynccontextmanager
    async def acquire_slot(self) -> AsyncIterator[None]:
        # Timeout chi tinh thoi gian cho slot, khong gioi han thoi gian suy luan sau khi da vao slot
        try:
            async with asyncio.timeout(self._wait_timeout_seconds):
                await self._inference_slot.acquire()
        except TimeoutError as wait_timeout:
            raise ServiceBusyException() from wait_timeout
        try:
            yield
        finally:
            self._inference_slot.release()
