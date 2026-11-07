# ai/src/visign_ai/evaluation/evaluate.py
"""Evaluate a T036 GRU artifact on its held-out test split."""

import argparse
import csv
import hashlib
import json
import pickle
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any
from zipfile import BadZipFile

import torch
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from visign_ai.cli import make_console_output_safe
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training.gru_classifier import GRUClassifier
from visign_ai.training.sequence_dataset import SequenceDataset
from visign_ai.training.training_inputs import MANIFEST_FIELDS, audit_rows, read_csv

from .metrics import EvaluationMetrics, evaluate_metrics


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def audit_split(
    rows: list[dict[str, str]], meaning_map: dict[str, str]
) -> dict[str, Any]:
    report = audit_rows(rows, meaning_map)
    signers_by_split: dict[str, set[str]] = {
        split: set() for split in report["sampleCounts"]
    }
    missing: Counter[str] = Counter()
    for row in rows:
        signer = row.get("signerId", "").strip()
        if signer:
            signers_by_split[row["split"]].add(signer)
        else:
            missing[row["split"]] += 1
    memberships = Counter(
        signer for signers in signers_by_split.values() for signer in signers
    )
    overlaps = sum(count > 1 for count in memberships.values())
    if not missing and overlaps == 0:
        report["mode"] = "signer-held-out"
    return {
        **report,
        "passed": True,
        "groupedBy": "recordingSessionId",
        "testSessionCount": len(
            {r["recordingSessionId"] for r in rows if r["split"] == "test"}
        ),
        "knownSignerCounts": {
            split: len(signers) for split, signers in signers_by_split.items()
        },
        "samplesWithoutSigner": {split: missing[split] for split in signers_by_split},
        "signerOverlapCount": overlaps,
    }


@torch.inference_mode()
def score_test(
    model: GRUClassifier,
    dataset: SequenceDataset,
    rows: list[dict[str, str]],
    meaning_map: dict[str, str],
    threshold: float,
    device: str,
) -> EvaluationMetrics:
    expected, predictions, latencies = [], [], []
    for index in range(len(dataset)):
        features, target = dataset[index]
        batch = features.unsqueeze(0).to(device)
        lengths = torch.tensor([len(features)])
        if device == "cuda":
            torch.cuda.synchronize()
        started = perf_counter()
        probabilities = model(batch, lengths).softmax(dim=1)[0]
        confidence, winner = probabilities.max(dim=0)
        score, predicted = confidence.item(), int(winner.item())
        latencies.append((perf_counter() - started) * 1000)
        if not 0 <= score <= 1:
            raise ValueError("GRU produced non-finite probabilities")
        expected.append(meaning_map[dataset.class_labels[target]])
        predictions.append(
            meaning_map[dataset.class_labels[predicted]] if score >= threshold else None
        )
    return evaluate_metrics(
        expected,
        predictions,
        list(dict.fromkeys(meaning_map.values())),
        signer_ids=[row.get("signerId") for row in rows],
        latencies_ms=latencies,
    )


def write_matrix(path: Path, metrics: EvaluationMetrics) -> None:
    figure = Figure(figsize=(9, 7), layout="constrained")
    FigureCanvasAgg(figure)
    # The optional rejection column makes the matrix rectangular.
    axes = figure.subplots()
    matrix = metrics["confusionMatrix"]
    axes.imshow(matrix, cmap="Blues")
    axes.set_xticks(
        range(len(metrics["confusionMatrixColumns"])),
        metrics["confusionMatrixColumns"],
        rotation=45,
        ha="right",
    )
    axes.set_yticks(range(len(metrics["meanings"])), metrics["meanings"])
    axes.set(xlabel="Predicted meaning", ylabel="True meaning")
    midpoint = max(map(max, matrix)) / 2
    for row, counts in enumerate(matrix):
        for column, count in enumerate(counts):
            axes.text(
                column,
                row,
                str(count),
                ha="center",
                va="center",
                color="white" if count > midpoint else "black",
            )
    figure.savefig(path, dpi=140)


def evaluate(args: argparse.Namespace) -> None:
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output exists: {output}")
    artifact = args.artifact
    info = read_object(artifact / "model_info.json")
    training = read_object(artifact / "training-report.json")
    schema = load_schema(artifact / "feature_schema.json")
    if schema.get("status") != "APPROVED" or any(
        info.get(key) != schema[key]
        for key in ("featureSchemaVersion", "extractorVersion")
    ):
        raise ValueError("Approved schema must match artifact metadata")
    if info.get("artifactKind") not in ("pilot", "full"):
        raise ValueError("Evaluation requires a trained pilot or full GRU")
    checkpoint = torch.load(
        artifact / "model.pt", map_location="cpu", weights_only=True
    )
    if checkpoint["schemaSha256"] != schema_digest(schema) or checkpoint[
        "labelBinding"
    ] != {key: info[key] for key in ("classLabels", "meaningMap", "displayTextMap")}:
        raise ValueError("Checkpoint schema or class binding does not match artifact")
    labels, meaning_map = info["classLabels"], info["meaningMap"]
    if set(labels) != set(meaning_map) or set(meaning_map.values()) != set(
        info["meanings"]
    ):
        raise ValueError("Metadata meanings or labels do not match class binding")
    threshold = info["acceptanceThreshold"]
    if type(threshold) not in (int, float) or not 0 <= threshold <= 1:
        raise ValueError("Invalid artifact acceptance threshold")
    if (
        threshold != training["acceptanceThreshold"]
        or info["datasetVersion"] != training["datasetVersion"]
    ):
        raise ValueError("Threshold or dataset version differs from training report")

    raw = args.manifest.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != training["manifestSha256"]:
        raise ValueError("Manifest does not match training-report manifestSha256")
    rows = [
        row
        for row in read_csv(raw, MANIFEST_FIELDS)
        if row["classLabel"] in meaning_map
    ]
    audit = audit_split(rows, meaning_map)
    test_rows = [row for row in rows if row["split"] == "test"]
    dataset = SequenceDataset(test_rows, args.feature_root, labels, schema)

    config = checkpoint["modelConfig"]
    if (
        config["num_classes"] != len(labels)
        or config["input_size"] != dataset.expected_shape[1]
    ):
        raise ValueError("GRU dimensions do not match class binding and feature schema")
    model = GRUClassifier(**config)
    model.load_state_dict(checkpoint["stateDict"])
    if args.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA is not available")
    model.to(args.device).eval()
    metrics = score_test(model, dataset, test_rows, meaning_map, threshold, args.device)
    report = {
        **metrics,
        **{
            key: info[key]
            for key in (
                "artifactKind",
                "modelVersion",
                "datasetVersion",
                "featureSchemaVersion",
                "extractorVersion",
                "acceptanceThreshold",
            )
        },
        "evaluatedAt": datetime.now(UTC).isoformat(),
        "manifestSha256": digest,
        "schemaSha256": schema_digest(schema),
        "splitAudit": audit,
        "device": args.device,
        "latencyScope": "GRU forward, softmax and top-class selection per test tensor",
        "demoReady": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".visign-eval-", dir=output.parent) as temporary:
        staging = Path(temporary) / "report"
        staging.mkdir()
        (staging / "evaluation-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        write_matrix(staging / "confusion-matrix.png", metrics)
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Output exists: {output}")
        staging.rename(output)


def main() -> int:
    make_console_output_safe()
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("artifact", "manifest", "feature-root", "output"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    try:
        evaluate(parser.parse_args())
    except (
        OSError,
        ValueError,
        RuntimeError,
        TypeError,
        KeyError,
        csv.Error,
        BadZipFile,
        EOFError,
        pickle.UnpicklingError,
    ) as error:
        print(f"T058: {error}", file=sys.stderr)
        return 2
    print("Evaluation report and confusion matrix written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
