# ai/src/visign_ai/landmarks/extract_manifest.py — Trích tensor từ danh sách clip T017.
"""Trích landmark từ danh sách thử nghiệm CSV gồm sampleId và rawPath."""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Any

import numpy as np

from .errors import PipelineError
from .holistic_extractor import group_masks
from .pipeline import process_video
from .sequence_transform import load_schema, schema_digest

SAMPLE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*_[0-9a-f]{12}")


class BatchSampleError(ValueError):
    """Lỗi riêng của thao tác đọc và xuất mẫu trong CLI offline."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def read_samples(path: Path) -> list[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.reader(source, strict=True)
        if next(reader, None) != ["sampleId", "rawPath"]:
            raise ValueError("CSV thử nghiệm cần header sampleId,rawPath.")
        rows: list[tuple[str, str]] = []
        seen: set[str] = set()
        for fields in reader:
            if len(fields) != 2:
                raise ValueError(f"Dòng {reader.line_num} cần đúng hai cột.")
            sample_id, raw_path = fields
            if not SAMPLE_ID.fullmatch(sample_id) or sample_id in seen:
                raise ValueError(
                    f"sampleId sai định dạng hoặc trùng ở dòng {reader.line_num}."
                )
            rows.append((sample_id, raw_path))
            seen.add(sample_id)
    if not rows:
        raise ValueError("Danh sách clip rỗng.")
    return rows


def source_path(root: Path, raw_path: str) -> Path:
    relative = PurePosixPath(raw_path)
    if (
        not relative.parts
        or relative.is_absolute()
        or ".." in relative.parts
        or any(char in raw_path for char in ("\\", ":", "\x00"))
    ):
        raise BatchSampleError(
            "INVALID_RAW_PATH", "rawPath phải tương đối và dùng dấu /."
        )
    path = root.joinpath(*relative.parts).resolve()
    if not path.is_relative_to(root):
        raise BatchSampleError("INVALID_RAW_PATH", "rawPath trỏ ra ngoài dataset.")
    return path


def write_sequence(path: Path, sample_id: str, result: dict[str, Any]) -> None:
    schema = result["schema"]
    valid = result["tensor_mask"]
    with NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with temporary.open("wb") as stream:
            np.savez_compressed(
                stream,
                sampleId=sample_id,
                features=result["tensor"],
                timestampsMs=np.rint(result["target"]).astype(np.int64),
                missingMask=~group_masks(valid),
                missingPointMask=~valid,
                normalization=schema["normalization"]["origin"],
                featureSchemaVersion=schema["featureSchemaVersion"],
                extractorVersion=schema["extractorVersion"],
                schemaSha256=schema_digest(schema),
            )
        # Công bố file đã ghi xong và từ chối nếu tiến trình khác đã tạo đích.
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def extract_sample(
    root: Path, output: Path, sample_id: str, raw_path: str, model_dir: Path | None
) -> dict[str, Any]:
    path = source_path(root, raw_path)
    if not path.is_file():
        raise BatchSampleError("SOURCE_NOT_FOUND", "Không tìm thấy file nguồn.")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest[:12] != sample_id.rsplit("_", 1)[1]:
        raise BatchSampleError(
            "SAMPLE_HASH_MISMATCH", "Hash video không khớp sampleId."
        )
    destination = output / f"{sample_id}.npz"
    if destination.exists():
        raise BatchSampleError("OUTPUT_EXISTS", "Artifact đã tồn tại.")
    result = process_video(path, model_dir=model_dir, allow_mp4=True)
    if result["report"]["inputStatus"] != "HAS_USABLE_FRAMES":
        raise PipelineError(
            "INSUFFICIENT_LANDMARKS", "Không có frame tensor đủ vai và tay."
        )
    write_sequence(destination, sample_id, result)
    return {
        "sampleId": sample_id,
        "landmarkPath": destination.relative_to(root).as_posix(),
        "report": result["report"],
    }


def run_batch(
    root: Path, rows: list[tuple[str, str]], model_dir: Path | None
) -> dict[str, Any]:
    schema = load_schema()
    version = schema["featureSchemaVersion"]
    output = root / "processed" / version
    if output.resolve() != output:
        raise ValueError("Thư mục output không được chuyển hướng qua symlink.")
    output.mkdir(parents=True, exist_ok=True)
    accepted, rejected = [], []
    for sample_id, raw_path in rows:
        try:
            accepted.append(
                extract_sample(root, output, sample_id, raw_path, model_dir)
            )
        except (BatchSampleError, PipelineError) as error:
            rejected.append({"sampleId": sample_id, "code": error.code})
        except FileExistsError:
            rejected.append({"sampleId": sample_id, "code": "OUTPUT_EXISTS"})
        except OSError:
            rejected.append({"sampleId": sample_id, "code": "SAMPLE_IO_FAILED"})
    return {
        "featureSchemaVersion": version,
        "extractorVersion": schema["extractorVersion"],
        "schemaSha256": schema_digest(schema),
        "acceptedCount": len(accepted),
        "rejectedCount": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path)
    args = parser.parse_args()
    try:
        root = args.dataset_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("Dataset root phải là thư mục có sẵn.")
        result = run_batch(root, read_samples(args.samples), args.model_dir)
    except (csv.Error, OSError, ValueError) as error:
        print(f"T017: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return int(bool(result["rejected"]))


if __name__ == "__main__":
    raise SystemExit(main())
