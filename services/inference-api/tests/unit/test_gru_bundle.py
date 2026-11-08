# services/inference-api/tests/unit/test_gru_bundle.py
# Kiem goi artifact GRU T037 khong can torch: schema di kem, checkpoint va label binding phai khop model_info.
from pathlib import Path
from typing import Any

import pytest
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.inference.artifact_loader import ArtifactRejectedError, LoadedArtifact
from visign_api.inference.gru_bundle import (
    APPROVED_SCHEMA_STATUS,
    GruBundle,
    ServingSchema,
    verify_gru_bundle,
)

SCHEMA_VERSION = "visign-xy-32-v0.3-draft"
EXTRACTOR_VERSION = "tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3"
SCHEMA_DIGEST = "a" * 64
LANDMARK_COUNT = 78
INPUT_SIZE = 3 * LANDMARK_COUNT
# Thu tu lop co chu y khong theo bang chu cai de bat loi tu sap xep lai
PILOT_CLASS_LABELS = ["SOT_HCM_1", "CAM_ON_HN_1", "NHAN_HCM_1"]
PILOT_MEANING_MAP = {"SOT_HCM_1": "SOT", "CAM_ON_HN_1": "CAM_ON", "NHAN_HCM_1": "NHAN"}
PILOT_DISPLAY_TEXTS = {"SOT": "Sốt", "CAM_ON": "Cảm ơn", "NHAN": "Nhận"}


def pilot_artifact() -> LoadedArtifact:
    pilot_metadata = ModelMetadata(
        modelVersion="pilot-gru-test-v1",
        artifactKind=ArtifactKind.PILOT,
        datasetVersion="pilot-v1",
        featureSchemaVersion=SCHEMA_VERSION,
        extractorVersion=EXTRACTOR_VERSION,
        meanings=list(PILOT_DISPLAY_TEXTS),
        classLabels=list(PILOT_CLASS_LABELS),
        meaningMap=dict(PILOT_MEANING_MAP),
        acceptanceThreshold=0.7,
    )
    return LoadedArtifact(
        directory=Path("pilot-artifact"),
        metadata=pilot_metadata,
        displayTextMap=dict(PILOT_DISPLAY_TEXTS),
        fixtureResponse=None,
    )


def serving_schema(**overrides: Any) -> ServingSchema:
    schema_content: dict[str, Any] = {
        "featureSchemaVersion": SCHEMA_VERSION,
        "extractorVersion": EXTRACTOR_VERSION,
        "status": APPROVED_SCHEMA_STATUS,
        "landmarkOrder": [f"POINT_{index}" for index in range(LANDMARK_COUNT)],
    }
    schema_content.update(overrides)
    return ServingSchema(content=schema_content, digest=SCHEMA_DIGEST)


def checkpoint(**overrides: Any) -> dict[str, Any]:
    trained_checkpoint: dict[str, Any] = {
        "modelConfig": {
            "input_size": INPUT_SIZE,
            "hidden_size": 8,
            "num_classes": len(PILOT_CLASS_LABELS),
            "num_layers": 1,
        },
        "stateDict": {},
        "schemaSha256": SCHEMA_DIGEST,
        "labelBinding": {
            "classLabels": list(PILOT_CLASS_LABELS),
            "meaningMap": dict(PILOT_MEANING_MAP),
            "displayTextMap": dict(PILOT_DISPLAY_TEXTS),
        },
    }
    trained_checkpoint.update(overrides)
    return trained_checkpoint


def with_model_config(**config_overrides: Any) -> dict[str, Any]:
    model_config = {**checkpoint()["modelConfig"], **config_overrides}
    return checkpoint(modelConfig=model_config)


def with_label_binding(**binding_overrides: Any) -> dict[str, Any]:
    label_binding = {**checkpoint()["labelBinding"], **binding_overrides}
    return checkpoint(labelBinding=label_binding)


def test_consistent_bundle_is_accepted() -> None:
    verify_gru_bundle(pilot_artifact(), GruBundle(serving_schema(), checkpoint()))


@pytest.mark.parametrize(
    "schema_overrides",
    [
        {"status": "DRAFT_PENDING_LEAD_REVIEW"},
        {"status": None},
        {"featureSchemaVersion": "visign-xy-32-v0.4"},
        {"extractorVersion": "tasks-hand-pose-face-1.1.2-0000000000000000"},
    ],
)
def test_bundled_schema_must_be_approved_and_match_metadata(
    schema_overrides: dict[str, Any],
) -> None:
    mismatched_bundle = GruBundle(serving_schema(**schema_overrides), checkpoint())

    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(pilot_artifact(), mismatched_bundle)


@pytest.mark.parametrize(
    "missing_key", ["modelConfig", "stateDict", "schemaSha256", "labelBinding"]
)
def test_checkpoint_missing_required_part_is_rejected(missing_key: str) -> None:
    # Checkpoint cu khong co labelBinding cung bi tu choi: khong tu gan binding cho trong so cu
    incomplete_checkpoint = checkpoint()
    del incomplete_checkpoint[missing_key]

    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(), GruBundle(serving_schema(), incomplete_checkpoint)
        )


def test_checkpoint_that_is_not_a_mapping_is_rejected() -> None:
    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(pilot_artifact(), GruBundle(serving_schema(), [1, 2, 3]))  # type: ignore[arg-type]


def test_weights_trained_on_another_schema_are_rejected() -> None:
    foreign_checkpoint = checkpoint(schemaSha256="b" * 64)

    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(), GruBundle(serving_schema(), foreign_checkpoint)
        )


@pytest.mark.parametrize(
    "binding_overrides",
    [
        # Cung tap lop nhung dao thu tu: logit i se gan nham nghia
        {"classLabels": list(reversed(PILOT_CLASS_LABELS))},
        {"classLabels": PILOT_CLASS_LABELS[:2]},
        {"meaningMap": {**PILOT_MEANING_MAP, "SOT_HCM_1": "NHAN", "NHAN_HCM_1": "SOT"}},
        {"displayTextMap": {**PILOT_DISPLAY_TEXTS, "SOT": "Sốt cao"}},
        {"classLabels": None},
    ],
)
def test_label_binding_must_match_model_info_exactly(
    binding_overrides: dict[str, Any],
) -> None:
    rebound_checkpoint = with_label_binding(**binding_overrides)

    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(), GruBundle(serving_schema(), rebound_checkpoint)
        )


def test_label_binding_that_is_not_a_mapping_is_rejected() -> None:
    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(),
            GruBundle(serving_schema(), checkpoint(labelBinding=PILOT_CLASS_LABELS)),
        )


@pytest.mark.parametrize(
    "config_overrides",
    [
        {"num_classes": len(PILOT_CLASS_LABELS) + 1},
        {"input_size": INPUT_SIZE - 1},
        {"hidden_size": 0},
        {"num_layers": True},
        {"hidden_size": 8.0},
        {"dropout": 0.1},
    ],
)
def test_model_config_must_fit_schema_and_class_count(
    config_overrides: dict[str, Any],
) -> None:
    misconfigured_checkpoint = with_model_config(**config_overrides)

    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(), GruBundle(serving_schema(), misconfigured_checkpoint)
        )


def test_model_config_missing_a_dimension_is_rejected() -> None:
    model_config = dict(checkpoint()["modelConfig"])
    del model_config["num_layers"]

    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(),
            GruBundle(serving_schema(), checkpoint(modelConfig=model_config)),
        )


def test_group_weighted_feature_scale_is_accepted() -> None:
    # Trong so nhom diem tay/mat/vai (2026-11-08): he so theo tung dac trung di cung modelConfig
    scale = [1.3] * 84 + [1.3] * 12 + [0.52] * 60 + [1.3] * 48 + [0.52] * 30
    verify_gru_bundle(
        pilot_artifact(),
        GruBundle(serving_schema(), with_model_config(feature_scale=scale)),
    )


@pytest.mark.parametrize(
    "bad_scale",
    [
        [1.0] * (INPUT_SIZE - 1),
        [1.0] * (INPUT_SIZE - 1) + [0.0],
        [1.0] * (INPUT_SIZE - 1) + [float("nan")],
        [1.0] * (INPUT_SIZE - 1) + [True],
        "1.0",
    ],
)
def test_invalid_feature_scale_is_rejected(bad_scale: Any) -> None:
    with pytest.raises(ArtifactRejectedError, match="feature_scale"):
        verify_gru_bundle(
            pilot_artifact(),
            GruBundle(serving_schema(), with_model_config(feature_scale=bad_scale)),
        )


def test_unknown_model_config_key_is_still_rejected() -> None:
    with pytest.raises(ArtifactRejectedError):
        verify_gru_bundle(
            pilot_artifact(),
            GruBundle(serving_schema(), with_model_config(dropout=1)),
        )
