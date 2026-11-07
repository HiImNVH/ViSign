# services/inference-api/tests/unit/test_model_version.py
# Kiem tra metadata artifact va cong demoReady cho fixture/pilot/full (T019).
from typing import Any

import pytest
from pydantic import ValidationError
from visign_api.domain.model_version import (
    ArtifactKind,
    ModelInfoResponse,
    ModelMetadata,
)

P0_MEANINGS = [f"MEANING_{index}" for index in range(10)]


def build_metadata(**overrides: Any) -> ModelMetadata:
    passing_full_fields: dict[str, Any] = {
        "modelVersion": "vsl-full-v1",
        "artifactKind": "full",
        "datasetVersion": "p0-2026-11-07",
        "featureSchemaVersion": "visign-xy-32-v0.3-draft",
        "extractorVersion": "tasks-hand-pose-face-1.1.1",
        "meanings": P0_MEANINGS,
        "macroF1": 0.85,
        "perMeaningRecall": dict.fromkeys(P0_MEANINGS, 0.7),
        "demoReady": True,
    }
    passing_full_fields.update(overrides)
    return ModelMetadata(**passing_full_fields)


def test_full_model_passing_every_gate_is_demo_ready() -> None:
    # Given full 10 nghia, macroF1 >= 0.80, moi recall >= 0.65; Then demoReady giu True
    assert build_metadata().demoReady is True


@pytest.mark.parametrize("artifact_kind", ["fixture", "pilot"])
def test_fixture_and_pilot_are_never_demo_ready(artifact_kind: str) -> None:
    # Given metadata tu khai demoReady=True; When kind la fixture/pilot; Then bi ep ve False
    metadata = build_metadata(artifactKind=artifact_kind)

    assert metadata.artifactKind == ArtifactKind(artifact_kind)
    assert metadata.demoReady is False


@pytest.mark.parametrize(
    "failing_overrides",
    [
        {
            "meanings": P0_MEANINGS[:9],
            "perMeaningRecall": dict.fromkeys(P0_MEANINGS[:9], 0.9),
        },
        {"macroF1": 0.7999},
        {"macroF1": None},
        {"perMeaningRecall": None},
        {"perMeaningRecall": {**dict.fromkeys(P0_MEANINGS, 0.9), "MEANING_3": 0.6499}},
        {"perMeaningRecall": dict.fromkeys(P0_MEANINGS[:9], 0.9)},
    ],
)
def test_full_model_failing_any_gate_is_not_demo_ready(
    failing_overrides: dict[str, Any],
) -> None:
    # Given full model truot mot dieu kien gate; Then demoReady fail closed ve False
    assert build_metadata(**failing_overrides).demoReady is False


def test_full_model_not_declared_demo_ready_stays_false() -> None:
    # Given full model dat chi so nhung artifact chua duoc duyet demo; Then khong tu nang len True
    assert build_metadata(demoReady=False).demoReady is False


def test_gate_boundaries_are_inclusive() -> None:
    # Given dung bang nguong 0.80 va 0.65; Then van dat gate
    metadata = build_metadata(
        macroF1=0.80, perMeaningRecall=dict.fromkeys(P0_MEANINGS, 0.65)
    )

    assert metadata.demoReady is True


def test_fixture_metrics_are_nullable() -> None:
    # Given fixture khong co danh gia; Then cac metric deu null
    metadata = build_metadata(
        artifactKind="fixture", macroF1=None, perMeaningRecall=None
    )

    assert metadata.accuracy is None
    assert metadata.macroF1 is None
    assert metadata.perMeaningPrecision is None
    assert metadata.evaluatedAt is None


@pytest.mark.parametrize(
    "invalid_overrides",
    [
        {"artifactKind": "candidate"},
        {"meanings": []},
        {"meanings": [f"MEANING_{index}" for index in range(11)]},
        {"macroF1": 1.2},
        {"acceptanceThreshold": -0.1},
    ],
)
def test_invalid_metadata_is_rejected(invalid_overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        build_metadata(**invalid_overrides)


def test_model_info_response_keeps_required_nullable_fields() -> None:
    # Given fixture khong co metric; When serialize model-info; Then key nullable van co mat
    fixture_metadata = build_metadata(
        artifactKind="fixture", macroF1=None, perMeaningRecall=None
    )

    model_info = ModelInfoResponse.from_metadata(fixture_metadata).model_dump(
        mode="json"
    )

    assert model_info["artifactKind"] == "fixture"
    assert model_info["demoReady"] is False
    for nullable_key in ("macroF1", "perMeaningRecall", "evaluatedAt"):
        assert nullable_key in model_info
        assert model_info[nullable_key] is None
