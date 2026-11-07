# services/inference-api/tests/integration/t036_artifact_builder.py
# Dung artifact pilot/full that bang CLI train T036 tren tensor tong hop cho test tich hop API va T064.
# Chi import sau khi da kiem extra serving (torch, visign_ai) de CI khong co torch van collect duoc.
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from numpy.typing import NDArray
from visign_ai.landmarks.extract_manifest import write_sequence
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training import train as training_cli


@dataclass(frozen=True)
class TrainingSpec:
    classMap: dict[str, dict[str, str]]
    config: dict[str, Any]
    datasetVersion: str
    modelVersion: str


@dataclass(frozen=True)
class ManifestSource:
    featureSchema: dict[str, Any]
    classMap: dict[str, dict[str, str]]


# Thu tu class map co chu y khac bang chu cai: artifact phai giu dung thu tu nay
CLASS_MAP = {
    "SOT_HCM_1": {"meaningId": "SOT", "displayText": "Sốt"},
    "CAM_ON_HN_1": {"meaningId": "CAM_ON", "displayText": "Cảm ơn"},
}
P0_MEANINGS = [
    "GIAY_TO",
    "DAU_BUNG",
    "SOT",
    "NHAN",
    "BAN",
    "CAM_ON",
    "GIUP_DO",
    "XIN_LOI",
    "DAU_DAU",
    "KHONG",
]
FULL_CLASS_MAP = {
    f"{meaning}_HCM_1": {"meaningId": meaning, "displayText": meaning.title()}
    for meaning in P0_MEANINGS
}
THRESHOLD_CANDIDATES = [0.5, 0.7]
TRAINING_CONFIG: dict[str, Any] = {
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
    "threshold_candidates": THRESHOLD_CANDIDATES,
}
MODEL_VERSION = "pilot-gru-test-v1"
PILOT_SPEC = TrainingSpec(CLASS_MAP, TRAINING_CONFIG, "pilot-v1", MODEL_VERSION)
FULL_SPEC = TrainingSpec(
    FULL_CLASS_MAP,
    {
        **TRAINING_CONFIG,
        "artifact_kind": "full",
        "min_meanings": 10,
        "max_meanings": 10,
    },
    "p0-v1",
    "full-gru-test-v1",
)
SPLITS = ("train", "validation", "test")
MANIFEST_COLUMNS = (
    "sampleId",
    "classLabel",
    "meaningId",
    "landmarkPath",
    "split",
    "recordingSessionId",
    "licenseStatus",
    "verificationStatus",
)
VALIDITY_OFFSET = 156


def approved_schema(workspace: Path) -> dict[str, Any]:
    # Schema repo con DRAFT; CLI T036 chi train tren ban APPROVED nen test duyet tren ban sao
    feature_schema = load_schema()
    feature_schema["status"] = "APPROVED"
    (workspace / "schema.json").write_text(json.dumps(feature_schema), encoding="utf-8")
    return feature_schema


def synthetic_sequence(
    feature_schema: dict[str, Any], class_index: int
) -> dict[str, Any]:
    features: NDArray[np.float32] = np.full(
        (32, 234), class_index / 2, dtype=np.float32
    )
    features[:, VALIDITY_OFFSET:] = 1
    return {
        "schema": feature_schema,
        "tensor": features,
        "tensor_mask": features[:, VALIDITY_OFFSET:] == 1,
        "target": np.linspace(0, 1000, 32),
    }


def write_manifest(workspace: Path, manifest_source: ManifestSource) -> None:
    manifest_lines = [",".join(MANIFEST_COLUMNS)]
    for split in SPLITS:
        for class_index, (class_label, class_info) in enumerate(
            manifest_source.classMap.items()
        ):
            sample_id = f"{split}-{class_index}"
            if split != "test":
                sequence = synthetic_sequence(
                    manifest_source.featureSchema, class_index
                )
                write_sequence(workspace / f"{sample_id}.npz", sample_id, sequence)
            manifest_lines.append(
                f"{sample_id},{class_label},{class_info['meaningId']},{sample_id}.npz,"
                f"{split},{sample_id},approved,verified"
            )
    (workspace / "pilot.csv").write_text("\n".join(manifest_lines), encoding="utf-8")


def p0_catalog_arguments(workspace: Path, training_spec: TrainingSpec) -> list[str]:
    # Full chi train khi class map trung dung danh muc 10 nghia P0 (registry T013)
    if training_spec.config["artifact_kind"] != "full":
        return []
    meaning_ids = [entry["meaningId"] for entry in training_spec.classMap.values()]
    catalog_path = workspace / "p0-meanings.csv"
    catalog_path.write_text(
        "meaningId\n" + "\n".join(meaning_ids) + "\n", encoding="utf-8"
    )
    return ["--p0-meanings", str(catalog_path)]


def training_arguments(workspace: Path, training_spec: TrainingSpec) -> list[str]:
    feature_schema = approved_schema(workspace)
    write_manifest(workspace, ManifestSource(feature_schema, training_spec.classMap))
    (workspace / "class-map.json").write_text(
        json.dumps(training_spec.classMap, ensure_ascii=False), encoding="utf-8"
    )
    (workspace / "config.json").write_text(
        json.dumps(training_spec.config), encoding="utf-8"
    )
    named_inputs = {
        "manifest": "pilot.csv",
        "class-map": "class-map.json",
        "feature-root": ".",
        "schema": "schema.json",
        "config": "config.json",
    }
    cli_arguments = ["train", "--dataset-version", training_spec.datasetVersion]
    for option, relative_path in named_inputs.items():
        cli_arguments += [f"--{option}", str(workspace / relative_path)]
    cli_arguments += p0_catalog_arguments(workspace, training_spec)
    return [*cli_arguments, "--model-version", training_spec.modelVersion]


def train_artifact(workspace: Path, training_spec: TrainingSpec) -> Path:
    artifact_directory = workspace / training_spec.modelVersion
    cli_arguments = [
        *training_arguments(workspace, training_spec),
        "--output",
        str(artifact_directory),
    ]
    deterministic_before = torch.are_deterministic_algorithms_enabled()
    # CLI train dat seed va che do deterministic toan cuc; khoi phuc de khong anh huong test khac
    with torch.random.fork_rng(devices=[]), pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(sys, "argv", cli_arguments)
        assert training_cli.main() == 0
    torch.use_deterministic_algorithms(deterministic_before)
    return artifact_directory
