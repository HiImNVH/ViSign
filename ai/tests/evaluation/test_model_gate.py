# ai/tests/evaluation/test_model_gate.py
"""Kiem tra metric va gate cho artifact fixture, pilot va full."""

import pytest
from visign_ai.evaluation.metrics import REJECTED, evaluate_metrics
from visign_ai.evaluation.release_gate import passes_release_gate

P0 = tuple(f"MEANING_{index}" for index in range(10))


def test_metrics_keep_abstentions_in_accuracy_recall_and_matrix() -> None:
    result = evaluate_metrics(
        ["A", "A", "B", "B"],
        ["A", None, "A", "B"],
        ["A", "B"],
        signer_ids=["S001", "S001", None, "S002"],
        latencies_ms=[10, 20, 30, 40],
    )

    assert result["accuracy"] == 0.5
    assert result["macroF1"] == pytest.approx((0.5 + 2 / 3) / 2)
    assert result["perMeaningPrecision"] == {"A": 0.5, "B": 1.0}
    assert result["perMeaningRecall"] == {"A": 0.5, "B": 0.5}
    assert result["testSampleCounts"] == {"A": 2, "B": 2}
    assert result["testSignerCount"] == 2
    assert result["testSamplesWithoutSigner"] == 1
    assert result["confusionMatrixColumns"] == ["A", "B", REJECTED]
    assert result["confusionMatrix"] == [[1, 0, 1], [1, 1, 0]]
    assert result["latencyMs"] == {"p50": 25, "p95": 38.5}


def test_metrics_keep_unobserved_meanings_in_macro_average() -> None:
    result = evaluate_metrics(["A", "A"], ["A", "A"], ["A", "B"])
    assert result["macroF1"] == 0.5
    assert result["testSampleCounts"] == {"A": 2, "B": 0}
    assert result["confusionMatrix"] == [[2, 0], [0, 0]]
    assert result["latencyMs"] is None


def test_metrics_reject_unknown_prediction() -> None:
    with pytest.raises(ValueError, match="configured meanings"):
        evaluate_metrics(["A"], ["B"], ["A"])


def test_metrics_reject_single_invalid_latency() -> None:
    with pytest.raises(ValueError, match="finite nonnegative"):
        evaluate_metrics(["A"], ["A"], ["A"], latencies_ms=[float("nan")])


def _passing_report() -> dict[str, object]:
    return {
        "splitAudit": {"passed": True, "mode": "video-held-out"},
        "macroF1": 0.80,
        "perMeaningRecall": dict.fromkeys(P0, 0.65),
        "testSampleCounts": dict.fromkeys(P0, 2),
    }


@pytest.mark.parametrize("kind", ["fixture", "pilot"])
def test_fixture_and_pilot_never_pass_even_with_perfect_full_metrics(kind: str) -> None:
    report = _passing_report()
    report.update(macroF1=1.0, perMeaningRecall=dict.fromkeys(P0, 1.0))
    assert not passes_release_gate(kind, P0, report, P0)


def test_full_passes_with_exact_p0_and_inclusive_thresholds() -> None:
    assert passes_release_gate("full", P0, _passing_report(), P0)


def test_full_requires_matching_p0_catalog() -> None:
    assert not passes_release_gate("full", (*P0[:-1], "OTHER"), _passing_report(), P0)


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("splitAudit", {"mode": "video-held-out"}),
        ("splitAudit", {"passed": True, "mode": "random"}),
        ("macroF1", 0.79),
        ("macroF1", float("nan")),
        ("macroF1", True),
        ("perMeaningRecall", dict.fromkeys(P0, 0.64)),
        ("testSampleCounts", {**dict.fromkeys(P0, 2), P0[0]: 0}),
    ],
)
def test_full_fails_closed_when_one_requirement_is_missing_or_fails(
    field: str, invalid: object
) -> None:
    report = _passing_report()
    report[field] = invalid
    assert not passes_release_gate("full", P0, report, P0)


def test_metadata_requires_explicit_approval_and_exact_p0() -> None:
    from visign_ai.evaluation.release_gate import build_model_metadata

    base = {
        "artifactKind": "full",
        "modelVersion": "synthetic",
        "datasetVersion": "p0-v1",
        "featureSchemaVersion": "schema-v1",
        "extractorVersion": "extractor-v1",
        "acceptanceThreshold": 0.7,
        "meanings": list(P0),
        "classLabels": ["EXAMPLE"],
    }
    report = {
        **base,
        **_passing_report(),
        "accuracy": 0.9,
        "perMeaningPrecision": dict.fromkeys(P0, 0.8),
        "evaluatedAt": "2026-11-07T21:00:00+07:00",
        "demoReady": True,
    }
    assert build_model_metadata(base)["accuracy"] is None
    pending = build_model_metadata(base, report)
    assert pending["demoReady"] is False
    assert pending["accuracy"] == 0.9
    assert pending["classLabels"] == ["EXAMPLE"]
    assert build_model_metadata(base, report, approve_demo=True, p0_meanings=P0)[
        "demoReady"
    ]
    with pytest.raises(ValueError, match="full release gate"):
        build_model_metadata(
            base, report, approve_demo=True, p0_meanings=(*P0[:-1], "OTHER")
        )
    with pytest.raises(ValueError, match="full release gate"):
        build_model_metadata(
            base, {**report, "macroF1": 0.79}, approve_demo=True, p0_meanings=P0
        )
    with pytest.raises(ValueError, match="does not match model metadata"):
        build_model_metadata(base, {**report, "modelVersion": "other"})
    with pytest.raises(ValueError, match="Invalid evaluation metric"):
        build_model_metadata(base, {**report, "accuracy": float("nan")})


def test_fixture_metadata_resets_metrics_and_cannot_be_approved() -> None:
    from visign_ai.evaluation.release_gate import build_model_metadata

    base = {"artifactKind": "fixture", "meanings": ["SOT"], "demoReady": True}
    metadata = build_model_metadata(base)
    assert metadata["demoReady"] is False
    assert metadata["accuracy"] is None
    assert metadata["macroF1"] is None
    with pytest.raises(ValueError, match="full evaluation report"):
        build_model_metadata(base, approve_demo=True)
