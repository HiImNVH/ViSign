# ai/src/visign_ai/pilot.py
"""Runner pilot cho cong cu admin (T110, contracts/admin-tools.md "Pilot runner").

API (`/api/admin/pilot/prepare|train`) goi `build_pilot_runner()` va dieu phoi khoa/trang thai; module nay lam
phan AI: kiem ban ban giao, trich landmark bang dung pipeline dung chung, train GRU (co trong so nhom diem) va
danh gia tren test. Moi bao cao chi tiet nam trong thu muc run; loi dau vao la `PilotInputError`.

Ban ban giao (`VISIGN_PILOT_HANDOFF`) la mot thu muc chua:
- manifest raw (mac dinh `manifest.csv`, doi bang `VISIGN_PILOT_MANIFEST`): `sampleId`, `classLabel`, `meaningId`,
  `recordingSessionId`, `licenseStatus`, `verificationStatus`, `split`, `rawPath` (tuong doi voi thu muc ban giao);
- class map (mac dinh `class-map.json`, doi bang `VISIGN_PILOT_CLASS_MAP`);
- cac video theo `rawPath`. `sampleId` phai ket thuc bang 12 ky tu dau SHA-256 cua video.
Cau hinh train mac dinh `ai/configs/pilot-gru.yaml` (doi bang `VISIGN_PILOT_CONFIG`).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from visign_ai.landmarks.extract_manifest import write_sequence
from visign_ai.landmarks.pipeline import PipelineError, process_video
from visign_ai.landmarks.sequence_transform import load_schema

AI_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = AI_ROOT / "configs" / "pilot-gru.yaml"
DEFAULT_SCHEMA = AI_ROOT / "configs" / "feature_schema.json"
RAW_FIELDS = (
    "sampleId",
    "classLabel",
    "meaningId",
    "recordingSessionId",
    "licenseStatus",
    "verificationStatus",
    "split",
    "rawPath",
)
FEATURE_MANIFEST = "manifest.csv"
CLASS_MAP = "class-map.json"
PREPARE_REPORT = "prepare-report.json"
DATASET_VERSION_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*")


class PilotInputError(ValueError):
    """Ban ban giao khong dat kiem tra (thieu file, cot, hash, nhan, coverage)."""

    # API (`pilot_jobs._fail`) nhan dang loi dau vao qua thuoc tinh nay
    is_pilot_input_error = True


class Progress(Protocol):
    def epoch(self, done: int, total: int) -> None: ...

    def evaluating(self) -> None: ...


@dataclass(frozen=True)
class PreparedPilot:
    datasetVersion: str
    featureSchemaVersion: str
    sampleTotal: int
    accepted: int


@dataclass(frozen=True)
class TrainedPilot:
    epochs: int
    accuracy: float | None
    macroF1: float | None
    wandbRunId: str | None
    wandbMode: str | None
    wandbUrl: str | None


def _read_rows(path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise PilotInputError("Không đọc được manifest bàn giao.") from error
    reader = csv.DictReader(io.StringIO(text))
    missing = set(RAW_FIELDS) - set(reader.fieldnames or [])
    if missing:
        raise PilotInputError(f"Manifest thiếu cột: {sorted(missing)}")
    rows = [dict(row) for row in reader]
    if not rows:
        raise PilotInputError("Manifest bàn giao rỗng.")
    ids = [row["sampleId"] for row in rows]
    if len(ids) != len(set(ids)):
        raise PilotInputError("Manifest có sampleId trùng.")
    return rows


def _source_path(root: Path, raw_path: str) -> Path:
    candidate = (root / raw_path).resolve()
    if root.resolve() not in candidate.parents:
        raise PilotInputError("rawPath trỏ ra ngoài thư mục bàn giao.")
    return candidate


def _dataset_version(manifest: Path, digest: str) -> str:
    stem = manifest.stem.lower()
    if DATASET_VERSION_PATTERN.fullmatch(stem):
        return stem
    return f"pilot-admin-{digest[:8]}-v1"


class FilePilotRunner:
    def __init__(
        self,
        handoff: Path,
        manifest: Path,
        class_map: Path,
        config: Path = DEFAULT_CONFIG,
        schema: Path = DEFAULT_SCHEMA,
        model_dir: Path | None = None,
        extract: Callable[[Path, Path | None], dict[str, Any]] | None = None,
    ) -> None:
        self.handoff = handoff
        self.manifest = manifest
        self.class_map = class_map
        self.config = config
        self.schema = schema
        self.model_dir = model_dir
        self._extract = extract or (
            lambda path, model_dir: process_video(
                path, model_dir=model_dir, allow_mp4=True
            )
        )

    def prepare(self, workspace: Path, progress: Progress) -> PreparedPilot:
        if not self.handoff.is_dir():
            raise PilotInputError("Không tìm thấy thư mục bàn giao pilot.")
        rows = _read_rows(self.manifest)
        try:
            class_map = json.loads(self.class_map.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            raise PilotInputError("Không đọc được class map.") from error
        if not isinstance(class_map, Mapping) or not class_map:
            raise PilotInputError("Class map phải là JSON object không rỗng.")
        schema = load_schema(self.schema)
        features = workspace / "features"
        features.mkdir(parents=True, exist_ok=True)
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        for row in rows:
            code = self._extract_one(row, features)
            if code is None:
                accepted.append(
                    {**row, "landmarkPath": f"features/{row['sampleId']}.npz"}
                )
            else:
                rejected.append({"sampleId": row["sampleId"], "code": code})
        digest = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        report = {
            "manifestSha256": digest,
            "featureSchemaVersion": schema["featureSchemaVersion"],
            "extractorVersion": schema["extractorVersion"],
            "sampleTotal": len(rows),
            "accepted": len(accepted),
            "rejected": rejected,
        }
        (workspace / PREPARE_REPORT).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if not accepted:
            raise PilotInputError("Không clip nào trích được landmark.")
        fields = [*RAW_FIELDS, "landmarkPath"]
        with (workspace / FEATURE_MANIFEST).open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(accepted)
        (workspace / CLASS_MAP).write_text(
            json.dumps(class_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        dataset_version = _dataset_version(self.manifest, digest)
        (workspace / "dataset-version.txt").write_text(
            dataset_version, encoding="utf-8"
        )
        # Kiem day du nhu luc train (license, verification, leakage, so nghia pilot) truoc khi bao "ready"
        try:
            from visign_ai.training.training_inputs import prepare_inputs

            prepare_inputs(self._train_args(workspace, workspace / "artifact"))
        except (ValueError, KeyError, TypeError) as error:
            raise PilotInputError(
                f"Bàn giao không đạt kiểm tra train: {error}"
            ) from error
        return PreparedPilot(
            datasetVersion=dataset_version,
            featureSchemaVersion=schema["featureSchemaVersion"],
            sampleTotal=len(rows),
            accepted=len(accepted),
        )

    def _extract_one(self, row: Mapping[str, str], features: Path) -> str | None:
        try:
            source = _source_path(self.handoff, row["rawPath"])
        except PilotInputError:
            return "SOURCE_OUTSIDE_HANDOFF"
        if not source.is_file():
            return "SOURCE_NOT_FOUND"
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest[:12] != row["sampleId"].rsplit("_", 1)[-1]:
            return "SAMPLE_HASH_MISMATCH"
        try:
            result = self._extract(source, self.model_dir)
        except PipelineError as error:
            return error.code
        if result["report"].get("inputStatus") != "HAS_USABLE_FRAMES":
            return "INSUFFICIENT_LANDMARKS"
        write_sequence(features / f"{row['sampleId']}.npz", row["sampleId"], result)
        return None

    def _train_args(self, workspace: Path, output: Path) -> argparse.Namespace:
        version_file = workspace / "dataset-version.txt"
        return argparse.Namespace(
            manifest=workspace / FEATURE_MANIFEST,
            feature_root=workspace,
            class_map=workspace / CLASS_MAP,
            schema=self.schema,
            config=self.config,
            output=output,
            dataset_version=version_file.read_text(encoding="utf-8").strip()
            if version_file.exists()
            else "pilot-admin-v1",
            model_version=f"admin-{workspace.name}",
            classes=None,
            p0_meanings=None,
            device="cpu",
        )

    def train(self, workspace: Path, progress: Progress) -> TrainedPilot:
        from visign_ai.evaluation.evaluate import evaluate
        from visign_ai.training.train import train

        if not (workspace / FEATURE_MANIFEST).is_file():
            raise PilotInputError("Chưa có bản pilot đã chuẩn bị trong run này.")
        artifact = workspace / "artifact"
        args = self._train_args(workspace, artifact)
        train(args, on_epoch=progress.epoch)
        progress.evaluating()
        evaluation = workspace / "evaluation"
        evaluate(
            argparse.Namespace(
                artifact=artifact,
                manifest=args.manifest,
                feature_root=workspace,
                output=evaluation,
                device="cpu",
            )
        )
        report = json.loads(
            (evaluation / "evaluation-report.json").read_text(encoding="utf-8")
        )
        training = json.loads(
            (artifact / "training-report.json").read_text(encoding="utf-8")
        )
        return TrainedPilot(
            epochs=len(training["history"]),
            accuracy=report.get("accuracy"),
            macroF1=report.get("macroF1"),
            wandbRunId=training.get("wandbRunId"),
            wandbMode=training.get("wandbMode"),
            wandbUrl=training.get("wandbUrl"),
        )


def build_pilot_runner() -> FilePilotRunner | None:
    """Doc cau hinh tu bien moi truong; thieu VISIGN_PILOT_HANDOFF thi tra None (API tra 503)."""
    handoff_value = os.environ.get("VISIGN_PILOT_HANDOFF")
    if not handoff_value:
        return None
    handoff = Path(handoff_value)
    model_dir = os.environ.get("VISIGN_MODEL_DIR")
    return FilePilotRunner(
        handoff=handoff,
        manifest=handoff / os.environ.get("VISIGN_PILOT_MANIFEST", "manifest.csv"),
        class_map=handoff / os.environ.get("VISIGN_PILOT_CLASS_MAP", "class-map.json"),
        config=Path(os.environ.get("VISIGN_PILOT_CONFIG", str(DEFAULT_CONFIG))),
        model_dir=Path(model_dir) if model_dir else None,
    )
