# ai/tests/training/test_augmentation.py
"""Tang cuong du lieu chi cho tap train: giu hinh dang tensor, giu diem khong hop le bang 0, tat thi khong doi."""

import numpy as np
import pytest
import torch
from visign_ai.training.augmentation import (
    AugmentedDataset,
    augment,
    validate_augmentation,
)

POINTS = 78


def sample(frames: int = 32) -> np.ndarray:
    rng = np.random.default_rng(0)
    coords = rng.normal(0, 1, (frames, POINTS * 2)).astype(np.float32)
    valid: np.ndarray = np.ones((frames, POINTS), dtype=np.float32)
    valid[:, 60:] = 0  # mot nhom diem khong thay
    coords.reshape(frames, POINTS, 2)[valid == 0] = 0
    return np.concatenate([coords, valid], axis=1)


def test_zero_parameters_keep_features_unchanged() -> None:
    features = sample()
    params = validate_augmentation({})
    np.testing.assert_allclose(
        augment(features, params, np.random.default_rng(1)), features
    )


def test_augmentation_keeps_shape_flags_and_zero_for_missing_points() -> None:
    features = sample()
    params = validate_augmentation(
        {"noise_std": 0.08, "time_warp": 0.35, "scale": 0.2, "rotate_deg": 20}
    )
    out = augment(features, params, np.random.default_rng(2))
    assert out.shape == features.shape and out.dtype == np.float32
    valid = out[:, 2 * POINTS :]
    assert set(np.unique(valid)) <= {0.0, 1.0}
    coords = out[:, : 2 * POINTS].reshape(32, POINTS, 2)
    assert np.all(coords[valid == 0] == 0)
    assert not np.allclose(out, features)


@pytest.mark.parametrize(
    "config",
    [
        {"noise_std": -0.1},
        {"time_warp": 1.0},
        {"scale": 1.5},
        {"rotate_deg": True},
        {"unknown": 0.1},
        [0.1],
    ],
)
def test_invalid_augmentation_config_is_rejected(config: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        validate_augmentation(config)


def test_augmented_dataset_is_deterministic_for_a_seed() -> None:
    features = torch.from_numpy(sample())
    base = [(features, 3)]
    params = validate_augmentation({"noise_std": 0.05, "time_warp": 0.2})
    first = AugmentedDataset(base, params, seed=42)[0]  # type: ignore[arg-type]
    second = AugmentedDataset(base, params, seed=42)[0]  # type: ignore[arg-type]
    torch.testing.assert_close(first[0], second[0])
    assert first[1] == 3
