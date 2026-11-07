# services/inference-api/tests/integration/test_gru_artifact_loading.py
# T036 -> T037: artifact pilot/full do CLI train that tao ra phai nap qua registry, giu thu tu lop, tinh xac
# suat giong luc train, du doan qua HTTP va fail closed khi goi bi sua hoac model.pt chua pickle doc. Can extra serving.
import json
import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
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

import httpx2
import torch
from fastapi.testclient import TestClient
from visign_ai.landmarks.errors import PipelineError
from visign_ai.landmarks.holistic_extractor import resolve_model_dir
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training.gru_classifier import GRUClassifier
from visign_ai.training.sequence_dataset import collate_sequences
from visign_api.config import Settings
from visign_api.domain.model_version import ArtifactKind
from visign_api.domain.prediction import (
    REJECTED_PREDICTION_TEXT,
    PredictionQualityHints,
)
from visign_api.inference import gru_predictor as gru_predictor_module
from visign_api.inference.artifact_loader import (
    ArtifactRejectedError,
    load_artifact,
)
from visign_api.inference.clip_validator import DurationWindow
from visign_api.inference.feature_extraction import ExtractedFeatures, PipelineBinding
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


from t036_artifact_builder import (
    CLASS_MAP,
    FULL_CLASS_MAP,
    FULL_SPEC,
    MODEL_VERSION,
    P0_MEANINGS,
    PILOT_SPEC,
    THRESHOLD_CANDIDATES,
    VALIDITY_OFFSET,
    train_artifact,
)

PROBABILITY_TOLERANCE = 1e-6


@pytest.fixture(scope="module")
def t036_artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return train_artifact(tmp_path_factory.mktemp("t036"), PILOT_SPEC)


@pytest.fixture(scope="module")
def full_t036_artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return train_artifact(tmp_path_factory.mktemp("t036-full"), FULL_SPEC)


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
        ptsSpanMs=1000.0,
        detectedAnyLandmark=True,
    )

    class FixedExtractor:
        def extract(self, clip_path: Path) -> ExtractedFeatures:
            return served_features

    gru_predictor = GruPredictor(
        load_artifact(t036_artifact, None),
        GruComponents(
            featureExtractor=FixedExtractor(),
            classifier=served_classifier,
            durationWindow=DurationWindow(minMs=300, maxMs=6000),
        ),
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


def test_full_artifact_serves_ten_meanings(full_t036_artifact: Path) -> None:
    gru_registry = gru_registry_with(full_t036_artifact)
    trained_checkpoint = read_checkpoint(full_t036_artifact / MODEL_WEIGHTS_FILE)
    class_probabilities = TorchSequenceClassifier(
        build_network(trained_checkpoint)
    ).class_probabilities(served_tensor())

    served_metadata = gru_registry.active_predictor.metadata
    assert served_metadata.artifactKind is ArtifactKind.FULL
    assert served_metadata.classLabels == list(FULL_CLASS_MAP)
    # Metric danh gia con null nen full moi train chua qua gate demo (T059)
    assert served_metadata.demoReady is False
    assert class_probabilities.shape == (len(P0_MEANINGS),)
    assert float(class_probabilities.sum()) == pytest.approx(1.0, abs=1e-5)


@dataclass(frozen=True)
class ExtractionOutcome:
    inputStatus: str
    anyValidPoint: bool


@dataclass(frozen=True)
class ExpectedPrediction:
    confidence: float
    accepted: bool
    classLabel: str | None
    text: str


USABLE_EXTRACTION = ExtractionOutcome("HAS_USABLE_FRAMES", anyValidPoint=True)
SAMPLE_CLIP = b"\x1aE\xdf\xa3\x9f\x42\x86\x81\x01\x42\x82\x84webm integration clip"
SOURCE_FRAME_COUNT = 8
FAKE_DECODE_MS = 20.0
FAKE_TOTAL_MS = 900.0


def served_tensor() -> NDArray[np.float32]:
    features: NDArray[np.float32] = np.full((32, 234), 0.5, dtype=np.float32)
    features[:, VALIDITY_OFFSET:] = 1
    return features


def fake_pipeline_result(
    feature_schema: dict[str, Any], extraction_outcome: ExtractionOutcome
) -> dict[str, Any]:
    usable = extraction_outcome.inputStatus == "HAS_USABLE_FRAMES"
    tensor = served_tensor() if usable else np.zeros((32, 234), dtype=np.float32)
    return {
        "schema": feature_schema,
        "tensor": tensor,
        "tensor_mask": tensor[:, VALIDITY_OFFSET:] == 1,
        "masks": np.full((SOURCE_FRAME_COUNT, 4), usable),
        "point_valid": np.full(
            (SOURCE_FRAME_COUNT, 78), extraction_outcome.anyValidPoint
        ),
        "report": {
            "inputStatus": extraction_outcome.inputStatus,
            "decodedFrameCount": 46,
            "ptsSpanMs": 1500.0,
            "timingsMs": {"decode": FAKE_DECODE_MS, "total": FAKE_TOTAL_MS},
        },
    }


def install_fake_pipeline(
    monkeypatch: pytest.MonkeyPatch, extraction_outcome: ExtractionOutcome
) -> list[dict[str, Any]]:
    # Chi thay MediaPipe bang ket qua trich dac trung xac dinh; HTTP, kiem clip, slot, clip tam,
    # GRU da train va luat quyet dinh van chay that
    pipeline_calls: list[dict[str, Any]] = []

    def fake_process_video(clip_path: Path, **pipeline_options: Any) -> dict[str, Any]:
        pipeline_calls.append({"path": Path(clip_path), **pipeline_options})
        feature_schema = load_schema(pipeline_options["schema_path"])
        return fake_pipeline_result(feature_schema, extraction_outcome)

    fake_binding = PipelineBinding(run=fake_process_video, errorType=PipelineError)
    monkeypatch.setattr(
        gru_predictor_module, "build_visign_ai_binding", lambda: fake_binding
    )
    return pipeline_calls


def post_clip_to(artifact_directory: Path) -> httpx2.Response:
    artifact_settings = Settings(_env_file=None, model_artifact_path=artifact_directory)  # type: ignore[call-arg]
    with TestClient(create_app(artifact_settings)) as artifact_client:
        return artifact_client.post(
            "/api/v1/predictions",
            files={"clip": ("capture.webm", SAMPLE_CLIP, "video/webm;codecs=vp8")},
        )


def expected_prediction(artifact_directory: Path) -> ExpectedPrediction:
    # Tinh doc lap tu trong so va metadata cua artifact de doi chieu response HTTP
    loaded_artifact = load_artifact(artifact_directory, None)
    trained_checkpoint = read_checkpoint(artifact_directory / MODEL_WEIGHTS_FILE)
    class_probabilities = TorchSequenceClassifier(
        build_network(trained_checkpoint)
    ).class_probabilities(served_tensor())
    best_index = int(np.argmax(class_probabilities))
    confidence = float(class_probabilities[best_index])
    best_label = loaded_artifact.metadata.classLabels[best_index]
    best_text = loaded_artifact.displayTextMap[
        loaded_artifact.metadata.meaningMap[best_label]
    ]
    accepted = confidence >= loaded_artifact.metadata.acceptanceThreshold
    return ExpectedPrediction(
        confidence=confidence,
        accepted=accepted,
        classLabel=best_label if accepted else None,
        text=best_text if accepted else REJECTED_PREDICTION_TEXT,
    )


@pytest.mark.parametrize("artifact_fixture", ["t036_artifact", "full_t036_artifact"])
def test_http_prediction_runs_the_trained_gru(
    artifact_fixture: str,
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_directory: Path = request.getfixturevalue(artifact_fixture)
    pipeline_calls = install_fake_pipeline(monkeypatch, USABLE_EXTRACTION)

    prediction_response = post_clip_to(artifact_directory)

    prediction = prediction_response.json()
    expected = expected_prediction(artifact_directory)
    assert prediction_response.status_code == 200
    assert (
        prediction["modelVersion"]
        == load_artifact(artifact_directory, None).metadata.modelVersion
    )
    assert prediction["confidence"] == pytest.approx(
        expected.confidence, abs=PROBABILITY_TOLERANCE
    )
    assert (prediction["accepted"], prediction["classLabel"], prediction["text"]) == (
        expected.accepted,
        expected.classLabel,
        expected.text,
    )
    assert prediction["timingsMs"]["decode"] == round(FAKE_DECODE_MS)
    assert prediction["timingsMs"]["extract"] == round(FAKE_TOTAL_MS - FAKE_DECODE_MS)
    # Adapter trich dac trung bang schema di kem artifact; clip tam bi xoa sau khi phuc vu
    assert pipeline_calls[0]["schema_path"] == artifact_directory / FEATURE_SCHEMA_FILE
    assert not pipeline_calls[0]["path"].exists()


@pytest.mark.parametrize(
    ("extraction_outcome", "expected_code"),
    [
        (
            ExtractionOutcome("INSUFFICIENT_LANDMARKS", anyValidPoint=False),
            "NO_PERSON_DETECTED",
        ),
        (
            ExtractionOutcome("INSUFFICIENT_LANDMARKS", anyValidPoint=True),
            "INSUFFICIENT_LANDMARKS",
        ),
    ],
)
def test_http_applies_p3_person_rule_before_gru(
    t036_artifact: Path,
    monkeypatch: pytest.MonkeyPatch,
    extraction_outcome: ExtractionOutcome,
    expected_code: str,
) -> None:
    # Quy tac P3 (T037 handoff) qua duong HTTP that: khong diem nao hop le → khong co nguoi;
    # co diem nhung khong co buoc tensor du vai va tay → thieu landmark
    install_fake_pipeline(monkeypatch, extraction_outcome)

    rejected_response = post_clip_to(t036_artifact)

    assert rejected_response.status_code == 422
    assert rejected_response.json()["code"] == expected_code
