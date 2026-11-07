"""Summarize held-out serving probes without recording clips or signer IDs."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict, cast

from visign_ai.cli import make_console_output_safe

Outcome = Literal["accepted", "rejected", "error"]
SLICE_FIELDS = ("signerGroup", "lighting", "angle")
PROBE_FIELDS = (
    "probeId",
    "modelVersion",
    "expectedMeaning",
    "predictedMeaning",
    "outcome",
    "oodKind",
    *SLICE_FIELDS,
)


@dataclass(frozen=True)
class Probe:
    probeId: str
    modelVersion: str
    expectedMeaning: str
    predictedMeaning: str
    outcome: Outcome
    signerGroup: str
    lighting: str
    angle: str
    oodKind: str = ""


class ProbeCounts(TypedDict):
    attempts: int
    errors: int
    oodAttempts: int
    oodErrors: int
    oodDecisions: int
    falseAccepts: int
    falseAcceptRate: float | None
    supportedAttempts: int
    supportedCorrect: int
    supportedCorrectRate: float | None


class RobustnessReport(TypedDict):
    modelVersion: str
    overall: ProbeCounts
    byMeaning: dict[str, ProbeCounts]
    byOodKind: dict[str, ProbeCounts]
    bySlice: dict[str, dict[str, ProbeCounts]]
    repeatedProbes: dict[str, int]


def outcome_counts(probes: Sequence[Probe]) -> ProbeCounts:
    ood = [probe for probe in probes if not probe.expectedMeaning]
    errors = sum(probe.outcome == "error" for probe in ood)
    false_accepts = sum(probe.outcome == "accepted" for probe in ood)
    decided = len(ood) - errors
    supported = [probe for probe in probes if probe.expectedMeaning]
    correct = sum(
        probe.outcome == "accepted" and probe.predictedMeaning == probe.expectedMeaning
        for probe in supported
    )
    return {
        "attempts": len(probes),
        "errors": sum(probe.outcome == "error" for probe in probes),
        "oodAttempts": len(ood),
        "oodErrors": errors,
        "oodDecisions": decided,
        "falseAccepts": false_accepts,
        "falseAcceptRate": false_accepts / decided if decided else None,
        "supportedAttempts": len(supported),
        "supportedCorrect": correct,
        "supportedCorrectRate": correct / len(supported) if supported else None,
    }


def summarize_probes(probes: Sequence[Probe]) -> RobustnessReport:
    versions = {probe.modelVersion for probe in probes}
    if len(versions) != 1 or "" in versions:
        raise ValueError("Expected probes from exactly one model version")
    repeated: dict[str, list[Probe]] = defaultdict(list)
    meanings: dict[str, list[Probe]] = defaultdict(list)
    ood_kinds: dict[str, list[Probe]] = defaultdict(list)
    slices: dict[str, dict[str, list[Probe]]] = {
        field: defaultdict(list) for field in SLICE_FIELDS
    }
    for probe in probes:
        if not probe.probeId or probe.outcome not in ("accepted", "rejected", "error"):
            raise ValueError("Missing probe ID or invalid outcome")
        if bool(probe.predictedMeaning) != (probe.outcome == "accepted"):
            raise ValueError("Only accepted outcomes must have a predicted meaning")
        repeated[probe.probeId].append(probe)
        if probe.expectedMeaning:
            if probe.oodKind:
                raise ValueError("Supported probes cannot have an OOD kind")
            meanings[probe.expectedMeaning].append(probe)
        else:
            ood_kinds[probe.oodKind or "unknown"].append(probe)
        for field in SLICE_FIELDS:
            slices[field][getattr(probe, field) or "unknown"].append(probe)

    stability: Counter[str] = Counter()
    for group in repeated.values():
        if len(group) == 1:
            continue
        attributes = ("expectedMeaning", "oodKind", *SLICE_FIELDS)
        if (
            len(
                {
                    tuple(getattr(probe, field) for field in attributes)
                    for probe in group
                }
            )
            != 1
        ):
            raise ValueError("Repeated probe has conflicting labels or slice metadata")
        if any(probe.outcome == "error" for probe in group):
            stability["incomplete"] += 1
        elif len({(probe.outcome, probe.predictedMeaning) for probe in group}) == 1:
            stability["stable"] += 1
        else:
            stability["changed"] += 1

    return {
        "modelVersion": versions.pop(),
        "overall": outcome_counts(probes),
        "byMeaning": {
            meaning: outcome_counts(rows) for meaning, rows in meanings.items()
        },
        "byOodKind": {kind: outcome_counts(rows) for kind, rows in ood_kinds.items()},
        "bySlice": {
            field: {name: outcome_counts(rows) for name, rows in groups.items()}
            for field, groups in slices.items()
        },
        "repeatedProbes": {
            status: stability[status] for status in ("stable", "changed", "incomplete")
        },
    }


def read_probes(path: Path) -> list[Probe]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if (
            not reader.fieldnames
            or set(reader.fieldnames) != set(PROBE_FIELDS)
            or len(reader.fieldnames) != len(PROBE_FIELDS)
        ):
            raise ValueError("Unexpected probe CSV header")
        probes = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Invalid probe CSV row {reader.line_num}")
            fields = {field: row[field].strip() for field in PROBE_FIELDS}
            probes.append(
                Probe(
                    probeId=fields["probeId"],
                    modelVersion=fields["modelVersion"],
                    expectedMeaning=fields["expectedMeaning"],
                    predictedMeaning=fields["predictedMeaning"],
                    outcome=cast(Outcome, fields["outcome"]),
                    signerGroup=fields["signerGroup"],
                    lighting=fields["lighting"],
                    angle=fields["angle"],
                    oodKind=fields["oodKind"],
                )
            )
        return probes


def main() -> int:
    make_console_output_safe()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probes", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = summarize_probes(read_probes(args.probes))
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"T089: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
