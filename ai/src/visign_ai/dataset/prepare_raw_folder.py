# ai/src/visign_ai/dataset/prepare_raw_folder.py
"""Dung bo du lieu train tu thu muc raw theo quy uoc `<so>. <Nghia>/<VUNG>_<Nghia>_<so>.mp4`.

Lead chot 2026-11-08: raw nam ngoai repo (vd `A:/Project/5HVT/data/raw`). Script:
1. nhan dien nghia (registry P0) va vung tu ten file, lop = `<MEANING>_<VUNG>_1`;
2. `sampleId` = `raw-p0_<12 hex dau SHA-256 video>`; moi file la mot video goc rieng (`recordingSessionId` = sampleId)
   vi chua co thong tin clip nao cat tu cung video -> bao cao ghi `video-held-out`, khong tuyen bo unseen-signer;
3. bo lop co qua it clip (mac dinh < 6) de chia du train/validation/test, ghi lai trong bao cao;
4. chia tap theo tung lop theo ty le lead chot 70/20/10 (train/validation/test), seed co dinh, moi tap it nhat 1 clip;
5. trich landmark bang pipeline dung chung (song song nhieu tien trinh), clip loi/qua dai bi loai co ma loi;
6. ghi `manifest.csv`, `class-map.json`, `prepare-report.json` va `features/*.npz` vao thu muc output (ngoai Git).
Quyen su dung khai mot lan o muc bo du lieu (`licenseStatus=approved`), nhan `unverified`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path
from typing import Any

MEANINGS = {
    "giấy": "GIAY_TO",
    "đau bụng": "DAU_BUNG",
    "sốt": "SOT",
    "nhận": "NHAN",
    "bạn": "BAN",
    "cảm ơn": "CAM_ON",
    "giúp đỡ": "GIUP_DO",
    "xin lỗi": "XIN_LOI",
    "đau đầu": "DAU_DAU",
    "không": "KHONG",
}
# Lead chot 2026-11-08: 70% train, 20% validation, 10% test
VALIDATION_RATIO = 0.2
TEST_RATIO = 0.1
REGIONS = {"HCM", "HN", "HP", "OTHER", "UNKNOWN"}
FILE_PATTERN = re.compile(
    r"(?P<region>[A-Za-z]+)_(?P<meaning>.+)_(?P<number>\d+)\.mp4", re.IGNORECASE
)
FIELDS = (
    "sampleId",
    "classLabel",
    "meaningId",
    "recordingSessionId",
    "licenseStatus",
    "verificationStatus",
    "split",
    "rawPath",
    "landmarkPath",
)


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip().lower()


def scan(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.mp4")):
        match = FILE_PATTERN.fullmatch(unicodedata.normalize("NFC", path.name))
        relative = path.relative_to(root).as_posix()
        if not match:
            skipped.append({"rawPath": relative, "code": "NAME_NOT_CONVENTION"})
            continue
        meaning = MEANINGS.get(normalize(match["meaning"]))
        region = match["region"].upper()
        if meaning is None or region not in REGIONS:
            skipped.append({"rawPath": relative, "code": "UNKNOWN_MEANING_OR_REGION"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sample_id = f"raw-p0_{digest[:12]}"
        rows.append(
            {
                "sampleId": sample_id,
                "classLabel": f"{meaning}_{region}_1",
                "meaningId": meaning,
                "recordingSessionId": sample_id,
                "licenseStatus": "approved",
                "verificationStatus": "unverified",
                "split": "",
                "rawPath": relative,
                "landmarkPath": "",
            }
        )
    return rows, skipped


def assign_splits(rows: list[dict[str, str]], seed: int) -> None:
    by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_class[row["classLabel"]].append(row)
    rng = random.Random(seed)
    for label in sorted(by_class):
        members = sorted(by_class[label], key=lambda row: row["sampleId"])
        rng.shuffle(members)
        count = len(members)
        test = max(1, round(count * TEST_RATIO))
        validation = max(1, round(count * VALIDATION_RATIO))
        for index, row in enumerate(members):
            row["split"] = (
                "test"
                if index < test
                else "validation"
                if index < test + validation
                else "train"
            )


# File lon hon gioi han upload cua API (10 MiB) thuong la video 1080p60 quay bang dien thoai: chuan hoa ve dang camera
# trinh duyet gui len (WebM VP8, rong 640 px, 30 fps, giu ti le) truoc khi trich landmark.
TRANSCODE_ABOVE_BYTES = 10 * 1024 * 1024
TRANSCODE_WIDTH = 640
TRANSCODE_FPS = 30


def transcode_like_browser(source: Path, target: Path) -> None:
    import av

    with av.open(str(source)) as input_container, av.open(str(target), "w") as output:
        video = input_container.streams.video[0]
        width = TRANSCODE_WIDTH
        height = (
            round(video.codec_context.height * width / video.codec_context.width / 2)
            * 2
        )
        stream = output.add_stream("libvpx", rate=TRANSCODE_FPS)
        stream.width, stream.height, stream.pix_fmt = width, height, "yuv420p"
        stream.bit_rate = 1_500_000
        next_time = 0.0
        written = 0
        for frame in input_container.decode(video):
            if frame.time is None or frame.time + 1e-6 < next_time:
                continue
            next_time += 1 / TRANSCODE_FPS
            scaled = frame.reformat(width=width, height=height, format="yuv420p")
            # Danh lai PTS tuan tu theo 30 fps; giu PTS goc 60 fps lam timestamp trung/khong tang
            scaled.pts = written
            scaled.time_base = Fraction(1, TRANSCODE_FPS)
            written += 1
            for packet in stream.encode(scaled):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)


def extract_one(
    raw: str, output: str, sample_id: str, cache: str | None = None
) -> tuple[str, str | None]:
    os.environ.setdefault("MALLOC_ARENA_MAX", "2")
    from visign_ai.landmarks.extract_manifest import write_sequence
    from visign_ai.landmarks.pipeline import PipelineError, process_video

    source = Path(raw)
    if cache is not None and source.stat().st_size > TRANSCODE_ABOVE_BYTES:
        target = Path(cache) / f"{sample_id}.webm"
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            transcode_like_browser(source, target)
        source = target
    try:
        result = process_video(source, allow_mp4=True)
    except PipelineError as error:
        return sample_id, error.code
    if result["report"].get("inputStatus") != "HAS_USABLE_FRAMES":
        return sample_id, "INSUFFICIENT_LANDMARKS"
    write_sequence(Path(output) / f"{sample_id}.npz", sample_id, result)
    return sample_id, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-per-class", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--transcode-large",
        action="store_true",
        help="Chuan hoa file > 10 MiB ve WebM 640 px 30 fps (cache trong output/transcoded)",
    )
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    rows, skipped = scan(args.raw_root)
    counts = Counter(row["classLabel"] for row in rows)
    dropped_classes = {
        label: count for label, count in counts.items() if count < args.min_per_class
    }
    rows = [row for row in rows if row["classLabel"] not in dropped_classes]
    assign_splits(rows, args.seed)

    features = args.output / "features"
    features.mkdir(parents=True, exist_ok=True)
    rejected: list[dict[str, str]] = []
    pending = {
        row["sampleId"]: row
        for row in rows
        if not (features / f"{row['sampleId']}.npz").exists()
    }
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                extract_one,
                str(args.raw_root / row["rawPath"]),
                str(features),
                sample_id,
                str(args.output / "transcoded") if args.transcode_large else None,
            )
            for sample_id, row in pending.items()
        ]
        for done, future in enumerate(as_completed(futures), 1):
            sample_id, code = future.result()
            if code is not None:
                rejected.append(
                    {
                        "sampleId": sample_id,
                        "rawPath": pending[sample_id]["rawPath"],
                        "code": code,
                    }
                )
            if done % 25 == 0 or done == len(futures):
                print(
                    f"extracted {done}/{len(futures)} (rejected {len(rejected)})",
                    flush=True,
                )
    rejected_ids = {item["sampleId"] for item in rejected}
    kept = []
    for row in rows:
        if (
            row["sampleId"] in rejected_ids
            or not (features / f"{row['sampleId']}.npz").exists()
        ):
            continue
        kept.append({**row, "landmarkPath": f"features/{row['sampleId']}.npz"})

    with (args.output / "manifest.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, FIELDS)
        writer.writeheader()
        writer.writerows(kept)
    registry = {
        row["meaningId"]: row["displayText"]
        for row in csv.DictReader(
            (
                Path(__file__).resolve().parents[4]
                / "data"
                / "manifests"
                / "p0-meanings.csv"
            ).open(encoding="utf-8-sig")
        )
    }
    class_map = {
        label: {
            "meaningId": label.rsplit("_", 2)[0],
            "displayText": registry[label.rsplit("_", 2)[0]],
        }
        for label in sorted({row["classLabel"] for row in kept})
    }
    (args.output / "class-map.json").write_text(
        json.dumps(class_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report: dict[str, Any] = {
        "rawRoot": str(args.raw_root),
        "scanned": len(rows) + sum(dropped_classes.values()) + len(skipped),
        "skippedNames": skipped,
        "droppedClasses": dropped_classes,
        "rejected": rejected,
        "kept": len(kept),
        "byClassSplit": {
            label: dict(
                Counter(row["split"] for row in kept if row["classLabel"] == label)
            )
            for label in sorted(class_map)
        },
        "splitEvidence": "video-held-out (moi file la mot video goc rieng; chua co signerId)",
        "seed": args.seed,
        "split": "70/20/10 (train/validation/test) theo lop",
        "transcodedAboveBytes": TRANSCODE_ABOVE_BYTES if args.transcode_large else None,
    }
    (args.output / "prepare-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: report[k] for k in ("scanned", "kept", "droppedClasses")},
            ensure_ascii=False,
        )
    )
    print(f"rejected by code: {dict(Counter(item['code'] for item in rejected))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
