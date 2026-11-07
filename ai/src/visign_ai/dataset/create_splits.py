"""ai/src/visign_ai/dataset/create_splits.py: T018 grouped, exact-quota split.

Creates a new manifest only after a feasible assignment passes T012. Never
invents samples, approvals, signer IDs or labels. Search is bounded explicitly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

from .manifest_schema import (
    MANIFEST_COLUMNS,
    read_manifest_csv,
    validate_dataset_version,
    validate_rows,
)
from .validate_manifest import (
    FULL_TRAINING_SPLITS,
    audit,
    independent_group_ids,
    load_catalog,
)

SPLITS = tuple(FULL_TRAINING_SPLITS)


def assign_groups(rows: list[dict[str, str]], quotas: dict[str, dict[str, int]],
                  *, max_states: int = 100_000) -> dict:
    """Prefer known-signer isolation; original source-video isolation is mandatory."""
    parents: dict[str, str] = {}

    def find(key: str) -> str:
        parents.setdefault(key, key)
        if parents[key] != key:
            parents[key] = find(parents[key])
        return parents[key]

    for row in rows:
        session = find("session:" + row["recordingSessionId"])
        if row.get("signerId"):
            signer = find("signer:" + row["signerId"])
            parents[max(session, signer)] = min(session, signer)
    if any(row.get("signerId") for row in rows):
        preferred_rows = [{**row, "recordingSessionId": find("session:" + row["recordingSessionId"])}
                          for row in rows]
        preferred = _assign_groups(preferred_rows, quotas, max_states=max_states)
        if preferred["status"] == "FEASIBLE":
            preferred["signerPreference"] = "satisfied-for-known-signers"
            return preferred
        result = _assign_groups(rows, quotas, max_states=max_states)
        result["signerPreference"] = "fallback-to-source-video"
        result["signerPreferenceAttemptStatus"] = preferred["status"]
        return result
    result = _assign_groups(rows, quotas, max_states=max_states)
    result["signerPreference"] = "no-known-signers"
    return result


def _assign_groups(rows: list[dict[str, str]], quotas: dict[str, dict[str, int]],
                  *, max_states: int = 100_000) -> dict:
    """Pure solver; supplied rows must already have validated IDs/statuses."""
    if max_states < 1 or not rows:
        raise ValueError("nonempty samples and positive search limit required")
    if not isinstance(quotas, dict) or not all(isinstance(q, dict) for q in quotas.values()):
        raise ValueError("quotas must map meanings to split counts")
    meanings = sorted(quotas)
    if {r["meaningId"] for r in rows} != set(meanings):
        return {"status": "INFEASIBLE", "reason": "quota/sample meanings differ"}
    counts = Counter(r["meaningId"] for r in rows)
    for meaning, target in quotas.items():
        if (set(target) != set(SPLITS) or any(type(n) is not int or n < 1 for n in target.values())):
            raise ValueError("each meaning needs positive integer train/validation/test quotas")
        if sum(target.values()) != counts[meaning]:
            return {"status": "INFEASIBLE", "reason": "sample counts differ from exact quotas"}
    labels = sorted({r["classLabel"] for r in rows})
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    group_ids = independent_group_ids(rows)
    for row in rows:
        by_group[group_ids[row["sampleId"]]].append(row)
    group_frequency = Counter(label for group in by_group.values()
                              for label in {r["classLabel"] for r in group})
    if any(group_frequency[label] < 3 for label in labels):
        return {"status": "INFEASIBLE", "reason": "a class has fewer than three independent groups"}
    # Rare classes first; larger groups first; content IDs make ties reproducible.
    groups = sorted(by_group.values(), key=lambda g: (
        min(group_frequency[r["classLabel"]] for r in g), -len(g),
        min(r["sampleId"] for r in g),
    ))
    vectors = [Counter(r["meaningId"] for r in g) for g in groups]
    group_labels = [{r["classLabel"] for r in g} for g in groups]
    remaining_groups = dict(group_frequency)
    remaining = {(m, s): quotas[m][s] for m in meanings for s in SPLITS}
    masks = dict.fromkeys(labels, 0)
    choices = []
    failed = set()
    states = 0

    def search(index: int) -> bool:
        nonlocal states
        states += 1
        if states > max_states:
            raise RuntimeError("search limit")
        if index == len(groups):
            return all(n == 0 for n in remaining.values()) and all(n == 7 for n in masks.values())
        state = (index, tuple(remaining.values()), tuple(masks.values()))
        if state in failed:
            return False
        for label in group_labels[index]:
            remaining_groups[label] -= 1
        for split_index, split in enumerate(SPLITS):
            if any(remaining[(m, split)] < n for m, n in vectors[index].items()):
                continue
            previous_masks = {label: masks[label] for label in group_labels[index]}
            for label in previous_masks:
                masks[label] |= 1 << split_index
            for meaning, n in vectors[index].items():
                remaining[(meaning, split)] -= n
            choices.append(split)
            feasible = all(3 - masks[label].bit_count() <= remaining_groups[label] for label in labels)
            if feasible and search(index + 1):
                return True
            choices.pop()
            for meaning, n in vectors[index].items():
                remaining[(meaning, split)] += n
            masks.update(previous_masks)
        for label in group_labels[index]:
            remaining_groups[label] += 1
        failed.add(state)
        return False

    try:
        feasible = search(0)
    except RuntimeError:
        return {"status": "SEARCH_LIMIT", "states": states,
                "reason": "search exhausted its budget; feasibility is unknown"}
    if not feasible:
        return {"status": "INFEASIBLE", "states": states,
                "reason": "group isolation, class coverage and quotas cannot all be satisfied"}
    return {"status": "FEASIBLE", "states": states,
            "assignment": {r["sampleId"]: split for g, split in zip(groups, choices, strict=True) for r in g}}


def prepare_split(manifest: Path, registry: Path, class_catalog: Path, dataset_root: Path,
                  *, mode: str, pilot_quotas: dict | None = None, max_states: int = 100_000) -> tuple[dict, list]:
    if mode not in {"full", "pilot"}:
        raise ValueError("mode must be full or pilot")
    meanings, classes = load_catalog(registry, class_catalog)
    # This tool replaces existing assignments. Validate unsplit copies, preserving all other fields.
    samples = [replace(row, split=None) for row in read_manifest_csv(manifest)]
    validate_rows(samples, known_meanings=set(meanings),
                  known_classes={key: cls.meaning_id for key, cls in classes.items()}, dataset_root=dataset_root)
    rows = [row.to_csv_row() for row in samples]
    issues: Counter[str] = Counter()
    for row in rows:
        cls = classes[row["classLabel"]]
        if not cls.active or not cls.verified:
            issues["CLASS_NOT_APPROVED"] += 1
        if row["verificationStatus"] == "rejected" or row["licenseStatus"] != "approved":
            issues["SAMPLE_NOT_APPROVED"] += 1
    observed = {r["meaningId"] for r in rows}
    if mode == "full" and observed != set(meanings):
        issues["MISSING_P0_COVERAGE"] += 1
    if mode == "pilot" and not 1 <= len(observed) <= 3:
        issues["PILOT_MEANING_LIMIT"] += 1
    if issues:
        return {"status": "BLOCKED_INPUT", "issues": dict(issues)}, []
    if mode == "full":
        quotas = {m: dict(FULL_TRAINING_SPLITS) for m in meanings}
    elif pilot_quotas is not None:
        quotas = pilot_quotas
    else:
        raise ValueError("pilot requires explicit per-meaning quotas")
    result = assign_groups(rows, quotas, max_states=max_states)
    if result["status"] != "FEASIBLE":
        return result, []
    result["splitEvidence"] = "video-held-out"
    assigned = [replace(row, split=result["assignment"][row.sample_id]) for row in samples]
    return result, assigned


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "registry", "classes", "dataset-root", "output", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--mode", choices=["full", "pilot"], required=True)
    parser.add_argument("--pilot-quotas", type=Path)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--max-states", type=int, default=100_000)
    args = parser.parse_args(argv)
    created_output = False
    try:
        validate_dataset_version(args.dataset_version)
        if args.output.resolve() == args.report.resolve() or args.output.exists() or args.report.exists():
            raise ValueError("outputs must be distinct new files")
        if args.mode == "full" and args.pilot_quotas:
            raise ValueError("full quotas cannot be overridden")
        quotas = json.loads(args.pilot_quotas.read_text(encoding="utf-8")) if args.pilot_quotas else None
        result, samples = prepare_split(args.manifest, args.registry, args.classes, args.dataset_root,
                                        mode=args.mode, pilot_quotas=quotas, max_states=args.max_states)
        result.update(inputSha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                      datasetVersion=args.dataset_version, mode=args.mode, modelDemoReady=False)
        if result["status"] == "FEASIBLE":
            with args.output.open("x", encoding="utf-8", newline="") as stream:
                created_output = True
                writer = csv.DictWriter(stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(row.to_csv_row() for row in samples)
            check = audit(args.output, args.registry, args.classes, dataset_root=args.dataset_root,
                          for_training=args.mode == "pilot", for_full_training=args.mode == "full")
            if not check["valid"]:
                raise ValueError("T012 post-validation rejected split")
            result["outputSha256"] = check["inputSha256"]
            result["dataGatePassed"] = True
        result.pop("assignment", None)
        with args.report.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 0 if result["status"] == "FEASIBLE" else 1
    except (ValueError, OSError, KeyError, TypeError, csv.Error):
        if created_output:
            args.output.unlink(missing_ok=True)
        print("Split failed: check inputs, quotas, dataset files and new output paths")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
