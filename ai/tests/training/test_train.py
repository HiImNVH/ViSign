# ai/tests/training/test_train.py
"""Kiem tra T036 tren tensor tong hop."""

import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml
from numpy.typing import NDArray
from visign_ai.landmarks.extract_manifest import write_sequence
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training import train


@pytest.fixture
def training_files(
    tmp_path: Path, request: pytest.FixtureRequest
) -> tuple[list[str], dict[str, Any]]:
    schema = load_schema()
    schema["status"] = "APPROVED"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    class_map = {
        "SOT_HCM_1": {"meaningId": "SOT", "displayText": "Sốt"},
        "CAM_ON_HN_1": {"meaningId": "CAM_ON", "displayText": "Cảm ơn"},
        "NHAN_HCM_1": {"meaningId": "NHAN", "displayText": "Nhận"},
    }
    if getattr(request, "param", "pilot") == "full":
        for index in range(7):
            meaning = f"FIXTURE_{index}"
            class_map[f"{meaning}_HCM_1"] = {
                "meaningId": meaning,
                "displayText": meaning,
            }
    (tmp_path / "class-map.json").write_text(
        json.dumps(class_map, ensure_ascii=False), encoding="utf-8"
    )
    rows = []
    for split in ("train", "validation", "test"):
        for index, (label, info) in enumerate(class_map.items()):
            sample_id = f"{split}-{index}"
            filename = f"{sample_id}.npz"
            features: NDArray[np.float32] = np.full(
                (32, 234), index / 2, dtype=np.float32
            )
            features[:, 156:] = 1
            if split != "test":
                write_sequence(
                    tmp_path / filename,
                    sample_id,
                    {
                        "schema": schema,
                        "tensor": features,
                        "tensor_mask": features[:, 156:] == 1,
                        "target": np.linspace(0, 1000, 32),
                    },
                )
            rows.append(
                {
                    "sampleId": sample_id,
                    "classLabel": label,
                    "meaningId": info["meaningId"],
                    "landmarkPath": filename,
                    "split": split,
                    "recordingSessionId": sample_id,
                    "licenseStatus": "approved",
                    "verificationStatus": "verified",
                }
            )
    with (tmp_path / "pilot.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    config = {
        "artifact_kind": "pilot",
        "min_meanings": 1,
        "max_meanings": 3,
        "input_size": 234,
        "target_frame_count": 32,
        "seed": 42,
        "hidden_size": 4,
        "num_layers": 1,
        "batch_size": 2,
        "epochs": 2,
        "learning_rate": 0.001,
        "threshold_candidates": [0.5, 0.7],
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    return [
        "train",
        "--manifest",
        str(tmp_path / "pilot.csv"),
        "--class-map",
        str(tmp_path / "class-map.json"),
        "--feature-root",
        str(tmp_path),
        "--schema",
        str(schema_path),
        "--config",
        str(tmp_path / "config.yaml"),
        "--dataset-version",
        "pilot-v1",
        "--model-version",
        "test-v1",
        "--classes",
        "CAM_ON_HN_1",
        "SOT_HCM_1",
    ], schema


def test_cli_training_is_repeatable_and_does_not_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    args, schema = training_files
    expected_labels = ["SOT_HCM_1", "CAM_ON_HN_1"]
    with torch.random.fork_rng(devices=[]):
        checkpoints = []
        for name in ("first", "second"):
            output = tmp_path / name
            monkeypatch.setattr(sys, "argv", [*args, "--output", str(output)])
            assert train.main() == 0
            assert {file.name for file in output.iterdir()} == {
                "model.pt",
                "model_info.json",
                "feature_schema.json",
                "training-report.json",
            }
            info = json.loads((output / "model_info.json").read_text(encoding="utf-8"))
            report = json.loads(
                (output / "training-report.json").read_text(encoding="utf-8")
            )
            checkpoint = torch.load(output / "model.pt", weights_only=True)
            assert info["classLabels"] == expected_labels
            assert (
                info["artifactKind"] == "pilot" and info["datasetVersion"] == "pilot-v1"
            )
            assert info["demoReady"] is False and info["accuracy"] is None
            assert checkpoint["schemaSha256"] == schema_digest(schema)
            assert checkpoint["modelConfig"]["num_classes"] == 2
            assert checkpoint["labelBinding"]["classLabels"] == expected_labels
            assert report["splitAudit"]["sampleCounts"] == {
                "train": 2,
                "validation": 2,
                "test": 2,
            }
            assert len(report["history"]) == 2
            assert info["acceptanceThreshold"] in (0.5, 0.7)
            checkpoints.append(checkpoint)
        for key, tensor in checkpoints[0]["stateDict"].items():
            torch.testing.assert_close(
                tensor, checkpoints[1]["stateDict"][key], rtol=0, atol=0
            )
        original = (output / "model.pt").read_bytes()
        assert train.main() == 2
        assert (output / "model.pt").read_bytes() == original


@pytest.mark.parametrize("case", ["draft", "leakage", "rights"])
def test_cli_rejects_blocked_data_without_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
    case: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, schema = training_files
    if case == "draft":
        schema["status"] = "DRAFT_PENDING_LEAD_REVIEW"
        (tmp_path / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    else:
        path = tmp_path / "pilot.csv"
        raw = path.read_text(encoding="utf-8")
        if case == "rights":
            raw = raw.replace(",approved,verified", ",unknown,verified", 1)
        else:
            raw = raw.replace(",validation,validation-0,", ",validation,train-0,", 1)
        path.write_text(raw, encoding="utf-8")
    output = tmp_path / "blocked"
    monkeypatch.setattr(sys, "argv", [*args, "--output", str(output)])
    assert train.main() == 2
    assert not output.exists()
    expected = {"draft": "APPROVED", "leakage": "leakage", "rights": "data intake gate"}
    assert expected[case] in capsys.readouterr().err


@pytest.mark.parametrize("training_files", ["full"], indirect=True)
def test_full_cli_requires_exact_p0_catalog(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    args, _ = training_files
    config = tmp_path / "config.yaml"
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update(artifact_kind="full", min_meanings=10, max_meanings=10, epochs=1)
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    catalog = tmp_path / "p0-meanings.csv"
    mapping = json.loads((tmp_path / "class-map.json").read_text(encoding="utf-8"))
    meanings = [item["meaningId"] for item in mapping.values()]
    output = tmp_path / "full"
    cli = [
        *args[: args.index("--classes")],
        "--p0-meanings",
        str(catalog),
        "--output",
        str(output),
    ]
    monkeypatch.setattr(sys, "argv", cli)
    catalog.write_text(
        "meaningId\n" + "\n".join([*meanings[:-1], "OTHER"]) + "\n", encoding="utf-8"
    )
    assert train.main() == 2
    assert not output.exists()
    catalog.write_text("meaningId\n" + "\n".join(meanings) + "\n", encoding="utf-8")
    assert train.main() == 0
    info = json.loads((output / "model_info.json").read_text(encoding="utf-8"))
    assert info["artifactKind"] == "full"
    assert info["meanings"] == meanings and info["demoReady"] is False
