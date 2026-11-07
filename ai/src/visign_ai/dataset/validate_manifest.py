"""T012: read-only manifest audit with separate pilot and 200-video full-training gates."""

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from .entities import (
    Category,
    DataSplit,
    EntityValidationError,
    LicenseStatus,
    Meaning,
    Priority,
    Region,
    SignClass,
    VerificationStatus,
    validate_catalog,
)
from .manifest_schema import (
    _SESSION_ID,
    MANIFEST_COLUMNS,
    ManifestRow,
    _positive_integer,
    _relative_path,
    validate_rows,
)
from .meaning_registry import read_p0_meanings

CLASS_COLUMNS = ("classLabel", "meaningId", "region", "variantName", "verified", "active")
FULL_TRAINING_SPLITS = {"train": 12, "validation": 5, "test": 3}


def read_csv(path: Path, columns: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise ValueError("CSV requires UTF-8/no BOM/LF/final newline")
    text = raw.decode("utf-8")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError("CSV requires NFC")
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    header = reader.fieldnames
    if not header or len(header) != len(set(header)):
        raise ValueError("CSV header missing or duplicated")
    if columns is not None and header != list(columns):
        raise ValueError("CSV header does not match contract")
    result = list(reader)
    for row in result:
        if set(row) != set(header) or any(
            not isinstance(v, str) or v != v.strip()
            or any(ord(c) < 32 or ord(c) == 127 for c in v) for v in row.values()
        ):
            raise ValueError("invalid CSV field count, whitespace or control character")
    return result


def load_catalog(meanings_path: Path, classes_path: Path):
    meanings = [Meaning(row["meaningId"], row["displayText"], Category(row["category"]),
                        Priority(row["priority"]), True)
                for row in read_p0_meanings(meanings_path).values()]
    classes = []
    for row in read_csv(classes_path, CLASS_COLUMNS):
        if row["verified"] not in {"true", "false"} or row["active"] not in {"true", "false"}:
            raise EntityValidationError("class booleans must be true/false")
        classes.append(SignClass(row["classLabel"], row["meaningId"], Region(row["region"]),
                                 row["variantName"], row["verified"] == "true",
                                 row["active"] == "true"))
    return validate_catalog(meanings, classes)


def coverage(rows: list[dict[str, str]], meanings, classes) -> dict:
    def summarize(items):
        return {
            "sampleCount": len(items),
            "sourceVideoCount": len({r["recordingSessionId"] for r in items}),
            "knownSignerCount": len({r["signerId"] for r in items if r["signerId"]}),
            "missingSignerCount": sum(not r["signerId"] for r in items),
            "splitCounts": dict(sorted(Counter(r["split"] or "unassigned" for r in items).items())),
        }
    return {
        "total": summarize(rows),
        "byMeaning": {key: summarize([r for r in rows if r["meaningId"] == key])
                      for key in meanings},
        "byClass": {key: summarize([r for r in rows if r["classLabel"] == key])
                    for key in classes},
        "licenseCounts": dict(Counter(r["licenseStatus"] for r in rows)),
        "verificationCounts": dict(Counter(r["verificationStatus"] for r in rows)),
        "releaseExcludedCount": sum(r["licenseStatus"] != "approved"
                                    or r["verificationStatus"] == "rejected" for r in rows),
    }


def full_training_coverage(rows: list[dict[str, str]], meanings) -> dict:
    """Counts are per *meaning*, not per candidate variant class (T061)."""
    result = {}
    for meaning_id in meanings:
        samples = [row for row in rows if row["meaningId"] == meaning_id]
        counts = Counter(row["split"] for row in samples)
        current = {split: counts[split] for split in FULL_TRAINING_SPLITS}
        result[meaning_id] = {
            "total": len(samples),
            "current": current,
            "target": dict(FULL_TRAINING_SPLITS),
            "missing": {split: max(0, required - current[split])
                        for split, required in FULL_TRAINING_SPLITS.items()},
            "excess": {split: max(0, current[split] - required)
                       for split, required in FULL_TRAINING_SPLITS.items()},
            "unassigned": counts[""],
        }
    return result


def independent_group_ids(rows: list[dict[str, str]]) -> dict[str, str]:
    """Group by original source video; signer identity is optional metadata."""
    return {row["sampleId"]: row["recordingSessionId"] for row in rows}


def raw_hash_audit(rows: list[tuple[int, dict[str, str]]], root: Path) -> tuple[dict, list[dict]]:
    """Audit every structurally usable file so one bad file cannot hide the rest."""
    errors = []
    digests: set[str] = set()
    passed = 0
    root = root.resolve()
    for number, row in rows:
        try:
            raw = (root / row["rawPath"]).resolve()
            if not raw.is_relative_to(root) or not raw.is_file():
                errors.append({"line": number, "code": "RAW_FILE_MISSING_OR_UNSAFE",
                               "reason": "raw file is missing or outside dataset root"})
                continue
            with raw.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if row["sampleId"].rsplit("_", 1)[1] != digest[:12]:
                errors.append({"line": number, "code": "RAW_HASH_MISMATCH",
                               "reason": "raw SHA-256 prefix does not match sampleId"})
            elif digest in digests:
                errors.append({"line": number, "code": "DUPLICATE_RAW_CONTENT",
                               "reason": "raw bytes already occur in another row"})
            else:
                passed += 1
            digests.add(digest)
        except OSError:
            errors.append({"line": number, "code": "RAW_FILE_UNREADABLE",
                           "reason": "cannot read raw file"})
    return {"checked": len(rows), "passed": passed, "failed": len(errors),
            "method": "SHA-256 prefix in sampleId; full digest duplicate detection"}, errors


def audit(
    path: Path, meanings_path: Path, classes_path: Path, *, inventory: bool = False,
    dataset_root: Path | None = None, for_release: bool = False, for_training: bool = False,
    for_full_training: bool = False, selected_classes: set[str] | None = None,
) -> dict:
    if sum((for_release, for_training, for_full_training)) > 1:
        raise ValueError("choose exactly one gate")
    meanings, classes = load_catalog(meanings_path, classes_path)
    rows = read_csv(path, None if inventory else MANIFEST_COLUMNS)
    errors, parsed, usable = [], [], []
    usable_lines = []
    pending_metadata: Counter[str] = Counter()
    seen_ids: set[str] = set()
    known_hashes: set[str] = set()
    sessions: dict[str, set[str]] = {}
    for number, row in enumerate(rows, start=2):
        try:
            if inventory:
                required = {"sampleId", "meaningId", "classLabel", "recordingSessionId", "signerId",
                            "licenseStatus", "verificationStatus", "split", "sha256", "rawPath",
                            "durationMs", "frameCount"}
                if not required <= row.keys():
                    raise ValueError("inventory missing required columns")
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*_[0-9a-f]{12}", row["sampleId"]):
                    raise ValueError("invalid sampleId")
                if not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
                    raise ValueError("invalid inventory sha256")
                if row["sampleId"].rsplit("_", 1)[1] != row["sha256"][:12]:
                    raise ValueError("sampleId/hash mismatch")
                if row["sha256"] in known_hashes:
                    raise ValueError("duplicate inventory raw content")
                known_hashes.add(row["sha256"])
                if not _SESSION_ID.fullmatch(row["recordingSessionId"]):
                    raise ValueError("invalid recordingSessionId")
                if row["signerId"] and not re.fullmatch(r"S[0-9]{3}", row["signerId"]):
                    raise ValueError("invalid signerId")
                if (row["recordingSessionId"].startswith("S") and row["signerId"]
                        and not row["recordingSessionId"].startswith(row["signerId"] + "-R")):
                    raise ValueError("signer session mismatch")
                try:
                    LicenseStatus(row["licenseStatus"])
                    VerificationStatus(row["verificationStatus"])
                    if row["split"]:
                        DataSplit(row["split"])
                except ValueError as exc:
                    raise ValueError("invalid inventory status") from exc
                if row["rawPath"]:
                    _relative_path("rawPath", row["rawPath"])
                for field in ("durationMs", "frameCount"):
                    if row[field]:
                        _positive_integer(field, row[field])
                if row["durationMs"] and not 300 <= int(row["durationMs"]) <= 6000:
                    raise ValueError("duration outside pipeline limits")
                if row["verificationStatus"] == "rejected" and not row.get("rejectionReason"):
                    raise ValueError("rejected sample requires rejectionReason")
                for field in ("rawPath", "durationMs", "frameCount"):
                    if not row[field]:
                        pending_metadata[field] += 1
            else:
                parsed.append(ManifestRow.from_mapping(row))
            if row["sampleId"] in seen_ids:
                raise ValueError("duplicate sampleId")
            seen_ids.add(row["sampleId"])
            if row["meaningId"] not in meanings:
                raise ValueError("unknown meaningId")
            cls = classes.get(row["classLabel"])
            if cls is None or cls.meaning_id != row["meaningId"]:
                raise ValueError("unknown/mismatched classLabel")
            sessions.setdefault(row["recordingSessionId"], set()).add(row["split"])
            if (for_release or for_training or for_full_training) and not cls.active:
                errors.append({"line": number, "code": "CLASS_INACTIVE", "reason": "class is inactive"})
            usable.append(row)
            usable_lines.append((number, row))
        except (ValueError, TypeError) as exc:
            # Avoid emitting any input row, URI, raw path or credential in reports.
            errors.append({"line": number, "code": "INVALID_ROW", "reason": str(exc)})
    for splits in sessions.values():
        if len(splits) > 1:
            errors.append({"code": "SPLIT_LEAKAGE", "reason": "recordingSessionId spans multiple splits"})
    if not inventory:
        try:
            validate_rows(parsed, known_meanings=set(meanings),
                          known_classes={key: cls.meaning_id for key, cls in classes.items()},
                          for_release=for_release or for_training or for_full_training)
        except (ValueError, OSError):
            errors.append({"code": "BATCH_VALIDATION_FAILED",
                           "reason": "ID/reference/hash/file/release validation failed"})
    hash_details = None
    if not inventory and dataset_root is not None:
        hash_details, hash_errors = raw_hash_audit(usable_lines, dataset_root)
        errors.extend(hash_errors)
    if not rows:
        errors.append({"code": "EMPTY_INPUT", "reason": "no samples"})
    if (for_release or for_training or for_full_training) and (inventory or dataset_root is None):
        errors.append({"code": "RELEASE_INPUT_REQUIRED",
                       "reason": "training/release requires a manifest and dataset root for hash audit"})
    if (for_release or for_full_training) and {r["meaningId"] for r in usable} != set(meanings):
        errors.append({"code": "MISSING_P0_COVERAGE", "reason": "all 10 meanings required"})
    observed = {r["classLabel"] for r in rows if "classLabel" in r}
    selected = selected_classes if selected_classes is not None else observed
    if for_release or for_full_training:
        selected = selected | {key for key, cls in classes.items() if cls.active}
    unknown_selected = selected - classes.keys()
    if unknown_selected:
        errors.append({"code": "UNKNOWN_SELECTED_CLASS", "reason": "selected class absent from registry"})
    if (for_training or for_full_training or for_release) and observed - selected:
        errors.append({"code": "UNSELECTED_INPUT_CLASS", "reason": "manifest contains unselected classes"})
    if for_training or for_full_training:
        rejected = sum(row["verificationStatus"] == "rejected" for row in usable)
        not_licensed = sum(row["licenseStatus"] != "approved" for row in usable)
        if rejected:
            errors.append({"code": "SAMPLES_REJECTED", "count": rejected,
                           "reason": "rejected samples cannot enter training"})
        if not_licensed:
            errors.append({"code": "SAMPLES_LICENSE_NOT_APPROVED", "count": not_licensed,
                           "reason": "training requires approved usage rights"})
        if for_training and len({row["meaningId"] for row in usable}) > 3:
            errors.append({"code": "PILOT_MEANING_LIMIT",
                           "reason": "pilot supports at most 3 meanings; use full-training gate for 10 P0"})
        for key in sorted(selected & classes.keys()):
            if not classes[key].verified:
                errors.append({"code": "CLASS_NOT_VERIFIED", "classLabel": key,
                               "reason": "candidate class requires expert verification"})
    meaning_coverage = full_training_coverage(usable, meanings)
    if for_full_training:
        for meaning_id, stats in meaning_coverage.items():
            if (stats["unassigned"] or any(stats["current"][split] != expected
                                           for split, expected in FULL_TRAINING_SPLITS.items())):
                errors.append({"code": "MEANING_SPLIT_QUOTA", "meaningId": meaning_id,
                               "current": stats["current"], "missing": stats["missing"],
                               "excess": stats["excess"],
                               "reason": "each meaning requires exactly 12 train, 5 validation, 3 test"})
    split_coverage: dict[str, dict] = {}
    independent_by_sample = independent_group_ids(usable)
    for key in sorted(selected & classes.keys()):
        samples = [r for r in usable if r["classLabel"] == key]
        counts = Counter(r["split"] for r in samples if r["split"])
        missing = sorted({"train", "validation", "test"} - counts.keys())
        group_count = len({independent_by_sample[r["sampleId"]] for r in samples})
        split_coverage[key] = {
            "splitCounts": dict(counts), "missingSplits": missing, "sampleCount": len(samples),
            "potentialIndependentGroupCount": group_count,
            "minimumAdditionalIndependentGroups": max(0, 3 - group_count),
            "knownSignerCount": len({r["signerId"] for r in samples if r["signerId"]}),
            "missingSignerCount": sum(not r["signerId"] for r in samples),
            "reassignmentAloneRuledOut": group_count < 3,
            "reason": ("fewer than 3 independent groups; collect additional videos"
                       if group_count < 3 else "check signer/session grouping and quotas before assigning splits"),
        }
        if (for_training or for_full_training or for_release) and missing:
            errors.append({"code": "MISSING_CLASS_SPLITS", "classLabel": key, "missingSplits": missing,
                           "reason": "each selected class needs train, validation and test samples"})
    approved_rows = [r for r in usable if not inventory and r["verificationStatus"] != "rejected"
                     and r["licenseStatus"] == "approved" and classes[r["classLabel"]].active
                     and classes[r["classLabel"]].verified]
    error_counts = dict(sorted(Counter(e["code"] for e in errors).items()))
    return {
        "valid": not errors, "inputSha256": hashlib.sha256(path.read_bytes()).hexdigest(), "inputKind": "review-inventory" if inventory else "manifest",
        "inputRowCount": len(rows), "acceptedForCoverageCount": len(usable), "errors": errors,
        "coverage": coverage(usable, meanings, classes), "pendingMetadataCounts": dict(pending_metadata),
        "hashAudit": ("NOT_RUN" if hash_details is None else
                      "PASSED" if hash_details["checked"] == len(rows) and not hash_details["failed"] else "FAILED"),
        "hashAuditDetails": hash_details, "errorCounts": error_counts,
        "labelAndLicenseApprovedCount": len(approved_rows),
        "labelAndLicenseApprovedMeaningCoverage": full_training_coverage(approved_rows, meanings),
        "releaseEligible": for_release and not errors, "modelDemoReady": False,
        "trainingEligible": (for_training or for_full_training) and not errors,
        "trainingMode": "full" if for_full_training else "pilot" if for_training else "not-evaluated",
        "fullTrainingTarget": {"meanings": len(meanings), "total": 20 * len(meanings),
                               "perMeaningSplit": dict(FULL_TRAINING_SPLITS)},
        "meaningSplitCoverage": meaning_coverage,
        "collectionPlan": {
            "currentBySplit": {split: sum(s["current"][split] for s in meaning_coverage.values())
                               for split in FULL_TRAINING_SPLITS},
            "missingBySplit": {split: sum(s["missing"][split] for s in meaning_coverage.values())
                               for split in FULL_TRAINING_SPLITS},
            "excessBySplit": {split: sum(s["excess"][split] for s in meaning_coverage.values())
                              for split in FULL_TRAINING_SPLITS},
            "classSplitRequirements": [
                {"meaningId": classes[key].meaning_id, "classLabel": key, "split": split,
                 "minimumSamples": 1,
                 "remainingMeaningQuota": meaning_coverage[classes[key].meaning_id]["missing"][split],
                 "action": ("collect-and-verify-independent-source-video"
                            if stats["reassignmentAloneRuledOut"] else "review-grouping-and-reassign-or-collect")}
                for key, stats in split_coverage.items() for split in stats["missingSplits"]
            ],
            "notes": ["Class requirements overlap meaning deficits; never add both totals",
                      "Current counts include unverified rows; they are not approved sample counts",
                      "Independent groups count original recording sessions, not signers",
                      "New samples must preserve recording-session isolation and meaning quotas"],
        },
        "releaseCheckScope": "manifest-metadata-and-per-class-splits", "fullQualityGateEvaluated": False,
        "schemaApprovalChecked": False, "classSplitCoverage": split_coverage,
        "splitEvidence": ("unassigned-or-leakage" if not usable
                          or any(e["code"] == "SPLIT_LEAKAGE" for e in errors)
                          or any(not r["split"] for r in usable)
                          else "video-held-out"),
        "notes": ["Coverage counts are metadata, not specialist verification or training sufficiency",
                  "No unseen-signer claim; split evidence reflects source-video isolation only",
                  "Approved public educational sources may omit sourceUri; see dataset card"],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--manifest", type=Path)
    inputs.add_argument("--inventory-review", type=Path)
    parser.add_argument("--registry", type=Path, default=Path("data/manifests/p0-meanings.csv"))
    parser.add_argument("--classes", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path)
    gates = parser.add_mutually_exclusive_group()
    gates.add_argument("--for-release", action="store_true")
    gates.add_argument("--for-training", action="store_true", help="pilot, at most 3 meanings, selected classes")
    gates.add_argument("--for-full-training", action="store_true", help="200 videos, 12/5/3 per meaning")
    parser.add_argument("--selected-class", action="append", default=None)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit(args.manifest or args.inventory_review, args.registry, args.classes,
                       inventory=args.inventory_review is not None, dataset_root=args.dataset_root,
                       for_release=args.for_release, for_training=args.for_training,
                       for_full_training=args.for_full_training,
                       selected_classes=set(args.selected_class) if args.selected_class else None)
    except (ValueError, OSError, csv.Error, UnicodeError):
        report = {"valid": False, "releaseEligible": False, "trainingEligible": False, "modelDemoReady": False,
                  "errors": [{"code": "INVALID_INPUT", "reason": "cannot read valid input/catalog"}]}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        # An explicit report must never overwrite input files or existing outputs.
        try:
            with args.report.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
        except OSError:
            print("Cannot create report; existing files are not overwritten", file=sys.stderr)
            return 1
    else:
        print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
