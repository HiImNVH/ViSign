# ai/src/visign_ai/training/training_inputs.py
"""Doc dau vao da duyet cho training CLI."""

import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from visign_ai.landmarks.sequence_transform import load_schema

from .augmentation import validate_augmentation
from .group_weights import feature_scale, validate_group_weights

SPLITS = ("train", "validation", "test")
MANIFEST_FIELDS = {
    "sampleId",
    "classLabel",
    "meaningId",
    "landmarkPath",
    "split",
    "recordingSessionId",
    "licenseStatus",
    "verificationStatus",
}


@dataclass(frozen=True)
class TrainingInputs:
    schema: dict[str, Any]
    config: dict[str, Any]
    rows: list[dict[str, str]]
    labels: list[str]
    meaning_map: dict[str, str]
    display_text_map: dict[str, str]
    manifest_sha256: str
    split_audit: dict[str, Any]


def read_csv(data: bytes, required: set[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(
        io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True
    )
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or required - set(fields):
        raise ValueError(f"CSV needs unique columns including {sorted(required)}")
    rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError("CSV is empty or has inconsistent columns")
    return rows


def read_config(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise TypeError("Training config must be a YAML mapping")
    for field in (
        "seed",
        "hidden_size",
        "num_layers",
        "batch_size",
        "epochs",
        "min_meanings",
        "max_meanings",
        "input_size",
        "target_frame_count",
    ):
        value = config.get(field)
        if type(value) is not int or value < 1:
            raise ValueError(f"{field} must be a positive integer")
    if config["seed"] > 2**32 - 1:
        raise ValueError("seed exceeds the NumPy seed range")
    bounds = (config["min_meanings"], config["max_meanings"])
    if (
        config.get("artifact_kind") == "pilot" and 1 <= bounds[0] <= bounds[1] <= 3
    ) or (config.get("artifact_kind") == "full" and bounds == (10, 10)):
        pass
    else:
        raise ValueError("Meaning limits must match the pilot or full artifact kind")
    if (config["input_size"], config["target_frame_count"]) != (
        3 * len(schema["landmarkOrder"]),
        schema["targetFrameCount"],
    ):
        raise ValueError("Training config does not match feature schema dimensions")
    rate = config.get("learning_rate")
    if (
        not isinstance(rate, int | float)
        or isinstance(rate, bool)
        or not math.isfinite(rate)
        or rate <= 0
    ):
        raise ValueError("learning_rate must be finite and positive")
    candidates = config.get("threshold_candidates")
    if (
        not isinstance(candidates, list)
        or not candidates
        or any(
            type(value) not in (int, float) or not 0 < value < 1 for value in candidates
        )
    ):
        raise ValueError("threshold_candidates must be a nonempty list in (0, 1)")
    # Trong so nhom diem la tuy chon de giu tai lap cac artifact cu; neu co phai hop le voi schema
    if config.get("augmentation"):
        config["augmentation"] = validate_augmentation(config["augmentation"])
    if "group_weights" in config:
        config["group_weights"] = validate_group_weights(config["group_weights"])
        feature_scale(schema["landmarkOrder"], config["group_weights"])
    return config


def read_class_map(path: Path) -> dict[str, tuple[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError("Class map must be a nonempty JSON object")
    mapping: dict[str, tuple[str, str]] = {}
    for label, item in raw.items():
        if not label.strip() or not isinstance(item, dict):
            raise ValueError("Invalid class map entry")
        meaning, display = item.get("meaningId"), item.get("displayText")
        if not isinstance(meaning, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*", meaning
        ):
            raise ValueError(f"Invalid meaningId for {label}")
        if not isinstance(display, str) or not display.strip():
            raise ValueError(f"Missing displayText for {label}")
        mapping[label] = meaning, display.strip()
    return mapping


def audit_rows(
    rows: list[dict[str, str]], meaning_map: dict[str, str]
) -> dict[str, Any]:
    ids: set[str] = set()
    sessions: dict[str, str] = {}
    classes_by_split: dict[str, set[str]] = {split: set() for split in SPLITS}
    counts: Counter[str] = Counter()
    for row in rows:
        sample_id, split, label = row["sampleId"], row["split"], row["classLabel"]
        if not sample_id.strip() or sample_id in ids:
            raise ValueError("Manifest sampleId must be nonempty and unique")
        ids.add(sample_id)
        if row["licenseStatus"] != "approved" or row["verificationStatus"] not in (
            "verified",
            "unverified",
        ):
            raise ValueError(f"{sample_id}: sample has not passed the data intake gate")
        session = row["recordingSessionId"]
        if (
            not session.strip()
            or split not in SPLITS
            or not row["landmarkPath"].strip()
        ):
            raise ValueError(f"{sample_id}: missing session, split or landmarkPath")
        if sessions.setdefault(session, split) != split:
            raise ValueError(f"recordingSessionId leakage across splits: {session}")
        if row["meaningId"] != meaning_map[label]:
            raise ValueError(f"{sample_id}: meaningId does not match class map")
        classes_by_split[split].add(label)
        counts[split] += 1
    for split, labels in classes_by_split.items():
        if labels != set(meaning_map):
            raise ValueError(f"{split} must contain each selected class")
    return {
        "mode": "video-held-out",
        "sampleCounts": dict(counts),
        "sessionCount": len(sessions),
    }


def prepare_inputs(args: Any) -> TrainingInputs:
    schema = load_schema(args.schema)
    if schema.get("status") != "APPROVED":
        raise ValueError("APPROVED feature schema is required before training")
    config = read_config(args.config, schema)
    class_map = read_class_map(args.class_map)
    raw = args.manifest.read_bytes()
    rows = read_csv(raw, MANIFEST_FIELDS)
    requested = args.classes or list(dict.fromkeys(row["classLabel"] for row in rows))
    if len(requested) != len(set(requested)) or set(requested) - class_map.keys():
        raise ValueError("Class subset contains duplicate or unknown labels")
    selected = set(requested)
    labels = [label for label in class_map if label in selected]
    meaning_map = {label: class_map[label][0] for label in labels}
    display: dict[str, str] = {}
    for label in labels:
        meaning, text = class_map[label]
        if display.setdefault(meaning, text) != text:
            raise ValueError(f"Inconsistent displayText for {meaning}")
    if not config["min_meanings"] <= len(display) <= config["max_meanings"]:
        raise ValueError("Selected meaning count is outside the training preset")
    if config["artifact_kind"] == "full":
        if args.p0_meanings is None:
            raise ValueError("Full training requires --p0-meanings")
        catalog = read_csv(args.p0_meanings.read_bytes(), {"meaningId"})
        if len(catalog) != 10 or {row["meaningId"] for row in catalog} != set(display):
            raise ValueError("Full class subset must match the ten P0 meanings")
    rows = [row for row in rows if row["classLabel"] in selected]
    return TrainingInputs(
        schema,
        config,
        rows,
        labels,
        meaning_map,
        display,
        hashlib.sha256(raw).hexdigest(),
        audit_rows(rows, meaning_map),
    )
