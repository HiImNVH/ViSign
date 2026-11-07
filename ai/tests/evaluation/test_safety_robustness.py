from dataclasses import replace

import pytest
from visign_ai.evaluation.robustness import Probe, read_probes, summarize_probes


def test_ood_errors_are_distinct_from_rejections_and_false_accepts():
    rejected = Probe("blank", "pilot", "", "", "rejected", "", "dark", "front", "blank")
    accepted = replace(
        rejected, probeId="ood-sign", predictedMeaning="SOT", outcome="accepted"
    )
    error = replace(rejected, probeId="timeout", outcome="error")
    report = summarize_probes([rejected, accepted, error])
    assert report["overall"] == {
        "attempts": 3,
        "errors": 1,
        "oodAttempts": 3,
        "oodErrors": 1,
        "oodDecisions": 2,
        "falseAccepts": 1,
        "falseAcceptRate": 0.5,
        "supportedAttempts": 0,
        "supportedCorrect": 0,
        "supportedCorrectRate": None,
    }
    assert summarize_probes([error])["overall"]["falseAcceptRate"] is None
    assert report["byOodKind"]["blank"]["falseAccepts"] == 1


def test_meaning_and_condition_slices_expose_imbalance_and_repeat_changes():
    front = Probe("a", "full", "SOT", "SOT", "accepted", "held-out", "bright", "front")
    side = replace(front, probeId="b", expectedMeaning="CAM_ON", angle="side")
    timeout = replace(side, predictedMeaning="", outcome="error")
    changed = replace(front, predictedMeaning="", outcome="rejected")
    other = replace(front, probeId="c")
    report = summarize_probes([front, changed, side, timeout, other, other])
    assert report["byMeaning"]["SOT"]["supportedAttempts"] == 4
    assert report["byMeaning"]["CAM_ON"]["supportedCorrectRate"] == 0
    assert report["bySlice"]["angle"]["side"]["errors"] == 1
    assert report["bySlice"]["signerGroup"]["held-out"]["supportedCorrect"] == 3
    assert report["repeatedProbes"] == {"stable": 1, "changed": 1, "incomplete": 1}


def test_mixed_models_inconsistent_probes_and_invalid_outcomes_fail_closed():
    probe = Probe("a", "full", "SOT", "SOT", "accepted", "", "", "")
    with pytest.raises(ValueError, match="one model version"):
        summarize_probes([probe, replace(probe, modelVersion="pilot")])
    with pytest.raises(ValueError, match="conflicting"):
        summarize_probes([probe, replace(probe, lighting="dark")])
    with pytest.raises(ValueError, match="predicted meaning"):
        summarize_probes([replace(probe, outcome="rejected")])


def test_csv_loads_explicit_columns_and_rejects_truncated_rows(tmp_path):
    path = tmp_path / "probes.csv"
    header = "probeId,modelVersion,expectedMeaning,predictedMeaning,outcome,oodKind,signerGroup,lighting,angle\n"
    path.write_text(
        header + "1,pilot,,,rejected,blank,,dark,front\n", encoding="utf-8-sig"
    )
    assert summarize_probes(read_probes(path))["overall"]["falseAcceptRate"] == 0
    path.write_text(header + "2,pilot,,,rejected\n", encoding="utf-8")
    with pytest.raises(ValueError, match="row 2"):
        read_probes(path)
