# ai/tests/training/test_tracking.py
"""W&B tuy chon: log du epoch va ma run khi bat; loi W&B khong lam hong train."""

import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest
import yaml
from visign_ai.training import train
from visign_ai.training.tracking import validate_wandb


class FakeRun:
    def __init__(self, record: dict[str, Any]) -> None:
        self.id = "run123"
        self.url = "https://wandb.ai/e/ViSign/runs/run123"
        self.summary: dict[str, Any] = {}
        self.record = record

    def log(self, payload: dict[str, Any], step: int | None = None) -> None:
        self.record["logs"].append((payload, step))

    def finish(self) -> None:
        self.record["finished"] += 1


def fake_wandb(record: dict[str, Any], fail: bool = False) -> types.ModuleType:
    module = types.ModuleType("wandb")

    def init(**kwargs: Any) -> FakeRun:
        record["init"].append(kwargs)
        if fail:
            raise RuntimeError("api_key not configured (no-tty)")
        return FakeRun(record)

    class Table:
        def __init__(self, columns: list[str]) -> None:
            self.rows: list[tuple[Any, ...]] = []

        def add_data(self, *row: Any) -> None:
            self.rows.append(row)

    module.init = init  # type: ignore[attr-defined]
    module.Table = Table  # type: ignore[attr-defined]
    module.Image = lambda path: ("image", path)  # type: ignore[attr-defined]
    return module


def with_wandb(args: list[str], mode: str = "online") -> None:
    config_path = Path(args[args.index("--config") + 1])
    settings = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    settings["wandb"] = {
        "entity": "team",
        "project": "ViSign",
        "mode": mode,
        "tags": ["test"],
    }
    config_path.write_text(yaml.safe_dump(settings), encoding="utf-8")


def run_training(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, args: list[str]
) -> dict[str, Any]:
    output = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", [*args, "--output", str(output)])
    assert train.main() == 0
    report: dict[str, Any] = json.loads(
        (output / "training-report.json").read_text(encoding="utf-8")
    )
    return report


def test_enabled_tracking_logs_every_epoch_and_records_the_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    record: dict[str, Any] = {"init": [], "logs": [], "finished": 0}
    monkeypatch.setitem(sys.modules, "wandb", fake_wandb(record))
    monkeypatch.delenv("WANDB_MODE", raising=False)
    args, _ = training_files
    with_wandb(args)
    report = run_training(tmp_path, monkeypatch, args)
    init = record["init"][0]
    assert (init["entity"], init["project"], init["name"], init["mode"]) == (
        "team",
        "ViSign",
        "test-v1",
        "online",
    )
    assert "wandb" not in init["config"] and init["config"]["trainSamples"] == 2
    epochs = [step for payload, step in record["logs"] if "train/loss" in payload]
    assert epochs == [1, 2]
    assert record["finished"] == 1
    assert report["wandbRunId"] == "run123" and report["wandbMode"] == "online"
    assert report["wandbUrl"].endswith("/run123")


def test_tracking_failure_never_breaks_training(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    record: dict[str, Any] = {"init": [], "logs": [], "finished": 0}
    monkeypatch.setitem(sys.modules, "wandb", fake_wandb(record, fail=True))
    args, _ = training_files
    with_wandb(args)
    report = run_training(tmp_path, monkeypatch, args)
    assert len(record["init"]) == 1
    assert report["wandbRunId"] is None and report["acceptanceThreshold"] in (0.5, 0.7)


def test_disabled_mode_skips_wandb(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    record: dict[str, Any] = {"init": [], "logs": [], "finished": 0}
    monkeypatch.setitem(sys.modules, "wandb", fake_wandb(record))
    monkeypatch.setenv("WANDB_MODE", "disabled")
    args, _ = training_files
    with_wandb(args)
    report = run_training(tmp_path, monkeypatch, args)
    assert record["init"] == [] and report["wandbRunId"] is None


@pytest.mark.parametrize(
    "config",
    [
        {"entity": "x"},
        {"project": "p", "mode": "cloud"},
        {"project": "p", "tags": "a"},
        {"project": "p", "key": 1},
    ],
)
def test_invalid_wandb_config_is_rejected(config: dict[str, Any]) -> None:
    with pytest.raises((ValueError, TypeError)):
        validate_wandb(config)
