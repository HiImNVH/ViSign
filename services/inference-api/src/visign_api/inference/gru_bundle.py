# services/inference-api/src/visign_api/inference/gru_bundle.py
# Kiem goi artifact GRU pilot/full truoc khi phuc vu: schema di kem APPROVED, trong so train tren dung schema
# va label binding trung model_info theo dung thu tu lop. Khong can torch nen CI kiem duoc (T037).
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from visign_api.inference.artifact_loader import ArtifactRejectedError, LoadedArtifact
from visign_api.inference.feature_extraction import VALUES_PER_LANDMARK

# Ten file do CLI train T036 cong bo trong thu muc artifact bat bien
MODEL_WEIGHTS_FILE = "model.pt"
FEATURE_SCHEMA_FILE = "feature_schema.json"
APPROVED_SCHEMA_STATUS = "APPROVED"
REQUIRED_CHECKPOINT_KEYS = frozenset(
    {"modelConfig", "stateDict", "schemaSha256", "labelBinding"}
)
MODEL_CONFIG_KEYS = frozenset(
    {"input_size", "hidden_size", "num_classes", "num_layers"}
)
# He so theo dac trung cho trong so nhom diem tay/mat/vai (tuy chon, artifact cu khong co)
FEATURE_SCALE_KEY = "feature_scale"


@dataclass(frozen=True)
class ServingSchema:
    content: Mapping[str, Any]
    digest: str


@dataclass(frozen=True)
class GruBundle:
    schema: ServingSchema
    checkpoint: Mapping[str, Any]


def verify_gru_bundle(loaded_artifact: LoadedArtifact, gru_bundle: GruBundle) -> None:
    verify_serving_schema(loaded_artifact, gru_bundle.schema)
    verify_checkpoint_layout(gru_bundle)
    verify_label_binding(loaded_artifact, gru_bundle.checkpoint["labelBinding"])
    verify_model_config(loaded_artifact, gru_bundle)


def verify_serving_schema(
    loaded_artifact: LoadedArtifact, serving_schema: ServingSchema
) -> None:
    schema_content = serving_schema.content
    metadata = loaded_artifact.metadata
    if schema_content.get("status") != APPROVED_SCHEMA_STATUS:
        raise ArtifactRejectedError("Schema di kem artifact chua APPROVED")
    if schema_content.get("featureSchemaVersion") != metadata.featureSchemaVersion:
        raise ArtifactRejectedError(
            "featureSchemaVersion cua schema di kem khac model_info"
        )
    if schema_content.get("extractorVersion") != metadata.extractorVersion:
        raise ArtifactRejectedError(
            "extractorVersion cua schema di kem khac model_info"
        )


def verify_checkpoint_layout(gru_bundle: GruBundle) -> None:
    trained_checkpoint = gru_bundle.checkpoint
    if not isinstance(trained_checkpoint, Mapping):
        raise ArtifactRejectedError(
            f"{MODEL_WEIGHTS_FILE} phai chua checkpoint dang dict"
        )
    missing_keys = REQUIRED_CHECKPOINT_KEYS - set(trained_checkpoint)
    if missing_keys:
        # Checkpoint cu thieu labelBinding cung bi tu choi: phai train lai bang CLI T036
        raise ArtifactRejectedError(f"Checkpoint thieu {sorted(missing_keys)}")
    if trained_checkpoint["schemaSha256"] != gru_bundle.schema.digest:
        raise ArtifactRejectedError(
            "Trong so duoc train tren schema khac schema di kem"
        )


def verify_label_binding(loaded_artifact: LoadedArtifact, label_binding: Any) -> None:
    # Logit thu i ung voi classLabels[i] luc train: lech thu tu hay chu hien thi la gan nham nghia
    if not isinstance(label_binding, Mapping):
        raise ArtifactRejectedError("labelBinding trong checkpoint phai la dict")
    expected_binding = {
        "classLabels": loaded_artifact.metadata.classLabels,
        "meaningMap": loaded_artifact.metadata.meaningMap,
        "displayTextMap": loaded_artifact.displayTextMap,
    }
    for binding_key, expected_value in expected_binding.items():
        if label_binding.get(binding_key) != expected_value:
            raise ArtifactRejectedError(f"labelBinding.{binding_key} khac model_info")


def verify_model_config(loaded_artifact: LoadedArtifact, gru_bundle: GruBundle) -> None:
    model_config = gru_bundle.checkpoint["modelConfig"]
    if not has_positive_integer_dimensions(model_config):
        raise ArtifactRejectedError(
            "modelConfig phai co dung 4 kich thuoc nguyen duong"
        )
    landmark_count = len(gru_bundle.schema.content.get("landmarkOrder", []))
    if model_config["input_size"] != VALUES_PER_LANDMARK * landmark_count:
        raise ArtifactRejectedError("input_size cua GRU khac so dac trung cua schema")
    if model_config["num_classes"] != len(loaded_artifact.metadata.classLabels):
        raise ArtifactRejectedError("num_classes cua GRU khac so classLabels")
    if FEATURE_SCALE_KEY in model_config and not is_valid_feature_scale(
        model_config[FEATURE_SCALE_KEY], model_config["input_size"]
    ):
        raise ArtifactRejectedError("feature_scale phai co input_size so duong huu han")


def has_positive_integer_dimensions(model_config: Any) -> bool:
    if (
        not isinstance(model_config, Mapping)
        or set(model_config) - {FEATURE_SCALE_KEY} != MODEL_CONFIG_KEYS
    ):
        return False
    # bool la lop con cua int nen phai loai rieng
    return all(
        isinstance(model_config[key], int)
        and not isinstance(model_config[key], bool)
        and model_config[key] > 0
        for key in MODEL_CONFIG_KEYS
    )


def is_valid_feature_scale(feature_scale: Any, input_size: int) -> bool:
    if not isinstance(feature_scale, list) or len(feature_scale) != input_size:
        return False
    return all(
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
        for value in feature_scale
    )
