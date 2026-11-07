# ai/src/visign_ai/evaluation/release_gate.py
"""Quality predicate for the full model on an audited FR-015 split."""

import argparse
import csv
import hashlib
import json
import sys
from collections.abc import Collection, Mapping
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from visign_ai.cli import make_console_output_safe
from visign_ai.landmarks.errors import PipelineError
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training.training_inputs import read_csv

MIN_MACRO_F1 = 0.80
MIN_MEANING_RECALL = 0.65
P0_MEANING_COUNT = 10


def _passes_threshold(value: object, minimum: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and minimum <= value <= 1
    )


def passes_release_gate(
    artifact_kind: str,
    supported_meanings: Collection[str],
    report: Mapping[str, object],
    p0_meanings: Collection[str],
) -> bool:
    """Require all P0 meanings and a passed recording-session audit from evaluation."""
    required = set(p0_meanings)
    if (
        artifact_kind != "full"
        or len(p0_meanings) != P0_MEANING_COUNT
        or len(required) != P0_MEANING_COUNT
        or len(supported_meanings) != P0_MEANING_COUNT
        or set(supported_meanings) != required
    ):
        return False
    audit = report.get("splitAudit")
    if (
        not isinstance(audit, dict)
        or audit.get("passed") is not True
        or audit.get("mode") not in ("video-held-out", "signer-held-out")
    ):
        return False
    recalls = report.get("perMeaningRecall")
    sample_counts = report.get("testSampleCounts")
    return (
        _passes_threshold(report.get("macroF1"), MIN_MACRO_F1)
        and isinstance(recalls, dict)
        and set(recalls) == required
        and isinstance(sample_counts, dict)
        and set(sample_counts) == required
        and all(
            _passes_threshold(recalls[meaning], MIN_MEANING_RECALL)
            for meaning in required
        )
        and all(type(count) is int and count > 0 for count in sample_counts.values())
    )


METRIC_FIELDS = (
    "accuracy",
    "macroF1",
    "perMeaningPrecision",
    "perMeaningRecall",
    "evaluatedAt",
)
IDENTITY_FIELDS = (
    "artifactKind",
    "modelVersion",
    "datasetVersion",
    "featureSchemaVersion",
    "extractorVersion",
    "acceptanceThreshold",
)


def build_model_metadata(
    base: Mapping[str, Any],
    report: Mapping[str, Any] | None = None,
    *,
    approve_demo: bool = False,
    p0_meanings: Collection[str] = (),
) -> dict[str, Any]:
    """Write API metadata from evaluation, with a separate explicit approval step."""
    kind = base.get("artifactKind")
    meanings = base.get("meanings")
    if kind not in ("fixture", "pilot", "full") or (
        not isinstance(meanings, list)
        or not meanings
        or any(not isinstance(meaning, str) or not meaning for meaning in meanings)
        or len(set(meanings)) != len(meanings)
    ):
        raise ValueError("Invalid artifact kind or meanings")
    if report is None:
        if approve_demo:
            raise ValueError("Release approval requires a full evaluation report")
        return {**base, **dict.fromkeys(METRIC_FIELDS), "demoReady": False}
    if kind == "fixture" or any(
        field not in base or field not in report or report[field] != base[field]
        for field in IDENTITY_FIELDS
    ):
        raise ValueError("Evaluation report does not match model metadata")
    if report.get("meanings") != meanings:
        raise ValueError("Evaluation report meanings differ from model metadata")
    for field in ("accuracy", "macroF1"):
        if not _passes_threshold(report.get(field), 0):
            raise ValueError(f"Invalid evaluation metric: {field}")
    for field in ("perMeaningPrecision", "perMeaningRecall"):
        values = report.get(field)
        if (
            not isinstance(values, dict)
            or set(values) != set(meanings)
            or not all(_passes_threshold(value, 0) for value in values.values())
        ):
            raise ValueError(f"Invalid evaluation metric: {field}")
    evaluated_at = report.get("evaluatedAt")
    if (
        not isinstance(evaluated_at, str)
        or datetime.fromisoformat(evaluated_at).tzinfo is None
    ):
        raise ValueError("Evaluation timestamp must include a time zone")
    if approve_demo and not passes_release_gate(kind, meanings, report, p0_meanings):
        raise ValueError("Artifact did not pass the full release gate")
    return {
        **base,
        **{field: report[field] for field in METRIC_FIELDS},
        "demoReady": approve_demo,
    }


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def update_model_metadata(
    artifact: Path,
    report_path: Path | None,
    *,
    approve_demo: bool = False,
    p0_path: Path | None = None,
) -> None:
    metadata_path = artifact / "model_info.json"
    base = read_object(metadata_path)
    if report_path is None and base.get("artifactKind") != "fixture":
        raise ValueError("Pilot and full artifacts require --report")
    report = read_object(report_path) if report_path is not None else None
    if report is not None:
        training = read_object(artifact / "training-report.json")
        schema = load_schema(artifact / "feature_schema.json")
        audit = report.get("splitAudit")
        training_audit = training["splitAudit"]
        with (artifact / "model.pt").open("rb") as weights:
            weights_digest = hashlib.file_digest(weights, "sha256").hexdigest()
        if (
            schema.get("status") != "APPROVED"
            or report.get("schemaSha256") != schema_digest(schema)
            or any(
                base.get(field) != schema[field]
                for field in ("featureSchemaVersion", "extractorVersion")
            )
            or report.get("weightsSha256") != weights_digest
            or report.get("manifestSha256") != training["manifestSha256"]
            or any(
                base.get(field) != training[field]
                for field in ("datasetVersion", "acceptanceThreshold")
            )
            or not isinstance(audit, dict)
            or audit.get("passed") is not True
            or audit.get("groupedBy") != "recordingSessionId"
            or any(
                audit.get(field) != training_audit[field]
                for field in ("sampleCounts", "sessionCount")
            )
        ):
            raise ValueError(
                "Evaluation provenance does not match this training artifact"
            )
    if approve_demo and p0_path is None:
        raise ValueError("Release approval requires --p0-meanings")
    catalog = (
        read_csv(p0_path.read_bytes(), {"meaningId"}) if p0_path is not None else []
    )
    metadata = build_model_metadata(
        base,
        report,
        approve_demo=approve_demo,
        p0_meanings=[row["meaningId"] for row in catalog],
    )
    payload = json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with TemporaryDirectory(prefix=".visign-metadata-", dir=artifact) as temporary:
        candidate = Path(temporary) / metadata_path.name
        candidate.write_text(payload, encoding="utf-8")
        candidate.replace(metadata_path)


def main() -> int:
    make_console_output_safe()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--p0-meanings", type=Path)
    parser.add_argument(
        "--approve-demo", action="store_true", help="Apply the lead's release approval"
    )
    args = parser.parse_args()
    try:
        update_model_metadata(
            args.artifact,
            args.report,
            approve_demo=args.approve_demo,
            p0_path=args.p0_meanings,
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        csv.Error,
        PipelineError,
    ) as error:
        print(f"T059: {error}", file=sys.stderr)
        return 2
    print("Model metadata written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
