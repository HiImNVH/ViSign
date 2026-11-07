# services/inference-api/tests/unit/test_detector_pool.py
# T065/SC-002: bo detector tao san o thread nen. Request lay bo da san sang (moi bo dung mot lan), bo da dung
# dong ngoai duong gang; bo bi treo hoac loi thi request tu tao detector nhu truoc, khong cho them.
import threading
import time
from dataclasses import dataclass

import pytest
from visign_api.inference.detector_pool import DetectorPool

GATE_TIMEOUT_SECONDS = 10
POLL_DEADLINE_SECONDS = 2
SHORT_WAIT_SECONDS = 0.2
MAIN_THREAD = "MainThread"


@dataclass
class FakeDetectorSet:
    index: int
    openedOn: str
    closedOn: str | None = None


class FakeDetectorSets:
    # Mo bo detector gia: ghi thread tao/dong; co the cham, treo hoac loi theo kich ban cua test
    def __init__(self) -> None:
        self.opened: list[FakeDetectorSet] = []
        self.gate = threading.Event()
        self.gate.set()
        self.prepare_delay_seconds = 0.0
        self.failures_left = 0

    def open(self) -> "FakeDetectorContext":
        return FakeDetectorContext(self)


class FakeDetectorContext:
    # Context dang class: chi ghi dong khi __exit__ duoc goi that, GC khong the dong thay pool
    def __init__(self, detector_sets: FakeDetectorSets) -> None:
        self._detector_sets = detector_sets
        self._detector_set: FakeDetectorSet | None = None

    def __enter__(self) -> FakeDetectorSet:
        detector_sets = self._detector_sets
        detector_sets.gate.wait(GATE_TIMEOUT_SECONDS)
        time.sleep(detector_sets.prepare_delay_seconds)
        if detector_sets.failures_left:
            detector_sets.failures_left -= 1
            raise RuntimeError("detector khong khoi tao duoc")
        self._detector_set = FakeDetectorSet(
            index=len(detector_sets.opened), openedOn=threading.current_thread().name
        )
        detector_sets.opened.append(self._detector_set)
        return self._detector_set

    def __exit__(self, *exc_info: object) -> None:
        assert self._detector_set is not None
        self._detector_set.closedOn = threading.current_thread().name


@pytest.fixture
def detector_sets() -> FakeDetectorSets:
    return FakeDetectorSets()


def lease_once(pool: DetectorPool) -> FakeDetectorSet | None:
    with pool.lease() as detectors:
        return detectors


def wait_until_opened(detector_sets: FakeDetectorSets, count: int) -> None:
    deadline = time.monotonic() + POLL_DEADLINE_SECONDS
    while len(detector_sets.opened) < count:
        if time.monotonic() > deadline:
            raise AssertionError(f"chua mo du {count} bo detector")
        time.sleep(0.01)


def wait_for_prepared_set(pool: DetectorPool) -> FakeDetectorSet:
    # Bo dang chuan bi qua han thi lease tra None ngay; hoi lai toi khi bo hoan tat
    deadline = time.monotonic() + POLL_DEADLINE_SECONDS
    while time.monotonic() < deadline:
        detectors = lease_once(pool)
        if detectors is not None:
            return detectors
        time.sleep(0.01)
    raise AssertionError("bo detector khong san sang")


def test_request_uses_set_prepared_in_background(
    detector_sets: FakeDetectorSets,
) -> None:
    pool = DetectorPool(detector_sets.open)

    used = lease_once(pool)
    # Request xong thi bo ke tiep duoc chuan bi ngay o thread nen
    wait_until_opened(detector_sets, 2)
    pool.close(wait=True)

    assert used is detector_sets.opened[0]
    # Tao va dong deu o thread nen, khong nam tren thread xu ly request
    assert used.openedOn != MAIN_THREAD
    assert used.closedOn is not None and used.closedOn != MAIN_THREAD
    # Tat pool thi dong ca bo du phong chua dung
    assert all(spare.closedOn is not None for spare in detector_sets.opened)


def test_each_prepared_set_serves_one_request(
    detector_sets: FakeDetectorSets,
) -> None:
    pool = DetectorPool(detector_sets.open)

    first, second = lease_once(pool), lease_once(pool)
    pool.close(wait=True)

    assert first is not None and second is not None
    assert first is not second
    assert [first.index, second.index] == [0, 1]


def test_request_waits_for_set_still_being_prepared(
    detector_sets: FakeDetectorSets,
) -> None:
    detector_sets.prepare_delay_seconds = SHORT_WAIT_SECONDS
    pool = DetectorPool(detector_sets.open, wait_seconds=2)

    started = time.monotonic()
    used = lease_once(pool)
    pool.close(wait=True)

    assert used is detector_sets.opened[0]
    assert time.monotonic() - started >= SHORT_WAIT_SECONDS / 2


def test_stuck_preparation_falls_back_without_waiting_again(
    detector_sets: FakeDetectorSets,
) -> None:
    detector_sets.gate.clear()
    pool = DetectorPool(detector_sets.open, wait_seconds=SHORT_WAIT_SECONDS)

    first_started = time.monotonic()
    first = lease_once(pool)
    first_elapsed = time.monotonic() - first_started
    second_started = time.monotonic()
    second = lease_once(pool)
    second_elapsed = time.monotonic() - second_started
    detector_sets.gate.set()
    recovered = wait_for_prepared_set(pool)
    pool.close(wait=True)

    # Request tu tao detector (None) sau toi da mot lan cho; request sau khong cho lai bo dang treo
    assert first is None and second is None
    assert first_elapsed < SHORT_WAIT_SECONDS + 0.5
    assert second_elapsed < SHORT_WAIT_SECONDS / 2
    assert recovered is detector_sets.opened[0]


def test_failed_preparation_falls_back_then_recovers(
    detector_sets: FakeDetectorSets,
) -> None:
    detector_sets.failures_left = 1
    pool = DetectorPool(detector_sets.open)

    fallback = lease_once(pool)
    recovered = lease_once(pool)
    pool.close(wait=True)

    assert fallback is None
    assert recovered is detector_sets.opened[0]


def test_set_is_closed_even_when_request_fails(
    detector_sets: FakeDetectorSets,
) -> None:
    pool = DetectorPool(detector_sets.open)
    used: FakeDetectorSet | None = None

    with pytest.raises(RuntimeError, match="giua chung"), pool.lease() as detectors:
        used = detectors
        raise RuntimeError("detector loi giua chung")
    pool.close(wait=True)

    assert used is not None and used.closedOn is not None


def test_close_releases_spare_set_and_stops_preparing(
    detector_sets: FakeDetectorSets,
) -> None:
    pool = DetectorPool(detector_sets.open)
    wait_until_opened(detector_sets, 1)

    pool.close(wait=True)
    late = lease_once(pool)

    assert late is None
    # Bo du phong chua dung bi dong; sau khi tat khong mo them bo nao
    assert len(detector_sets.opened) == 1
    assert detector_sets.opened[0].closedOn is not None


def test_set_in_use_during_close_is_closed_after_its_request(
    detector_sets: FakeDetectorSets,
) -> None:
    pool = DetectorPool(detector_sets.open)

    with pool.lease() as in_use:
        pool.close(wait=True)
        closed_while_in_use = in_use is not None and in_use.closedOn is not None

    assert in_use is not None
    assert closed_while_in_use is False
    # Pool da dong nen bo duoc dong ngay tren thread vua dung xong
    assert in_use.closedOn == MAIN_THREAD
