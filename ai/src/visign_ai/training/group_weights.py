# ai/src/visign_ai/training/group_weights.py
"""Trong so dong gop theo nhom diem landmark (lead quyet dinh 2026-11-08).

Tay la phan chinh de nhan biet tu (0,7), mat bieu thi cam xuc va dong gop phu (0,2), vai/canh tay la phan neo cho biet
tay o dau so voi co the (0,1). Moi diem co 2 toa do + 1 co hop le trong tensor 234; he so cua mot nhom duoc chon sao
cho tong dong gop cua nhom do ty le voi trong so: he_so = trong_so * tong_so_diem / so_diem_cua_nhom.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Any

GROUP_PREFIXES: dict[str, tuple[str, ...]] = {
    "hands": ("LEFT_HAND_", "RIGHT_HAND_"),
    "face": ("FACE_",),
    "shoulders": ("POSE_",),
}
DEFAULT_GROUP_WEIGHTS: dict[str, float] = {"hands": 0.7, "face": 0.2, "shoulders": 0.1}


def validate_group_weights(weights: Any) -> dict[str, float]:
    """Dung du ba nhom, so duong huu han, tong bang 1."""
    if not isinstance(weights, Mapping) or set(weights) != set(GROUP_PREFIXES):
        raise ValueError("group_weights must define exactly hands, face and shoulders")
    checked: dict[str, float] = {}
    for group, value in weights.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"group_weights.{group} must be a number")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"group_weights.{group} must be positive and finite")
        checked[group] = float(value)
    if not math.isclose(sum(checked.values()), 1.0, abs_tol=1e-6):
        raise ValueError("group_weights must sum to 1")
    return checked


def group_of(landmark: str) -> str:
    for group, prefixes in GROUP_PREFIXES.items():
        if landmark.startswith(prefixes):
            return group
    raise ValueError(f"Landmark {landmark} does not belong to a weighted group")


def feature_scale(
    landmark_order: Sequence[str], weights: Mapping[str, float]
) -> list[float]:
    """He so cho 234 dac trung: 78 cap XY (diem-major) roi 78 co hop le, cung he so theo diem."""
    checked = validate_group_weights(weights)
    groups = [group_of(name) for name in landmark_order]
    counts = {group: groups.count(group) for group in GROUP_PREFIXES}
    missing = [group for group, count in counts.items() if count == 0]
    if missing:
        raise ValueError(f"Feature schema has no landmarks for {missing}")
    total = len(groups)
    per_point = [checked[group] * total / counts[group] for group in groups]
    return [scale for scale in per_point for _ in range(2)] + per_point
