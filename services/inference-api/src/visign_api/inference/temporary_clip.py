# services/inference-api/src/visign_api/inference/temporary_clip.py
# Vong doi clip tam tren dia: ghi tu bytes upload va luon xoa o moi duong di (T024, FR-011).
import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from visign_api.observability import LOGGER_NAME

CLIP_FILE_PREFIX = "visign_clip_"
# API chi nhan WebM nen duoi file co dinh, khong lay tu ten file nguoi dung gui
CLIP_FILE_SUFFIX = ".webm"

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
