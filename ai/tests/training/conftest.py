# ai/tests/training/conftest.py
"""Fixture chung cho test train: tensor tong hop, manifest, class map, schema va config pilot."""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml
from numpy.typing import NDArray
from visign_ai.landmarks.extract_manifest import write_sequence
from visign_ai.landmarks.sequence_transform import load_schema


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
