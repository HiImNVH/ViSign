# ai/src/visign_ai/training/tracking.py
"""Theo doi thi nghiem tren Weights & Biases (tuy chon, 2026-11-08).

Bat bang khoa `wandb` trong config train, vi du:
    wandb: {entity: hiimnvh-github-sai-gon-university, project: ViSign, tags: [raw-p0]}
`WANDB_MODE` (online/offline/disabled) ghi de `mode`. API key nam o `wandb login` cua may (khong bao gio trong repo).
W&B loi (chua cai goi, chua dang nhap, mat mang) chi canh bao va train tiep: theo doi khong duoc lam hong train.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

MODES = ("online", "offline", "disabled")


def validate_wandb(config: Any) -> dict[str, Any]:
    if not isinstance(config, Mapping) or not isinstance(config.get("project"), str):
        raise TypeError("wandb.project phai la chuoi")
    unknown = set(config) - {"entity", "project", "mode", "tags"}
    if unknown:
        raise ValueError(f"wandb khong nhan khoa {sorted(unknown)}")
    if config.get("mode", "online") not in MODES:
        raise ValueError(f"wandb.mode phai thuoc {MODES}")
    tags = config.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ValueError("wandb.tags phai la danh sach chuoi")
    return dict(config)


def _mode(value: str) -> Literal["online", "offline", "disabled"]:
    if value == "offline":
        return "offline"
    if value == "disabled":
        return "disabled"
    return "online"


def _warn(message: str) -> None:
    print(f"W&B: {message}", file=sys.stderr)


class Tracker:
    def __init__(self, run: Any, mode: str) -> None:
        self.run = run
        self.mode = mode

    def log_epoch(self, epoch: int, train_loss: float, validation_loss: float) -> None:
        try:
            self.run.log(
                {"epoch": epoch, "train/loss": train_loss, "val/loss": validation_loss},
                step=epoch,
            )
        except Exception as error:  # noqa: BLE001 - theo doi khong duoc lam hong train
            _warn(f"log epoch that bai: {error}")

    def finish(
        self, summary: Mapping[str, Any], sweep: list[dict[str, float]]
    ) -> dict[str, Any]:
        info = {
            "wandbRunId": getattr(self.run, "id", None),
            "wandbMode": self.mode,
            "wandbUrl": None,
        }
        try:
            import wandb

            table = wandb.Table(
                columns=["threshold", "coverage", "acceptedClassAccuracy", "score"]
            )
            for row in sweep:
                table.add_data(
                    row["threshold"],
                    row["coverage"],
                    row["acceptedClassAccuracy"],
                    row["score"],
                )
            self.run.log({"val/threshold_sweep": table})
            for key, value in summary.items():
                self.run.summary[key] = value
            info["wandbUrl"] = (
                getattr(self.run, "url", None) if self.mode == "online" else None
            )
            self.run.finish()
        except Exception as error:  # noqa: BLE001
            _warn(f"ket thuc run that bai: {error}")
        return info


def start_tracking(
    config: Mapping[str, Any], run_name: str, run_config: Mapping[str, Any]
) -> Tracker | None:
    settings = config.get("wandb")
    if not settings:
        return None
    mode = os.environ.get("WANDB_MODE", settings.get("mode", "online"))
    if mode == "disabled":
        return None
    try:
        import wandb
    except ImportError:
        _warn("chua cai goi wandb (uv sync --extra tracking); bo qua theo doi")
        return None
    try:
        run = wandb.init(
            entity=settings.get("entity"),
            project=settings["project"],
            name=run_name,
            tags=settings.get("tags", []),
            config=dict(run_config),
            mode=_mode(mode),
            reinit="finish_previous",
        )
    except Exception as error:  # noqa: BLE001 - vi du chua `wandb login`
        _warn(f"khong khoi tao duoc run ({error}); train tiep khong theo doi")
        return None
    return Tracker(run, mode)


def log_evaluation(
    artifact: Path, report: Mapping[str, Any], matrix: Path | None
) -> None:
    """Ghi metric test vao dung run da train (doc wandbRunId trong training-report)."""
    try:
        import json

        training = json.loads(
            (artifact / "training-report.json").read_text(encoding="utf-8")
        )
        run_id, mode = training.get("wandbRunId"), training.get("wandbMode")
        settings = (
            training.get("config", {}).get("wandb")
            if isinstance(training.get("config"), dict)
            else None
        )
        if not run_id or not settings or mode == "disabled":
            return
        import wandb

        run = wandb.init(
            entity=settings.get("entity"),
            project=settings["project"],
            id=run_id,
            resume="allow",
            mode=_mode(os.environ.get("WANDB_MODE", mode or "online")),
        )
        payload: dict[str, Any] = {
            "test/accuracy": report.get("accuracy"),
            "test/macroF1": report.get("macroF1"),
        }
        for meaning, value in (report.get("perMeaningRecall") or {}).items():
            payload[f"test/recall/{meaning}"] = value
        if matrix is not None and matrix.exists():
            payload["test/confusion_matrix"] = wandb.Image(str(matrix))
        run.log(payload)
        for key in ("accuracy", "macroF1"):
            run.summary[f"test/{key}"] = report.get(key)
        run.finish()
    except ImportError:
        return
    except Exception as error:  # noqa: BLE001
        _warn(f"ghi metric test that bai: {error}")
