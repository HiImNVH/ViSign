# services/inference-api/src/visign_api/admin/inspection.py
# Inspect mot clip cho admin (T079, FR-021): moi luc mot lan; clip nam trong thu muc tam rieng va bi xoa o moi nhanh,
# ke ca khi request het gio (worker van chay not roi xoa). Tra ZIP gom report.json va landmarks.npz, khong tra video.
import asyncio
import io
import json
import logging
import shutil
import tempfile
import threading
import time
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from visign_api.admin.errors import (
    ADMIN_JOB_ACTIVE,
    ADMIN_TIMEOUT,
    ADMIN_UNAVAILABLE,
    AdminApiException,
)
from visign_api.domain.errors import build_api_exception
from visign_api.inference.clip_validator import ensure_webm_signature
from visign_api.inference.feature_extraction import PipelineBinding
from visign_api.inference.pipeline_errors import map_pipeline_error_code
from visign_api.observability import LOGGER_NAME

INSPECT_DIRECTORY_PREFIX = "visign_inspect_"
STALE_INSPECTION_AGE_SECONDS = 15 * 60
MP4_BOX_TYPE = b"ftyp"
REPORT_FILE = "report.json"
LANDMARKS_FILE = "landmarks.npz"

service_logger = logging.getLogger(LOGGER_NAME)


def detect_clip_suffix(clip_bytes: bytes) -> str:
    # Nhan dien bang byte dau, khong tin ten file/MIME client gui
    if clip_bytes[4:8] == MP4_BOX_TYPE:
        return ".mp4"
    ensure_webm_signature(clip_bytes)
    return ".webm"


def to_json_value(value: Any) -> Any:
    as_list = getattr(value, "tolist", None)
    return as_list() if callable(as_list) else str(value)


def build_report_zip(pipeline_result: Mapping[str, Any], suffix: str) -> bytes:
    inspection_report = dict(pipeline_result.get("report", {}))
    # Ten file tam co the lo cau truc thu muc may chu: thay bang ten chung
    inspection_report["sourceName"] = f"clip{suffix}"
    landmark_arrays: dict[str, Any] = {
        name: value
        for name, value in pipeline_result.items()
        if isinstance(value, np.ndarray)
    }
    landmarks_buffer = io.BytesIO()
    np.savez_compressed(landmarks_buffer, **landmark_arrays)
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as report_zip:
        report_zip.writestr(
            REPORT_FILE,
            json.dumps(
                inspection_report, ensure_ascii=False, indent=2, default=to_json_value
            ),
        )
        report_zip.writestr(LANDMARKS_FILE, landmarks_buffer.getvalue())
    return archive_buffer.getvalue()


def sweep_stale_inspections(
    directory: Path | None = None,
    max_age_seconds: float = STALE_INSPECTION_AGE_SECONDS,
) -> int:
    # Thu muc inspect cua tien trinh bi giet cung (khong chay finally) bi xoa khi khoi dong; log chi dem so luong
    inspect_root = directory or Path(tempfile.gettempdir())
    oldest_allowed = time.time() - max_age_seconds
    removed = 0
    for leftover in inspect_root.glob(f"{INSPECT_DIRECTORY_PREFIX}*"):
        try:
            if leftover.is_dir() and leftover.stat().st_mtime < oldest_allowed:
                shutil.rmtree(leftover)
                removed += 1
        except OSError:
            continue
    if removed:
        service_logger.info(
            "Da don %s thu muc inspect con sot tu tien trinh truoc", removed
        )
    return removed


class InspectionService:
    def __init__(
        self,
        pipeline: PipelineBinding | None,
        timeout_seconds: float,
        model_directory: Path | None,
    ) -> None:
        self._pipeline = pipeline
        self._timeout_seconds = timeout_seconds
        self._model_directory = model_directory
        # Mot luot inspect: luot bi het gio van giu slot toi khi worker xong va don xong
        self._slot = threading.Lock()

    async def inspect(self, clip_bytes: bytes) -> bytes:
        if self._pipeline is None:
            raise AdminApiException(ADMIN_UNAVAILABLE)
        suffix = detect_clip_suffix(clip_bytes)
        if not self._slot.acquire(blocking=False):
            raise AdminApiException(ADMIN_JOB_ACTIVE)
        event_loop = asyncio.get_running_loop()
        finished: asyncio.Future[bytes] = event_loop.create_future()
        # Thread daemon: inspect treo khong giu tien trinh song khi tat app
        worker = threading.Thread(
            target=self._inspect_and_release,
            args=(self._pipeline, clip_bytes, suffix, event_loop, finished),
            name="visign-inspect",
            daemon=True,
        )
        try:
            worker.start()
        except BaseException:
            self._slot.release()
            raise
        try:
            return await asyncio.wait_for(
                asyncio.shield(finished), self._timeout_seconds
            )
        except TimeoutError:
            raise AdminApiException(ADMIN_TIMEOUT) from None
        finally:
            # Request het gio hoac bi huy: bo ket qua ve sau, worker van tu don thu muc tam
            if not finished.done():
                finished.cancel()

    def _inspect_and_release(
        self,
        pipeline: PipelineBinding,
        clip_bytes: bytes,
        suffix: str,
        event_loop: asyncio.AbstractEventLoop,
        finished: "asyncio.Future[bytes]",
    ) -> None:
        report_zip: bytes | None = None
        failure: BaseException | None = None
        try:
            report_zip = self._inspect_in_temporary_directory(
                pipeline, clip_bytes, suffix
            )
        except BaseException as inspection_error:  # noqa: BLE001 - moi loi phai ve request, khong mat trong thread
            failure = inspection_error
        finally:
            # Nha slot sau khi da xoa thu muc tam, truoc khi tra ket qua: request ke tiep khong bi 409 gia
            self._slot.release()
        settle_from_worker(event_loop, finished, report_zip, failure)

    def _inspect_in_temporary_directory(
        self, pipeline: PipelineBinding, clip_bytes: bytes, suffix: str
    ) -> bytes:
        inspect_directory = Path(tempfile.mkdtemp(prefix=INSPECT_DIRECTORY_PREFIX))
        try:
            clip_path = inspect_directory / f"clip{suffix}"
            clip_path.write_bytes(clip_bytes)
            try:
                pipeline_result = pipeline.run(
                    clip_path, model_dir=self._model_directory, allow_mp4=True
                )
            except pipeline.errorType as pipeline_error:
                pipeline_code = str(getattr(pipeline_error, "code", ""))
                raise build_api_exception(
                    map_pipeline_error_code(pipeline_code)
                ) from pipeline_error
            return build_report_zip(pipeline_result, suffix)
        finally:
            shutil.rmtree(inspect_directory, ignore_errors=True)


def settle_from_worker(
    event_loop: asyncio.AbstractEventLoop,
    finished: "asyncio.Future[bytes]",
    report_zip: bytes | None,
    failure: BaseException | None,
) -> None:
    def settle() -> None:
        if finished.done():
            return
        if failure is not None:
            finished.set_exception(failure)
        elif report_zip is not None:
            finished.set_result(report_zip)

    try:
        event_loop.call_soon_threadsafe(settle)
    except RuntimeError:
        # Event loop da dong (app tat): khong con request nao cho ket qua
        return
