# ai/tests/test_pilot_runner.py
"""T110: runner pilot cho cong cu admin chay prepare -> train (co trong so nhom) -> evaluate."""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml
from visign_ai import pilot
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training.group_weights import DEFAULT_GROUP_WEIGHTS

CLASSES = {
    "GIAY_TO_HCM_1": {"meaningId": "GIAY_TO", "displayText": "Giấy tờ"},
    "NHAN_HCM_1": {"meaningId": "NHAN", "displayText": "Nhận"},
}


class Progress:
    def __init__(self) -> None:
        self.epochs: list[tuple[int, int]] = []
        self.evaluated = False

    def epoch(self, done: int, total: int) -> None:
        self.epochs.append((done, total))

    def evaluating(self) -> None:
        self.evaluated = True


def fake_extract(path: Path, _model_dir: Path | None) -> dict[str, Any]:
    # Tensor tong hop phan biet duoc theo lop (byte dau cua "video" ma hoa lop)
    level = path.read_bytes()[0] / 255
    tensor: np.ndarray[Any, np.dtype[np.float32]] = np.full(
        (32, 234), level, dtype=np.float32
    )
    tensor[:, 156:] = 1
    return {
        "schema": load_schema(),
        "tensor": tensor,
        "tensor_mask": tensor[:, 156:] == 1,
        "target": np.linspace(0, 1000, 32),
        "report": {"inputStatus": "HAS_USABLE_FRAMES"},
    }


def make_handoff(root: Path, *, broken: str | None = None) -> pilot.FilePilotRunner:
    (root / "videos").mkdir(parents=True)
    rows: list[dict[str, str]] = []
    for split in ("train", "train", "validation", "test"):
        for index, (label, info) in enumerate(CLASSES.items()):
            content = (
                bytes([40 + 160 * index]) + f"{split}-{label}-{len(rows)}".encode()
            )
            name = f"videos/{len(rows)}.mp4"
            (root / name).write_bytes(content)
            sample_id = f"ds_{hashlib.sha256(content).hexdigest()[:12]}"
            rows.append(
                {
                    "sampleId": sample_id,
                    "classLabel": label,
                    "meaningId": info["meaningId"],
                    "recordingSessionId": sample_id,
                    "licenseStatus": "approved",
                    "verificationStatus": "unverified",
                    "split": split,
                    "rawPath": name,
                }
            )
    if broken == "hash":
        rows[0]["sampleId"] = "ds_000000000000"
    if broken == "rejected":
        for row in rows:
            row["verificationStatus"] = "rejected"
    with (root / "manifest.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (root / "class-map.json").write_text(
        json.dumps(CLASSES, ensure_ascii=False), encoding="utf-8"
    )
    config = yaml.safe_load(pilot.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    config.update(epochs=3, hidden_size=4, batch_size=2)
    (root / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    return pilot.FilePilotRunner(
        handoff=root,
        manifest=root / "manifest.csv",
        class_map=root / "class-map.json",
        config=root / "config.yaml",
        extract=fake_extract,
    )


def test_prepare_train_and_evaluate_through_the_shared_cli(tmp_path: Path) -> None:
    runner = make_handoff(tmp_path / "handoff")
    run = tmp_path / "runs" / "pilot-1"
    run.mkdir(parents=True)
    progress = Progress()
    prepared = runner.prepare(run, progress)
    assert (prepared.sampleTotal, prepared.accepted) == (8, 8)
    assert prepared.featureSchemaVersion == load_schema()["featureSchemaVersion"]
    assert prepared.datasetVersion.startswith(
        "pilot-admin-"
    ) and prepared.datasetVersion.endswith("-v1")
    trained = runner.train(run, progress)
    assert progress.epochs == [(1, 3), (2, 3), (3, 3)] and progress.evaluated
    assert trained.epochs == 3
    assert trained.accuracy is not None and 0 <= trained.accuracy <= 1
    assert trained.macroF1 is not None and 0 <= trained.macroF1 <= 1
    checkpoint = torch.load(run / "artifact" / "model.pt", weights_only=True)
    assert checkpoint["groupWeights"] == DEFAULT_GROUP_WEIGHTS
    info = json.loads(
        (run / "artifact" / "model_info.json").read_text(encoding="utf-8")
    )
    assert info["artifactKind"] == "pilot" and info["demoReady"] is False
    assert (run / "evaluation" / "evaluation-report.json").is_file()


def test_bad_samples_are_skipped_and_reported_without_failing_prepare(
    tmp_path: Path,
) -> None:
    runner = make_handoff(tmp_path / "handoff", broken="hash")
    run = tmp_path / "run"
    run.mkdir()
    prepared = runner.prepare(run, Progress())
    assert (prepared.sampleTotal, prepared.accepted) == (8, 7)
    report = json.loads((run / pilot.PREPARE_REPORT).read_text(encoding="utf-8"))
    assert report["rejected"] == [
        {"sampleId": "ds_000000000000", "code": "SAMPLE_HASH_MISMATCH"}
    ]
    with (run / pilot.FEATURE_MANIFEST).open(encoding="utf-8") as stream:
        kept = [row["sampleId"] for row in csv.DictReader(stream)]
    assert "ds_000000000000" not in kept and len(kept) == 7


def test_rejected_samples_fail_training_checks_as_input_errors(tmp_path: Path) -> None:
    runner = make_handoff(tmp_path / "handoff", broken="rejected")
    run = tmp_path / "run"
    run.mkdir()
    with pytest.raises(pilot.PilotInputError) as raised:
        runner.prepare(run, Progress())
    assert raised.value.is_pilot_input_error is True


def test_paths_outside_the_handoff_and_missing_columns_are_rejected(
    tmp_path: Path,
) -> None:
    runner = make_handoff(tmp_path / "handoff")
    manifest = tmp_path / "handoff" / "manifest.csv"
    with manifest.open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rows[0]["rawPath"] = "../outside.mp4"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    run = tmp_path / "run"
    run.mkdir()
    prepared = runner.prepare(run, Progress())
    assert prepared.accepted == 7
    report = json.loads((run / pilot.PREPARE_REPORT).read_text(encoding="utf-8"))
    assert {
        "sampleId": rows[0]["sampleId"],
        "code": "SOURCE_OUTSIDE_HANDOFF",
    } in report["rejected"]
    manifest.write_text("sampleId\nx\n", encoding="utf-8")
    with pytest.raises(pilot.PilotInputError, match="thiếu cột"):
        runner.prepare(tmp_path / "run2", Progress())


def test_train_without_prepare_is_an_input_error(tmp_path: Path) -> None:
    runner = make_handoff(tmp_path / "handoff")
    with pytest.raises(pilot.PilotInputError):
        runner.train(tmp_path, Progress())


def test_runner_is_built_only_when_a_handoff_is_configured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("VISIGN_PILOT_HANDOFF", raising=False)
    assert pilot.build_pilot_runner() is None
    monkeypatch.setenv("VISIGN_PILOT_HANDOFF", str(tmp_path))
    monkeypatch.setenv("VISIGN_PILOT_MANIFEST", "manifests/pilot-v1.csv")
    runner = pilot.build_pilot_runner()
    assert runner is not None
    assert runner.manifest == tmp_path / "manifests" / "pilot-v1.csv"
    assert pilot._dataset_version(runner.manifest, "ab" * 32) == "pilot-v1"
