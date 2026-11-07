# services/inference-api/src/visign_api/inference/detector_pool.py
# Bo detector MediaPipe tao san o thread nen (T065, SC-002): request lay bo da san sang thay vi tao 3 detector tren
# duong gang, bo da dung duoc dong o thread nen. Moi bo chi dung cho mot clip theo hop dong cua visign_ai; bo bi
# treo hoac loi thi request tu tao detector nhu truoc.
import logging
import threading
import time
from collections.abc import Callable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import AbstractContextManager, ExitStack, contextmanager
from dataclasses import dataclass
from typing import Any

from visign_api.observability import LOGGER_NAME

# Bo dang tao thuong xong trong khoang 0,5 s; cho lau hon thi khong con nhanh hon tu tao tren duong gang
PREPARED_SET_WAIT_SECONDS = 2.0
DETECTOR_THREAD_PREFIX = "visign-detectors"

DetectorSetOpener = Callable[[], AbstractContextManager[Any]]

service_logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class DetectorLease:
    resources: ExitStack
    detectors: Any


class DetectorPool:
    def __init__(
        self,
        open_detector_set: DetectorSetOpener,
        wait_seconds: float = PREPARED_SET_WAIT_SECONDS,
    ) -> None:
        self._open_detector_set = open_detector_set
        self._wait_seconds = wait_seconds
        self._lock = threading.Lock()
        # Mot thread: tao va dong bo detector tuan tu, khong tranh CPU voi nhau
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=DETECTOR_THREAD_PREFIX
        )
        self._pending: Future[DetectorLease] | None = None
        self._pending_deadline = 0.0
        self._closed = False
        self._schedule_next_set()

    @contextmanager
    def lease(self) -> Iterator[Any | None]:
        # None: khong co bo san sang, pipeline tu tao detector cho clip nay nhu truoc
        detector_lease = self._take_prepared_set()
        try:
            yield None if detector_lease is None else detector_lease.detectors
        finally:
            # Chuan bi bo ke tiep truoc roi moi dong bo vua dung: request sau co bo som nhat
            self._schedule_next_set()
            if detector_lease is not None:
                self._release(detector_lease)

    def close(self, wait: bool = False) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            pending, self._pending = self._pending, None
        if pending is not None and not pending.cancel():
            # Bo dang tao (hoac da tao xong) duoc dong ngay khi co, khong ai dung nua
            pending.add_done_callback(close_finished_preparation)
        self._executor.shutdown(wait=wait)

    def _open_lease(self) -> DetectorLease:
        resources = ExitStack()
        try:
            detectors = resources.enter_context(self._open_detector_set())
        except BaseException:
            resources.close()
            raise
        return DetectorLease(resources, detectors)

    def _schedule_next_set(self) -> None:
        with self._lock:
            if self._closed or self._pending is not None:
                return
            self._pending = self._executor.submit(self._open_lease)
            self._pending_deadline = time.monotonic() + self._wait_seconds

    def _take_prepared_set(self) -> DetectorLease | None:
        with self._lock:
            pending, deadline = self._pending, self._pending_deadline
        if pending is None:
            return None
        try:
            # Qua han ma chua xong (co the treo): khong cho them, giu bo do cho request sau
            detector_lease = pending.result(
                timeout=max(deadline - time.monotonic(), 0.0)
            )
        except TimeoutError:
            return None
        except Exception:
            service_logger.warning(
                "Khong chuan bi san duoc bo detector; request tu tao detector",
                exc_info=True,
            )
            self._forget(pending)
            return None
        with self._lock:
            if self._pending is not pending:
                # Pool vua dong (bo se duoc dong theo callback) hoac request khac da lay: moi bo dung mot lan
                return None
            self._pending = None
        return detector_lease

    def _forget(self, failed: Future[DetectorLease]) -> None:
        with self._lock:
            if self._pending is failed:
                self._pending = None

    def _release(self, detector_lease: DetectorLease) -> None:
        with self._lock:
            if not self._closed:
                self._executor.submit(close_lease, detector_lease)
                return
        # Pool da dong (doi artifact hoac tat app): dong ngay tren thread vua dung xong
        close_lease(detector_lease)


def close_lease(detector_lease: DetectorLease) -> None:
    try:
        detector_lease.resources.close()
    except Exception:
        service_logger.warning("Dong bo detector bi loi", exc_info=True)


def close_finished_preparation(prepared: Future[DetectorLease]) -> None:
    if prepared.cancelled() or prepared.exception() is not None:
        return
    close_lease(prepared.result())
