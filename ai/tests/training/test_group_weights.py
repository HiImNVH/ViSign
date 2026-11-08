# ai/tests/training/test_group_weights.py
"""Trong so nhom diem tay 0,7 / mat 0,2 / vai 0,1 (lead 2026-11-08)."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training import train
from visign_ai.training.group_weights import (
    DEFAULT_GROUP_WEIGHTS,
    feature_scale,
    group_of,
    validate_group_weights,
)
from visign_ai.training.gru_classifier import GRUClassifier

SCHEMA = load_schema()
ORDER = SCHEMA["landmarkOrder"]


def test_groups_cover_the_approved_schema() -> None:
    groups = [group_of(name) for name in ORDER]
    assert (groups.count("hands"), groups.count("shoulders"), groups.count("face")) == (
        42,
        6,
        30,
    )


def test_scale_makes_group_contribution_proportional_to_weight() -> None:
    scale = feature_scale(ORDER, DEFAULT_GROUP_WEIGHTS)
    assert len(scale) == 234
    points = len(ORDER)
    contribution = {group: 0.0 for group in DEFAULT_GROUP_WEIGHTS}
    for index, name in enumerate(ORDER):
        group = group_of(name)
        # moi diem: 2 toa do (diem-major) + 1 co hop le, cung mot he so
        assert scale[2 * index] == scale[2 * index + 1] == scale[2 * points + index]
        contribution[group] += scale[2 * points + index]
    total = sum(contribution.values())
    for group, weight in DEFAULT_GROUP_WEIGHTS.items():
        assert contribution[group] / total == pytest.approx(weight)
    hand = scale[2 * points + ORDER.index("LEFT_HAND_00")]
    face = scale[2 * points + ORDER.index("FACE_0")]
    shoulder = scale[2 * points + ORDER.index("POSE_11")]
    assert hand == pytest.approx(0.7 * 78 / 42)
    assert face == pytest.approx(0.2 * 78 / 30)
    assert shoulder == pytest.approx(0.1 * 78 / 6)


@pytest.mark.parametrize(
    "weights",
    [
        {"hands": 0.7, "face": 0.2},
        {"hands": 0.7, "face": 0.2, "shoulders": 0.2},
        {"hands": 0.8, "face": 0.3, "shoulders": -0.1},
        {"hands": True, "face": 0.2, "shoulders": 0.1},
        {"hands": float("nan"), "face": 0.2, "shoulders": 0.1},
        [0.7, 0.2, 0.1],
    ],
)
def test_invalid_weights_are_rejected(weights: Any) -> None:
    with pytest.raises((ValueError, TypeError)):
        validate_group_weights(weights)


def test_unknown_landmark_group_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not belong"):
        feature_scale([*ORDER, "NECK_01"], DEFAULT_GROUP_WEIGHTS)


def test_model_applies_scale_and_keeps_it_in_state_dict() -> None:
    torch.manual_seed(0)
    scale = feature_scale(ORDER, DEFAULT_GROUP_WEIGHTS)
    weighted = GRUClassifier(234, 8, 3, feature_scale=scale)
    plain = GRUClassifier(234, 8, 3)
    plain.load_state_dict(
        {k: v for k, v in weighted.state_dict().items() if k != "feature_scale"}
    )
    sequences = torch.randn(2, 32, 234)
    lengths = torch.tensor([32, 20])
    expected = plain(sequences * torch.tensor(scale), lengths)
    torch.testing.assert_close(weighted(sequences, lengths), expected)
    restored = GRUClassifier(234, 8, 3, feature_scale=scale)
    restored.load_state_dict(weighted.state_dict(), strict=True)
    torch.testing.assert_close(restored.feature_scale, torch.tensor(scale))


def test_models_without_scale_keep_the_old_state_dict() -> None:
    assert "feature_scale" not in GRUClassifier(234, 8, 3).state_dict()
    with pytest.raises(ValueError, match="feature_scale"):
        GRUClassifier(234, 8, 3, feature_scale=[1.0] * 233)
    with pytest.raises(ValueError, match="feature_scale"):
        GRUClassifier(234, 8, 3, feature_scale=[0.0] * 234)


def test_cli_training_stores_group_weights_with_the_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    args, _ = training_files
    config_path = Path(args[args.index("--config") + 1])
    settings = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    settings["group_weights"] = dict(DEFAULT_GROUP_WEIGHTS)
    config_path.write_text(yaml.safe_dump(settings), encoding="utf-8")
    output = tmp_path / "weighted"
    monkeypatch.setattr(sys, "argv", [*args, "--output", str(output)])
    assert train.main() == 0
    checkpoint = torch.load(output / "model.pt", weights_only=True)
    expected = feature_scale(ORDER, DEFAULT_GROUP_WEIGHTS)
    assert checkpoint["modelConfig"]["feature_scale"] == pytest.approx(expected)
    assert checkpoint["groupWeights"] == DEFAULT_GROUP_WEIGHTS
    torch.testing.assert_close(
        checkpoint["stateDict"]["feature_scale"], torch.tensor(expected)
    )
    report = json.loads((output / "training-report.json").read_text(encoding="utf-8"))
    assert report["groupWeights"] == DEFAULT_GROUP_WEIGHTS
    model = GRUClassifier(**checkpoint["modelConfig"])
    model.load_state_dict(checkpoint["stateDict"], strict=True)


def test_config_with_invalid_group_weights_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    training_files: tuple[list[str], dict[str, Any]],
) -> None:
    args, _ = training_files
    config_path = Path(args[args.index("--config") + 1])
    settings = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    settings["group_weights"] = {"hands": 0.9, "face": 0.2, "shoulders": 0.1}
    config_path.write_text(yaml.safe_dump(settings), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [*args, "--output", str(tmp_path / "bad")])
    assert train.main() != 0
    assert not (tmp_path / "bad").exists()
