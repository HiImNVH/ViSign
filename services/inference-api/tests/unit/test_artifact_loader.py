# services/inference-api/tests/unit/test_artifact_loader.py
# Kiem tra nap model_info.json va tu choi artifact khong the phuc vu an toan (T037).
import json
from pathlib import Path
from typing import Any

import pytest
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.artifact_loader import (
    MODEL_INFO_FILE,
    ArtifactRejectedError,
    load_artifact,
)

FIXTURE_ARTIFACTS = Path(__file__).resolve().parents[1] / "fixtures" / "model-artifacts"
DRAFT_SCHEMA_VERSION = "visign-xy-32-v0.3-draft"
P0_MEANINGS = [
    "GIAY_TO",
    "DAU_BUNG",
    "SOT",
    "NHAN",
    "BAN",
    "CAM_ON",
    "GIUP_DO",
    "XIN_LOI",
    "DAU_DAU",
    "KHONG",
]


def build_model_info(**overrides: Any) -> dict[str, Any]:
    model_info: dict[str, Any] = json.loads(
        (FIXTURE_ARTIFACTS / "fixture" / MODEL_INFO_FILE).read_text(encoding="utf-8")
    )
    model_info.update(overrides)
    return model_info


def write_artifact(artifact_directory: Path, model_info: dict[str, Any]) -> Path:
    artifact_directory.mkdir(parents=True, exist_ok=True)
    (artifact_directory / MODEL_INFO_FILE).write_text(
        json.dumps(model_info, ensure_ascii=False), encoding="utf-8"
    )
    return artifact_directory


def labels_for(meanings: list[str]) -> dict[str, Any]:
    class_labels = [f"{meaning}_HCM_1" for meaning in meanings]
    return {
        "meanings": meanings,
        "classLabels": class_labels,
        "meaningMap": dict(zip(class_labels, meanings, strict=True)),
        "displayTextMap": {meaning: meaning.title() for meaning in meanings},
    }


def test_fixture_artifact_loads_with_display_texts() -> None:
    loaded = load_artifact(FIXTURE_ARTIFACTS / "fixture", DRAFT_SCHEMA_VERSION)

    assert loaded.metadata.artifactKind is ArtifactKind.FIXTURE
    assert loaded.metadata.demoReady is False
    assert loaded.metadata.classLabels == ["CAM_ON_HN_1", "SOT_HCM_1", "GIAY_TO_HCM_1"]
    assert loaded.displayTextMap["CAM_ON"] == "Cảm ơn"
    assert loaded.fixtureResponse is None


def test_low_confidence_fixture_carries_fixture_response() -> None:
    loaded = load_artifact(FIXTURE_ARTIFACTS / "fixture-low-confidence", None)

    assert loaded.fixtureResponse is not None
    assert loaded.fixtureResponse.classLabel == "SOT_HCM_1"
    assert loaded.fixtureResponse.confidence == pytest.approx(0.42)


def test_reordered_class_labels_are_kept_in_declared_order(tmp_path: Path) -> None:
    # Thu tu classLabels gan voi output cua model; khong duoc sap xep lai khi nap
    reordered = build_model_info(
        classLabels=["SOT_HCM_1", "GIAY_TO_HCM_1", "CAM_ON_HN_1"]
    )

    loaded = load_artifact(write_artifact(tmp_path / "reordered", reordered), None)

    assert loaded.metadata.classLabels == ["SOT_HCM_1", "GIAY_TO_HCM_1", "CAM_ON_HN_1"]


def test_missing_model_info_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArtifactRejectedError):
        load_artifact(tmp_path / "empty", None)


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    broken_directory = tmp_path / "broken"
    broken_directory.mkdir()
    (broken_directory / MODEL_INFO_FILE).write_text("{not json", encoding="utf-8")

    with pytest.raises(ArtifactRejectedError):
        load_artifact(broken_directory, None)


def test_schema_version_mismatch_is_rejected(tmp_path: Path) -> None:
    artifact_directory = write_artifact(tmp_path / "artifact", build_model_info())

    with pytest.raises(ArtifactRejectedError):
        load_artifact(artifact_directory, "visign-xy-32-v0.4")


@pytest.mark.parametrize(
    "invalid_overrides",
    [
        {"artifactKind": "candidate"},
        {"meanings": ["CAM_ON", "CAM_ON", "SOT"]},
        {"classLabels": []},
        {"classLabels": ["CAM_ON_HN_1", "CAM_ON_HN_1", "GIAY_TO_HCM_1"]},
        {"meaningMap": {"CAM_ON_HN_1": "CAM_ON", "SOT_HCM_1": "SOT"}},
        {
            "meaningMap": {
                "CAM_ON_HN_1": "CAM_ON",
                "SOT_HCM_1": "SOT",
                "GIAY_TO_HCM_1": "KHONG",
            }
        },
        {"displayTextMap": {"CAM_ON": "Cảm ơn", "SOT": "Sốt", "GIAY_TO": "   "}},
        {"displayTextMap": {"CAM_ON": "Cảm ơn", "SOT": "Sốt"}},
        {"fixtureResponse": {"classLabel": "KHONG_HN_1", "confidence": 0.5}},
        {"fixtureResponse": {"classLabel": "SOT_HCM_1", "confidence": 1.5}},
    ],
)
def test_unsafe_artifacts_are_rejected(
    tmp_path: Path, invalid_overrides: dict[str, Any]
) -> None:
    artifact_directory = write_artifact(
        tmp_path / "artifact", build_model_info(**invalid_overrides)
    )

    with pytest.raises(ArtifactRejectedError):
        load_artifact(artifact_directory, None)


def test_pilot_with_more_than_three_meanings_is_rejected(tmp_path: Path) -> None:
    pilot_info = build_model_info(artifactKind="pilot", **labels_for(P0_MEANINGS[:4]))

    with pytest.raises(ArtifactRejectedError):
        load_artifact(write_artifact(tmp_path / "pilot", pilot_info), None)


def test_full_artifact_needs_exactly_ten_meanings(tmp_path: Path) -> None:
    full_info = build_model_info(artifactKind="full", **labels_for(P0_MEANINGS[:9]))

    with pytest.raises(ArtifactRejectedError):
        load_artifact(write_artifact(tmp_path / "full", full_info), None)


def test_full_artifact_with_ten_meanings_loads(tmp_path: Path) -> None:
    full_info = build_model_info(artifactKind="full", **labels_for(P0_MEANINGS))

    loaded = load_artifact(write_artifact(tmp_path / "full", full_info), None)

    assert loaded.metadata.artifactKind is ArtifactKind.FULL
    assert loaded.metadata.meanings == P0_MEANINGS


def test_fixture_response_is_only_allowed_on_fixture(tmp_path: Path) -> None:
    pilot_info = build_model_info(
        artifactKind="pilot",
        fixtureResponse={"classLabel": "SOT_HCM_1", "confidence": 0.42},
    )

    with pytest.raises(ArtifactRejectedError):
        load_artifact(write_artifact(tmp_path / "pilot", pilot_info), None)
