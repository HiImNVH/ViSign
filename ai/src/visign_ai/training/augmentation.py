# ai/src/visign_ai/training/augmentation.py
"""Tang cuong du lieu landmark chi cho tap train (2026-11-08).

Moi khung trong tensor 32x234 gom 78 cap toa do (diem-major, da chuan hoa ve goc giua hai vai, don vi = khoang cach
vai) roi 78 co hop le. Bien doi giu nguyen y nghia ky hieu:
- nhieu Gauss nho tren toa do diem hop le;
- co gian/dich theo thoi gian (lay mau gan nhat ca khung, toa do va co hop le di cung nhau);
- phong to/thu nho va xoay nhe quanh goc (nguoi dung gan/xa camera, nghieng nhe).
Diem khong hop le luon giu 0. Tat mac dinh; bat bang khoa `augmentation` trong config train.
"""

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import torch
from torch.utils.data import Dataset

from .sequence_dataset import SequenceSample

FIELDS = ("noise_std", "time_warp", "scale", "rotate_deg")


def validate_augmentation(config: Any) -> dict[str, float]:
    if not isinstance(config, Mapping) or set(config) - set(FIELDS):
        raise ValueError(f"augmentation chi nhan cac khoa {FIELDS}")
    checked: dict[str, float] = {}
    for key in FIELDS:
        value = config.get(key, 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"augmentation.{key} phai la so")
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"augmentation.{key} phai >= 0")
        checked[key] = float(value)
    if checked["time_warp"] >= 1 or checked["scale"] >= 1:
        raise ValueError("augmentation.time_warp va scale phai < 1")
    return checked


def augment(
    features: np.ndarray, params: Mapping[str, float], rng: np.random.Generator
) -> np.ndarray:
    frames, width = features.shape
    points = width // 3
    coords = features[:, : 2 * points].reshape(frames, points, 2).copy()
    valid = features[:, 2 * points :].copy()

    warp = params["time_warp"]
    if warp > 0:
        speed = rng.uniform(1 - warp, 1 + warp)
        shift = rng.uniform(-warp, warp) * frames / 2
        centre = (frames - 1) / 2
        source = np.clip(
            np.rint((np.arange(frames) - centre) * speed + centre + shift),
            0,
            frames - 1,
        )
        index = source.astype(np.int64)
        coords, valid = coords[index], valid[index]

    scale = params["scale"]
    angle = math.radians(params["rotate_deg"])
    if scale > 0 or angle > 0:
        factor = rng.uniform(1 - scale, 1 + scale)
        theta = rng.uniform(-angle, angle)
        rotation = np.array(
            [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
        )
        coords = coords @ rotation.T * factor

    if params["noise_std"] > 0:
        coords = coords + rng.normal(0, params["noise_std"], coords.shape)

    coords = coords * valid[:, :, None]
    return np.concatenate([coords.reshape(frames, 2 * points), valid], axis=1).astype(
        np.float32
    )


class AugmentedDataset(Dataset[SequenceSample]):
    def __init__(
        self, base: Dataset[SequenceSample], params: Mapping[str, float], seed: int
    ) -> None:
        self.base = base
        self.params = dict(params)
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.base)  # type: ignore[arg-type]

    def __getitem__(self, index: int) -> SequenceSample:
        features, label = self.base[index]
        return torch.from_numpy(augment(features.numpy(), self.params, self.rng)), label
