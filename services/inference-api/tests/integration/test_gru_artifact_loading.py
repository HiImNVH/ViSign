# services/inference-api/tests/integration/test_gru_artifact_loading.py
# T036 -> T037: artifact do CLI train that tao ra phai nap qua registry, giu thu tu lop, tinh xac suat
# giong luc train va fail closed khi goi bi sua hoac model.pt chua pickle doc. Can extra serving.
import json
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

SERVING_EXTRA_REASON = (
    "Can extra serving: uv sync --project services/inference-api --extra serving"
)
pytest.importorskip("torch", reason=SERVING_EXTRA_REASON)
pytest.importorskip("visign_ai.training.train", reason=SERVING_EXTRA_REASON)

import torch
from fastapi.testclient import TestClient
from visign_ai.landmarks.extract_manifest import write_sequence
from visign_ai.landmarks.holistic_extractor import resolve_model_dir
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training import train as training_cli
from visign_ai.training.gru_classifier import GRUClassifier
from visign_ai.training.sequence_dataset import collate_sequences
from visign_api.config import Settings
from visign_api.domain.model_version import ArtifactKind
from visign_api.domain.prediction import PredictionQualityHints
from visign_api.inference.artifact_loader import (
    ArtifactRejectedError,
    load_artifact,
)
from visign_api.inference.feature_extraction import ExtractedFeatures
from visign_api.inference.gru_bundle import (
    FEATURE_SCHEMA_FILE,
    MODEL_WEIGHTS_FILE,
)
from visign_api.inference.gru_predictor import (
    GruComponents,
    GruPredictor,
    GruRuntime,
    TorchSequenceClassifier,
    build_network,
    read_checkpoint,
)
from visign_api.inference.predictor_registry import (
    PredictorRegistry,
    build_predictor_factories,
)
from visign_api.main import create_app

if not all(
    (resolve_model_dir() / detector_file).is_file()
    for detector_file in load_schema()["modelFiles"].values()
):
    pytest.skip(
        "Chay ai/setup_models.py de tai detector MediaPipe", allow_module_level=True
    )

# Thu tu class map co chu y khac bang chu cai: artifact phai giu dung thu tu nay
CLASS_MAP = {
    "SOT_HCM_1": {"meaningId": "SOT", "displayText": "Sốt"},
    "CAM_ON_HN_1": {"meaningId": "CAM_ON", "displayText": "Cảm ơn"},
}
THRESHOLD_CANDIDATES = [0.5, 0.7]
TRAINING_CONFIG: dict[str, Any] = {
    "artifact_kind": "pilot",
    "min_meanings": 1,
    "max_meanings": 3,
    "input_size": 234,
    "target_frame_count": 32,
    "seed": 42,
    "hidden_size": 4,
    "num_layers": 1,
    "batch_size": 2,
    "epochs": 2,
    "learning_rate": 0.001,
    "threshold_candidates": THRESHOLD_CANDIDATES,
}
MODEL_VERSION = "pilot-gru-test-v1"
SPLITS = ("train", "validation", "test")
MANIFEST_COLUMNS = (
    "sampleId",
    "classLabel",
    "meaningId",
    "landmarkPath",
    "split",
    "recordingSessionId",
    "licenseStatus",
    "verificationStatus",
)
VALIDITY_OFFSET = 156
PROBABILITY_TOLERANCE = 1e-6


def approved_schema(workspace: Path) -> dict[str, Any]:
    # Schema repo con DRAFT; CLI T036 chi train tren ban APPROVED nen test duyet tren ban sao
    feature_schema = load_schema()
    feature_schema["status"] = "APPROVED"
    (workspace / "schema.json").write_text(json.dumps(feature_schema), encoding="utf-8")
    return feature_schema


def synthetic_sequence(
    feature_schema: dict[str, Any], class_index: int
) -> dict[str, Any]:
    features: NDArray[np.float32] = np.full(
        (32, 234), class_index / 2, dtype=np.float32
    )
    features[:, VALIDITY_OFFSET:] = 1
    return {
        "schema": feature_schema,
        "tensor": features,
        "tensor_mask": features[:, VALIDITY_OFFSET:] == 1,
        "target": np.linspace(0, 1000, 32),
    }


def write_manifest(workspace: Path, feature_schema: dict[str, Any]) -> None:
    manifest_lines = [",".join(MANIFEST_COLUMNS)]
    for split in SPLITS:
        for class_index, (class_label, class_info) in enumerate(CLASS_MAP.items()):
            sample_id = f"{split}-{class_index}"
            if split != "test":
                sequence = synthetic_sequence(feature_schema, class_index)
                write_sequence(workspace / f"{sample_id}.npz", sample_id, sequence)
            manifest_lines.append(
                f"{sample_id},{class_label},{class_info['meaningId']},{sample_id}.npz,"
                f"{split},{sample_id},approved,verified"
            )
    (workspace / "pilot.csv").write_text("\n".join(manifest_lines), encoding="utf-8")


def training_arguments(workspace: Path) -> list[str]:
    write_manifest(workspace, approved_schema(workspace))
    (workspace / "class-map.json").write_text(
        json.dumps(CLASS_MAP, ensure_ascii=False), encoding="utf-8"
    )
    (workspace / "config.json").write_text(
        json.dumps(TRAINING_CONFIG), encoding="utf-8"
    )
    named_inputs = {
        "manifest": "pilot.csv",
        "class-map": "class-map.json",
        "feature-root": ".",
        "schema": "schema.json",
        "config": "config.json",
    }
    cli_arguments = ["train", "--dataset-version", "pilot-v1"]
    for option, relative_path in named_inputs.items():
        cli_arguments += [f"--{option}", str(workspace / relative_path)]
    return [*cli_arguments, "--model-version", MODEL_VERSION]


@pytest.fixture(scope="module")
def t036_artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("t036")
    artifact_directory = workspace / MODEL_VERSION
    cli_arguments = [
        *training_arguments(workspace),
        "--output",
        str(artifact_directory),
    ]
    deterministic_before = torch.are_deterministic_algorithms_enabled()
    # CLI train dat seed va che do deterministic toan cuc; khoi phuc de khong anh huong test khac
    with torch.random.fork_rng(devices=[]), pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(sys, "argv", cli_arguments)
        assert training_cli.main() == 0
    torch.use_deterministic_algorithms(deterministic_before)
    return artifact_directory


def gru_registry_with(artifact_directory: Path) -> PredictorRegistry:
    gru_registry = PredictorRegistry(
        build_predictor_factories(GruRuntime(modelDirectory=None))
    )
    gru_registry.activate(artifact_directory, None)
    return gru_registry


def test_t036_artifact_activates_through_default_registry(t036_artifact: Path) -> None:
    gru_registry = gru_registry_with(t036_artifact)

    served_metadata = gru_registry.active_predictor.metadata
    assert isinstance(gru_registry.active_predictor, GruPredictor)
    assert served_metadata.artifactKind is ArtifactKind.PILOT
    assert served_metadata.classLabels == list(CLASS_MAP)
    assert served_metadata.demoReady is False
    assert served_metadata.acceptanceThreshold in THRESHOLD_CANDIDATES


def test_health_and_model_info_report_the_trained_pilot(t036_artifact: Path) -> None:
    pilot_settings = Settings(_env_file=None, model_artifact_path=t036_artifact)  # type: ignore[call-arg]

    with TestClient(create_app(pilot_settings)) as pilot_client:
        health = pilot_client.get("/api/v1/health").json()
        model_info = pilot_client.get("/api/v1/model-info").json()

    assert health == {"status": "ok", "modelReady": True, "modelVersion": MODEL_VERSION}
    assert model_info["artifactKind"] == "pilot"
    assert model_info["meanings"] == ["SOT", "CAM_ON"]
    assert model_info["demoReady"] is False


def test_missing_detector_assets_degrade_instead_of_serving(
    t036_artifact: Path, tmp_path: Path
) -> None:
    # VISIGN_MODEL_DIR tro toi thu muc khong co detector: khong duoc phuc vu pilot bang extractor khac
    misconfigured_settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        model_artifact_path=t036_artifact,
        visign_model_dir=tmp_path / "empty-detectors",
    )

    with TestClient(create_app(misconfigured_settings)) as degraded_client:
        health = degraded_client.get("/api/v1/health").json()

    assert health == {"status": "degraded", "modelReady": False, "modelVersion": None}


def test_served_probabilities_match_training_forward_pass(t036_artifact: Path) -> None:
    trained_checkpoint = read_checkpoint(t036_artifact / MODEL_WEIGHTS_FILE)
    served_classifier = TorchSequenceClassifier(build_network(trained_checkpoint))
    feature_tensor = (
        np.random.default_rng(7).uniform(-1, 1, (32, 234)).astype(np.float32)
    )

    served_probabilities = served_classifier.class_probabilities(feature_tensor)

    # Doc lap voi adapter: dung lai GRUClassifier va collate_sequences cua luc train
    training_network = GRUClassifier(**trained_checkpoint["modelConfig"])
    training_network.load_state_dict(trained_checkpoint["stateDict"])
    training_network.eval()
    sequences, lengths, _ = collate_sequences([(torch.from_numpy(feature_tensor), 0)])
    with torch.inference_mode():
        training_logits = training_network(sequences, lengths)
    expected_probabilities = training_logits.softmax(dim=1)[0].numpy()
    np.testing.assert_allclose(
        served_probabilities, expected_probabilities, rtol=0, atol=PROBABILITY_TOLERANCE
    )


def test_predictor_maps_trained_output_to_class_label(t036_artifact: Path) -> None:
    trained_checkpoint = read_checkpoint(t036_artifact / MODEL_WEIGHTS_FILE)
    served_classifier = TorchSequenceClassifier(build_network(trained_checkpoint))
    served_features = ExtractedFeatures(
        tensor=np.full((32, 234), 0.5, dtype=np.float32),
        tensorMask=np.ones((32, 78), dtype=bool),
        groupMask=np.ones((32, 4), dtype=bool),
        featureSchemaVersion="visign-xy-32-v0.3-draft",
        inputStatus="HAS_USABLE_FRAMES",
        qualityHints=PredictionQualityHints(handsDetectedRatio=1.0, frameCount=32),
        decodeMs=10,
        extractMs=900,
    )

    class FixedExtractor:
        def extract(self, clip_path: Path) -> ExtractedFeatures:
            return served_features

    gru_predictor = GruPredictor(
        load_artifact(t036_artifact, None),
        GruComponents(featureExtractor=FixedExtractor(), classifier=served_classifier),
    )
    raw_prediction = gru_predictor.predict(Path("clip.webm"))

    expected_probabilities = served_classifier.class_probabilities(
        served_features.tensor
    )
    best_index = int(np.argmax(expected_probabilities))
    assert raw_prediction.classLabel == list(CLASS_MAP)[best_index]
    assert raw_prediction.confidence == pytest.approx(
        float(expected_probabilities[best_index])
    )


def rewrite_json(json_path: Path, change: Callable[[dict[str, Any]], object]) -> None:
    json_document = json.loads(json_path.read_text(encoding="utf-8"))
    change(json_document)
    json_path.write_text(
        json.dumps(json_document, ensure_ascii=False), encoding="utf-8"
    )


def truncate_weights(candidate: Path) -> None:
    weights_path = candidate / MODEL_WEIGHTS_FILE
    weights_path.write_bytes(weights_path.read_bytes()[:64])


TAMPERS: dict[str, Callable[[Path], object]] = {
    "reordered-class-labels": lambda candidate: rewrite_json(
        candidate / "model_info.json", lambda info: info["classLabels"].reverse()
    ),
    "changed-display-text": lambda candidate: rewrite_json(
        candidate / "model_info.json",
        lambda info: info["displayTextMap"].update(SOT="Sốt cao"),
    ),
    "edited-schema": lambda candidate: rewrite_json(
        candidate / FEATURE_SCHEMA_FILE,
        lambda schema: schema.update(poseMinVisibility=0.6),
    ),
    "draft-schema": lambda candidate: rewrite_json(
        candidate / FEATURE_SCHEMA_FILE,
        lambda schema: schema.update(status="DRAFT_PENDING_LEAD_REVIEW"),
    ),
    "truncated-weights": truncate_weights,
    "missing-weights": lambda candidate: (candidate / MODEL_WEIGHTS_FILE).unlink(),
    "missing-schema": lambda candidate: (candidate / FEATURE_SCHEMA_FILE).unlink(),
}


@pytest.mark.parametrize("tamper_name", sorted(TAMPERS))
def test_tampered_candidate_is_rejected_and_previous_model_keeps_serving(
    t036_artifact: Path, tmp_path: Path, tamper_name: str
) -> None:
    gru_registry = gru_registry_with(t036_artifact)
    candidate = shutil.copytree(t036_artifact, tmp_path / "candidate")
    TAMPERS[tamper_name](candidate)

    with pytest.raises(ArtifactRejectedError):
        gru_registry.activate(candidate, None)

    assert gru_registry.active_artifact_directory == t036_artifact


class MarkerPayload:
    # Mo phong model.pt doc: neu bi unpickle se tao thu muc danh dau
    def __init__(self, marker_path: Path) -> None:
        self.marker_path = marker_path

    def __reduce__(self) -> tuple[Callable[[str], None], tuple[str]]:
        return (os.mkdir, (str(self.marker_path),))


def test_untrusted_pickle_in_weights_is_never_executed(
    t036_artifact: Path, tmp_path: Path
) -> None:
    candidate = shutil.copytree(t036_artifact, tmp_path / "candidate")
    marker_path = tmp_path / "pickle-executed"
    trained_checkpoint = torch.load(candidate / MODEL_WEIGHTS_FILE, weights_only=True)
    torch.save(
        {**trained_checkpoint, "payload": MarkerPayload(marker_path)},
        candidate / MODEL_WEIGHTS_FILE,
    )

    with pytest.raises(ArtifactRejectedError):
        gru_registry_with(candidate)
    assert not marker_path.exists()

    # Doi chung: neu nap khong co weights_only, payload chay that, nen kiem tra tren co y nghia
    torch.load(candidate / MODEL_WEIGHTS_FILE, weights_only=False)
    assert marker_path.is_dir()
