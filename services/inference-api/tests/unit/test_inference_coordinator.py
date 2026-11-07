# services/inference-api/tests/unit/test_inference_coordinator.py
# Kiem tra coordinator chi cho mot luot suy luan, het thoi gian cho thi tra SERVICE_BUSY (T026).
import asyncio

import pytest
from visign_api.domain.errors import ErrorCode, ServiceBusyException
from visign_api.inference.coordinator import InferenceCoordinator

SHORT_WAIT_SECONDS = 0.05


def test_second_request_is_rejected_as_busy_while_slot_is_held() -> None:
    async def scenario() -> None:
        coordinator = InferenceCoordinator(SHORT_WAIT_SECONDS)
        async with coordinator.acquire_slot():
            with pytest.raises(ServiceBusyException) as busy_error:
                async with coordinator.acquire_slot():
                    pytest.fail("Khong duoc vao slot thu hai")
        assert busy_error.value.code is ErrorCode.SERVICE_BUSY

    asyncio.run(scenario())


def test_waiting_request_gets_slot_when_released_within_timeout() -> None:
    async def scenario() -> None:
        coordinator = InferenceCoordinator(1.0)
        served_order: list[str] = []

        async def hold_slot_briefly() -> None:
            async with coordinator.acquire_slot():
                served_order.append("first")
                await asyncio.sleep(0.02)

        async def wait_for_slot() -> None:
            await asyncio.sleep(0.005)
            async with coordinator.acquire_slot():
                served_order.append("second")

        await asyncio.gather(hold_slot_briefly(), wait_for_slot())
        assert served_order == ["first", "second"]

    asyncio.run(scenario())


def test_slot_is_released_when_inference_raises() -> None:
    async def scenario() -> None:
        coordinator = InferenceCoordinator(SHORT_WAIT_SECONDS)
        with pytest.raises(RuntimeError):
            async with coordinator.acquire_slot():
                raise RuntimeError("loi suy luan gia lap")
        async with coordinator.acquire_slot():
            pass

    asyncio.run(scenario())


def test_timed_out_waiter_does_not_leak_the_slot() -> None:
    async def scenario() -> None:
        coordinator = InferenceCoordinator(SHORT_WAIT_SECONDS)
        async with coordinator.acquire_slot():
            with pytest.raises(ServiceBusyException):
                async with coordinator.acquire_slot():
                    pass
        # Sau khi request bi tu choi, slot van dung mot va dung lai duoc
        async with coordinator.acquire_slot():
            pass

    asyncio.run(scenario())


def test_wait_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError):
        InferenceCoordinator(0)
