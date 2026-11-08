"""T010 handoff: export validated paths and join artifact references by sampleId."""

import argparse
import csv
import hashlib
import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from .manifest_schema import (
    MANIFEST_COLUMNS,
    ManifestRow,
    ManifestSchemaError,
    _relative_path,
    read_manifest_csv,
    validate_unique_sample_ids,
)


def validated_input(manifest: Path, validation_report: Path) -> list[ManifestRow]:
    report = json.loads(validation_report.read_text(encoding="utf-8"))
    if (
        not isinstance(report, dict)
        or report.get("valid") is not True
        or report.get("inputKind") != "manifest"
        or report.get("inputSha256")
        != hashlib.sha256(manifest.read_bytes()).hexdigest()
    ):
        raise ManifestSchemaError(
            "validation report is invalid or stale for this manifest"
        )
    rows = read_manifest_csv(manifest)
    validate_unique_sample_ids(rows)
    if not rows:
        raise ManifestSchemaError("manifest has no samples")
    return rows


def export_paths(
    manifest: Path,
    validation_report: Path,
    dataset_root: Path,
    output: Path,
    *,
    allow_draft: bool = False,
) -> int:
    rows = validated_input(manifest, validation_report)
    root = dataset_root.resolve()
    for row in rows:
        if not allow_draft and (
            row.license_status != "approved" or row.verification_status != "verified"
        ):
            raise ManifestSchemaError(
                "export requires approved/verified samples; draft mode must be explicit"
            )
        path = (root / row.raw_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ManifestSchemaError("rawPath missing or escapes dataset root")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if row.sample_id.rsplit("_", 1)[1] != digest[:12]:
            raise ManifestSchemaError("raw hash mismatch")
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["sampleId", "rawPath"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(
            {"sampleId": row.sample_id, "rawPath": row.raw_path} for row in rows
        )
    return len(rows)


def merge_landmarks(
    manifest: Path,
    validation_report: Path,
    mapping: Mapping[str, str],
    artifact_root: Path,
    output: Path,
) -> int:
    rows = validated_input(manifest, validation_report)
    by_id = {row.sample_id: row for row in rows}
    if mapping.keys() - by_id.keys():
        raise ManifestSchemaError("landmark mapping references unknown sampleId")
    root = artifact_root.resolve()
    merged = []
    for row in rows:
        if row.sample_id in mapping:
            relative = mapping[row.sample_id]
            _relative_path("landmarkPath", relative)
            path = (root / relative).resolve()
            if (
                not path.is_relative_to(root)
                or not path.is_file()
                or path.name != row.sample_id + ".npz"
            ):
                raise ManifestSchemaError(
                    "landmark artifact missing/unsafe or sampleId filename mismatch"
                )
            row = replace(row, landmark_path=relative)
        merged.append(row)
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(row.to_csv_row() for row in merged)
    return len(mapping)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "merge"])
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--validation-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="diagnostic export only; never training approval",
    )
    parser.add_argument("--landmarks", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "export":
            if args.dataset_root is None:
                parser.error("export requires --dataset-root")
            count = export_paths(
                args.manifest,
                args.validation_report,
                args.dataset_root,
                args.output,
                allow_draft=args.allow_draft,
            )
        else:
            if args.landmarks is None or args.artifact_root is None:
                parser.error("merge requires --landmarks and --artifact-root")
            with args.landmarks.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames != ["sampleId", "landmarkPath"]:
                    raise ManifestSchemaError(
                        "landmark mapping header must be sampleId,landmarkPath"
                    )
                records = list(reader)
            mapping = {}
            for record in records:
                if (
                    set(record) != {"sampleId", "landmarkPath"}
                    or not record["sampleId"]
                    or not record["landmarkPath"]
                    or record["sampleId"] in mapping
                ):
                    raise ManifestSchemaError("invalid or duplicate landmark mapping")
                mapping[record["sampleId"]] = record["landmarkPath"]
            count = merge_landmarks(
                args.manifest,
                args.validation_report,
                mapping,
                args.artifact_root,
                args.output,
            )
    except (ValueError, OSError, csv.Error):
        parser.exit(
            1, "Handoff failed; check validated inputs, paths and existing outputs\n"
        )
    print(
        json.dumps(
            {
                "processed": count,
                "trainingApproval": False,
                "npzContentsValidated": False,
                "draftInputAllowed": args.allow_draft,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
