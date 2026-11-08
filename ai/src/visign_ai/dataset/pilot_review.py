"""ai/src/visign_ai/dataset/pilot_review.py: T076 scoped pilot review handoff.

Select explicit meanings and preserve all input decisions. A candidate package
is not an approved pilot.csv, even when its metadata or split is valid.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from .create_splits import assign_groups
from .validate_manifest import CLASS_COLUMNS, audit, load_catalog, read_csv


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_pilot_review(
    manifest: Path,
    registry: Path,
    classes: Path,
    dataset_root: Path,
    output: Path,
    selected_meanings: set[str],
) -> dict:
    if output.exists():
        raise ValueError("output directory must be new")
    meanings, catalog = load_catalog(registry, classes)
    if not 1 <= len(selected_meanings) <= 3 or not selected_meanings <= meanings.keys():
        raise ValueError("select 1 to 3 registered P0 meanings")
    # Audit all source rows before selecting a subset; do not hide invalid raw files.
    source = audit(manifest, registry, classes, dataset_root=dataset_root)
    if not source["valid"]:
        raise ValueError("source manifest metadata/hash audit failed")
    rows = [r for r in read_csv(manifest) if r["meaningId"] in selected_meanings]
    if {r["meaningId"] for r in rows} != selected_meanings:
        raise ValueError("selected meaning has no samples")
    selected_labels = {r["classLabel"] for r in rows}
    class_rows = [
        r
        for r in read_csv(classes, CLASS_COLUMNS)
        if r["classLabel"] in selected_labels
    ]
    # Preserve existing split assignments; input audit already checked group isolation.
    quotas = {
        m: {
            s: sum(r["meaningId"] == m and r["split"] == s for r in rows)
            for s in ("train", "validation", "test")
        }
        for m in sorted(selected_meanings)
    }
    if any(
        sum(q.values()) != sum(r["meaningId"] == m for r in rows)
        or any(n == 0 for n in q.values())
        for m, q in quotas.items()
    ):
        raise ValueError(
            "pilot candidates need existing assigned coverage in all three splits"
        )
    feasibility = assign_groups(rows, quotas)
    output.mkdir(parents=True)
    candidate_path = output / "pilot.candidates.DRAFT.csv"
    class_path = output / "pilot-classes.DRAFT.csv"
    write_csv(candidate_path, rows)
    write_csv(class_path, class_rows)
    report = audit(
        candidate_path,
        registry,
        class_path,
        dataset_root=dataset_root,
        for_training=True,
        selected_classes=selected_labels,
    )
    write_csv(
        output / "sample-review.csv",
        [
            {
                "sampleId": r["sampleId"],
                "meaningId": r["meaningId"],
                "classLabel": r["classLabel"],
                "rawPath": r["rawPath"],
                "signerId": r["signerId"],
                "recordingSessionId": r["recordingSessionId"],
                "sourceUri": r["sourceUri"],
                "proposedSplit": r["split"],
                "rawSha256": hashlib.sha256(
                    (dataset_root / r["rawPath"]).read_bytes()
                ).hexdigest(),
                "decision": "pending",
                "labelDecision": "",
                "labelEvidenceReference": "",
                "rightsDecision": "",
                "rightsEvidenceReference": "",
                "groupDecision": "",
                "groupEvidenceReference": "",
                "reviewer": "",
                "reviewedAtUtc": "",
                "notes": "",
            }
            for r in rows
        ],
    )
    write_csv(
        output / "class-review.csv",
        [
            {
                "classLabel": key,
                "meaningId": catalog[key].meaning_id,
                "region": str(catalog[key].region),
                "variantName": catalog[key].variant_name,
                "classDecision": "",
                "classEvidenceReference": "",
                "reviewer": "",
                "reviewedAtUtc": "",
                "notes": "",
            }
            for key in sorted(selected_labels)
        ],
    )
    feasibility.pop("assignment", None)
    summary = {
        "task": "T076",
        "selectedMeanings": sorted(selected_meanings),
        "selectionIsProposal": True,
        "candidateCount": len(rows),
        "classCount": len(selected_labels),
        "inputSha256": source["inputSha256"],
        "candidateSha256": report["inputSha256"],
        "sourceClassSha256": hashlib.sha256(classes.read_bytes()).hexdigest(),
        "sourceRegistrySha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
        "candidateHashAudit": report["hashAuditDetails"],
        "splitCounts": report["coverage"]["total"]["splitCounts"],
        "pilotQuotas": quotas,
        "structuralSplitFeasibility": feasibility,
        "classSplitCoverage": report["classSplitCoverage"],
        "pilotDataGatePassed": report["trainingEligible"],
        "blockerCounts": report["errorCounts"],
        "unknownSignerCount": report["coverage"]["total"]["missingSignerCount"],
        "labelAndLicenseApprovedCount": report["labelAndLicenseApprovedCount"],
        "approvedPilotManifestCreated": False,
        "schemaApprovalChecked": False,
        "modelDemoReady": False,
        "notes": [
            "Existing rows, labels, IDs, rights and splits preserved; final decisions pending human review",
            "Feasible grouping is structural metadata only; source grouping needs human confirmation",
            "Pilot may use session-only evaluation; no unseen-signer or full-release claim",
            "Do not rename candidate CSV to pilot.csv to bypass review",
        ],
    }
    for filename, data in [
        ("summary.json", summary),
        ("pilot-gate.json", report),
        ("source-metadata.json", source),
        ("pilot-quotas.json", quotas),
    ]:
        with (output / filename).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "registry", "classes", "dataset-root", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--meaning", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        report = build_pilot_review(
            args.manifest,
            args.registry,
            args.classes,
            args.dataset_root,
            args.output,
            set(args.meaning),
        )
    except (ValueError, OSError, csv.Error):
        print(
            "Pilot review package failed; check inputs, selection and new output directory"
        )
        return 1
    print(
        json.dumps(
            {
                "reviewPackageCreated": True,
                "candidateCount": report["candidateCount"],
                "pilotDataGatePassed": report["pilotDataGatePassed"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
