# ai/src/visign_ai/evaluation/release_gate.py
"""Quality predicate for the full model on an audited FR-015 split."""

from collections.abc import Collection, Mapping

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
        and all(_passes_threshold(recalls[meaning], MIN_MEANING_RECALL) for meaning in required)
        and all(type(count) is int and count > 0 for count in sample_counts.values())
    )
