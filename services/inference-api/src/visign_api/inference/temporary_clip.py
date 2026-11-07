# services/inference-api/src/visign_api/inference/temporary_clip.py
# Vong doi clip tam tren dia: ghi tu bytes upload va luon xoa o moi duong di (T024, FR-011);
# clip con sot do tien trinh bi giet cung duoc don khi khoi dong (T066).
import logging
import os
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from visign_api.observability import LOGGER_NAME

CLIP_FILE_PREFIX = "visign_clip_"
# API chi nhan WebM nen duoi file co dinh, khong lay tu ten file nguoi dung gui
CLIP_FILE_SUFFIX = ".webm"
# Request chi giu clip vai giay (cho slot 3 s + suy luan); clip cu hon nguong nay la cua tien trinh da chet
# (OOM, SIGKILL) nen phai xoa de khong luu video. Nguong rong de khong dung clip cua tien trinh khac dang chay
STALE_CLIP_AGE_SECONDS = 15 * 60

service_logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class TemporaryClip:
    path: Path

    def delete(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as deletion_error:
            # Khong raise de khong che loi goc cua request; muc ERROR de van hanh don file con sot
            service_logger.error("Khong xoa duoc clip tam", exc_info=deletion_error)


@contextmanager
def open_temporary_clip(
    clip_bytes: bytes, directory: Path | None = None
) -> Iterator[TemporaryClip]:
    file_descriptor, raw_path = tempfile.mkstemp(
        prefix=CLIP_FILE_PREFIX, suffix=CLIP_FILE_SUFFIX, dir=directory
    )
    clip = TemporaryClip(Path(raw_path))
    try:
        with os.fdopen(file_descriptor, "wb") as clip_file:
            clip_file.write(clip_bytes)
        yield clip
    finally:
        clip.delete()


def find_stale_clips(clip_directory: Path, oldest_allowed_mtime: float) -> list[Path]:
    stale_clips = []
    for leftover_path in clip_directory.glob(f"{CLIP_FILE_PREFIX}*{CLIP_FILE_SUFFIX}"):
        try:
            if leftover_path.stat().st_mtime < oldest_allowed_mtime:
                stale_clips.append(leftover_path)
        except OSError:
            # File vua bi tien trinh khac xoa giua luc liet ke: khong con gi de don
            continue
    return stale_clips


def sweep_stale_clips(
    directory: Path | None = None, max_age_seconds: float = STALE_CLIP_AGE_SECONDS
) -> None:
    clip_directory = Path(directory or tempfile.gettempdir())
    stale_clips = find_stale_clips(clip_directory, time.time() - max_age_seconds)
    for stale_clip in stale_clips:
        TemporaryClip(stale_clip).delete()
    if stale_clips:
        # Chi ghi so luong, khong ghi duong dan hay ten file
        service_logger.info(
            "Da don %d clip tam con sot tu tien trinh truoc", len(stale_clips)
        )
