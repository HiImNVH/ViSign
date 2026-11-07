# ai/src/visign_ai/evaluation/metrics.py
"""Compute meaning-level metrics on a held-out set."""

from collections.abc import Sequence
from math import isfinite
from typing import TypedDict

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

REJECTED = "__REJECTED__"


class EvaluationMetrics(TypedDict):
    accuracy: float
    macroF1: float
    perMeaningPrecision: dict[str, float]
    perMeaningRecall: dict[str, float]
    testSampleCounts: dict[str, int]
    testSignerCount: int
    testSamplesWithoutSigner: int
    meanings: list[str]
    confusionMatrixColumns: list[str]
    confusionMatrix: list[list[int]]
    latencyMs: dict[str, float] | None


def evaluate_metrics(
    expected: Sequence[str],
    predicted: Sequence[str | None],
    meanings: Sequence[str],
    *,
    signer_ids: Sequence[str | None] | None = None,
    latencies_ms: Sequence[float] | None = None,
) -> EvaluationMetrics:
    """Score all configured meanings. A None prediction is an abstention."""
    labels = list(meanings)
    allowed = set(labels)
    if not labels or len(allowed) != len(labels) or REJECTED in allowed:
        raise ValueError("meanings must be nonempty, unique, and exclude the rejection label")
    if not expected or len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same nonzero sample count")
    observed_predictions = [label if label is not None else REJECTED for label in predicted]
    if not set(expected) <= allowed or any(
        label is not None and label not in allowed for label in predicted
    ):
        raise ValueError("expected and predicted must use configured meanings")

    signers = list(signer_ids) if signer_ids is not None else [None] * len(expected)
    if len(signers) != len(expected):
        raise ValueError("signer_ids must match the sample count")
    known_signers = {signer.strip() for signer in signers if signer and signer.strip()}
    latency = None
    if latencies_ms is not None:
        if len(latencies_ms) != len(expected) or any(
            not isfinite(value) or value < 0 for value in latencies_ms
        ):
            raise ValueError("latencies_ms must contain one finite nonnegative value per sample")
        percentiles: NDArray[np.float64] = np.percentile(latencies_ms, [50, 95])
        p50, p95 = percentiles
        latency = {"p50": float(p50), "p95": float(p95)}

    precision, recall, f1, support = precision_recall_fscore_support(
        expected, observed_predictions, labels=labels, zero_division=0
    )
    columns = [*labels, REJECTED] if REJECTED in observed_predictions else labels.copy()
    matrix = confusion_matrix(expected, observed_predictions, labels=columns)[: len(labels)]

    return {
        "accuracy": float(accuracy_score(expected, observed_predictions)),
        "macroF1": float(np.mean(f1)),
        "perMeaningPrecision": dict(zip(labels, map(float, precision), strict=True)),
        "perMeaningRecall": dict(zip(labels, map(float, recall), strict=True)),
        "testSampleCounts": dict(zip(labels, map(int, support), strict=True)),
        "testSignerCount": len(known_signers),
        "testSamplesWithoutSigner": sum(not signer or not signer.strip() for signer in signers),
        "meanings": labels,
        "confusionMatrixColumns": columns,
        "confusionMatrix": matrix.tolist(),
        "latencyMs": latency,
    }
