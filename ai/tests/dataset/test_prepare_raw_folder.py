# ai/tests/dataset/test_prepare_raw_folder.py
"""Quet thu muc raw theo quy uoc `<VUNG>_<Nghia>_<so>.mp4` va chia tap theo lop."""

import hashlib
from collections import Counter
from pathlib import Path

from visign_ai.dataset.prepare_raw_folder import assign_splits, scan


def write(root: Path, folder: str, name: str, content: bytes) -> None:
    (root / folder).mkdir(parents=True, exist_ok=True)
    (root / folder / name).write_bytes(content)


def test_scan_maps_vietnamese_names_regions_and_hashes(tmp_path: Path) -> None:
    write(tmp_path, "1. Giấy", "HCM_Giấy_1.mp4", b"a")
    write(tmp_path, "6. Cảm ơn", "hn_Cảm ơn_2.mp4", b"b")
    write(tmp_path, "6. Cảm ơn", "Cam on.mp4", b"c")
    write(tmp_path, "6. Cảm ơn", "HCM_Ăn_1.mp4", b"d")
    rows, skipped = scan(tmp_path)
    labels = {row["rawPath"]: row["classLabel"] for row in rows}
    assert labels == {
        "1. Giấy/HCM_Giấy_1.mp4": "GIAY_TO_HCM_1",
        "6. Cảm ơn/hn_Cảm ơn_2.mp4": "CAM_ON_HN_1",
    }
    first = next(row for row in rows if row["classLabel"] == "GIAY_TO_HCM_1")
    assert first["sampleId"] == f"raw-p0_{hashlib.sha256(b'a').hexdigest()[:12]}"
    assert first["recordingSessionId"] == first["sampleId"]
    assert (first["licenseStatus"], first["verificationStatus"]) == (
        "approved",
        "unverified",
    )
    assert {item["code"] for item in skipped} == {
        "NAME_NOT_CONVENTION",
        "UNKNOWN_MEANING_OR_REGION",
    }


def test_splits_are_per_class_deterministic_and_cover_every_split(
    tmp_path: Path,
) -> None:
    for index in range(20):
        write(tmp_path, "3. Sốt", f"HCM_Sốt_{index}.mp4", f"sot{index}".encode())
    for index in range(6):
        write(tmp_path, "4. Nhận", f"HN_Nhận_{index}.mp4", f"nhan{index}".encode())
    rows, _ = scan(tmp_path)
    assign_splits(rows, seed=42)
    first = {row["sampleId"]: row["split"] for row in rows}
    rows_again, _ = scan(tmp_path)
    assign_splits(rows_again, seed=42)
    assert first == {row["sampleId"]: row["split"] for row in rows_again}
    for label in ("SOT_HCM_1", "NHAN_HN_1"):
        counts = Counter(row["split"] for row in rows if row["classLabel"] == label)
        assert (
            counts["test"] >= 1 and counts["validation"] >= 1 and counts["train"] >= 1
        )
    sot = Counter(row["split"] for row in rows if row["classLabel"] == "SOT_HCM_1")
    # 70/20/10 theo quyet dinh lead
    assert sot == {"train": 14, "validation": 4, "test": 2}
