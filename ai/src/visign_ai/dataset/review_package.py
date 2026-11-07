"""ai/src/visign_ai/dataset/review_package.py: T076/T077 read-only intake handoff.

Collects review evidence without granting approvals or inventing a pilot/full manifest.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from .create_splits import prepare_split
from .validate_manifest import audit, read_csv


def build_package(manifest: Path, registry: Path, classes: Path, root: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("review output directory must be new")
    metadata = audit(manifest, registry, classes, dataset_root=root)
    if not metadata["valid"]:
        raise ValueError("repair metadata/raw errors before building a review package")
    full = audit(manifest, registry, classes, dataset_root=root, for_full_training=True)
    split, _ = prepare_split(manifest, registry, classes, root, mode="full")
    rows = read_csv(manifest)
    summary = {
        "inputSha256": metadata["inputSha256"],
        "registrySha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
        "classesSha256": hashlib.sha256(classes.read_bytes()).hexdigest(),
        "inputRowCount": len(rows), "metadataAndHashPassed": True,
        "labelAndLicenseApprovedCount": full["labelAndLicenseApprovedCount"],
        "fullTrainingEligible": full["trainingEligible"], "splitStatus": split["status"],
        "approvedPilotManifestCreated": False, "approvedFullManifestCreated": False,
        "modelDemoReady": False,
        "notes": ["Review worksheet decisions are pending until human signoff",
                  "No automatic label/license/signer/source approval",
                  "Class collection requests overlap meaning quota requests"],
    }
    output.mkdir(parents=True)
    for filename, report in [("summary.json", summary), ("metadata.json", metadata),
                             ("full-training.json", full), ("split-preflight.json", split)]:
        with (output / filename).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    review_rows = [{**row, "missingSigner": str(not bool(row["signerId"])).lower(),
                    "missingSource": str(not bool(row["sourceUri"])).lower(),
                    "decision": "pending", "expertLabelDecision": "", "rightsEvidenceReference": "",
                    "signerEvidenceReference": "", "reviewer": "", "reviewNotes": ""} for row in rows]
    write_csv(output / "sample-review.csv", review_rows)
    meaning_rows = [{"meaningId": m, "split": s, "current": stat["current"][s],
                     "target": stat["target"][s], "missing": stat["missing"][s]}
                    for m, stat in full["meaningSplitCoverage"].items() for s in stat["target"]]
    write_csv(output / "meaning-collection.csv", meaning_rows)
    priorities = full["collectionPlan"]["classSplitRequirements"]
    if priorities:
        write_csv(output / "priority-class-collection.csv", priorities)
    return summary


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "registry", "classes", "dataset-root", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        summary = build_package(args.manifest, args.registry, args.classes, args.dataset_root, args.output)
    except (ValueError, OSError, csv.Error):
        print("Review package failed; check metadata, files and a new output directory")
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
