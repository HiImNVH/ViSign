# services/inference-api/tests/unit/test_temporary_clip.py
# Chung minh clip tam luon bi xoa o moi duong di: thanh cong, loi, ngat, ghi hong va xoa that bai (T025).
import logging
from pathlib import Path
from typing import Any

import pytest
from visign_api.inference.temporary_clip import (
    CLIP_FILE_PREFIX,
    CLIP_FILE_SUFFIX,
    TemporaryClip,
    open_temporary_clip,
)
from visign_api.observability import LOGGER_NAME

SAMPLE_CLIP_BYTES = b"\x1aE\xdf\xa3 sample webm bytes"


def test_clip_exists_with_uploaded_bytes_then_is_deleted(tmp_path: Path) -> None:
    # Given bytes upload; When dung clip trong context; Then file dung noi dung va bi xoa khi thoat
    with open_temporary_clip(SAMPLE_CLIP_BYTES, tmp_path) as clip:
        assert isinstance(clip, TemporaryClip)
        assert clip.path.read_bytes() == SAMPLE_CLIP_BYTES
        assert clip.path.parent == tmp_path
        assert clip.path.name.startswith(CLIP_FILE_PREFIX)
        assert clip.path.name.endswith(CLIP_FILE_SUFFIX)
        clip_path = clip.path

    assert not clip_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_clip_is_deleted_when_inference_raises(tmp_path: Path) -> None:
    with (
        pytest.raises(RuntimeError, match="loi suy luan gia lap"),
        open_temporary_clip(SAMPLE_CLIP_BYTES, tmp_path) as clip,
    ):
        clip_path = clip.path
        raise RuntimeError("loi suy luan gia lap")

    assert not clip_path.exists()


def test_clip_is_deleted_when_request_is_interrupted(tmp_path: Path) -> None:
    # BaseException (huy request, tat server) cung phai di qua nhanh xoa
    with (
        pytest.raises(KeyboardInterrupt),
        open_temporary_clip(SAMPLE_CLIP_BYTES, tmp_path) as clip,
    ):
        clip_path = clip.path
        raise KeyboardInterrupt

    assert not clip_path.exists()


def test_partially_written_clip_is_deleted_when_write_fails(tmp_path: Path) -> None:
    invalid_clip_content: Any = "khong phai bytes"

    with pytest.raises(TypeError), open_temporary_clip(invalid_clip_content, tmp_path):
        pytest.fail("Khong duoc vao context khi ghi file that bai")

    assert list(tmp_path.iterdir()) == []


def test_delete_is_idempotent(tmp_path: Path) -> None:
    with open_temporary_clip(SAMPLE_CLIP_BYTES, tmp_path) as clip:
        clip.delete()
        clip.delete()
        assert not clip.path.exists()

    assert list(tmp_path.iterdir()) == []


class RecordingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.captured_records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.captured_records.append(record)


def test_failed_deletion_is_logged_as_error_without_masking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given he dieu hanh khoa file; Then log ERROR de van hanh xu ly, khong raise de khong che loi goc
    def refuse_unlink(self: Path, missing_ok: bool = False) -> None:
        raise PermissionError("file dang bi khoa")

    # Handler rieng gan thang vao logger de ket qua khong phu thuoc propagate/caplog cua pytest
    recording_handler = RecordingHandler()
    service_logger = logging.getLogger(LOGGER_NAME)
    service_logger.addHandler(recording_handler)
    monkeypatch.setattr(Path, "unlink", refuse_unlink)
    try:
        with open_temporary_clip(SAMPLE_CLIP_BYTES, tmp_path) as clip:
            locked_clip_path = clip.path
    finally:
        service_logger.removeHandler(recording_handler)
        monkeypatch.undo()
        for leftover_clip in tmp_path.iterdir():
            leftover_clip.unlink()

    error_records = [
        record
        for record in recording_handler.captured_records
        if record.levelno == logging.ERROR
    ]
    assert len(error_records) == 1
    assert error_records[0].exc_info is not None
    assert str(locked_clip_path) not in error_records[0].getMessage()


def test_repeated_requests_leave_no_files_behind(tmp_path: Path) -> None:
    for _ in range(20):
        with open_temporary_clip(SAMPLE_CLIP_BYTES, tmp_path):
            pass

    assert list(tmp_path.iterdir()) == []
