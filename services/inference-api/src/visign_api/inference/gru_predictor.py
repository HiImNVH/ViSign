# services/inference-api/src/visign_api/inference/gru_predictor.py
# Adapter GRU cho artifact pilot/full: trich dac trung bang pipeline chung voi schema di kem artifact, chay GRU
# va tra lop top-1 theo dung thu tu classLabels da train. Torch/visign_ai chi nap khi kich hoat artifact (T037).
import importlib.util
import pickle
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Self

import numpy as np
from numpy.typing import NDArray

from visign_api.config import (
    DEFAULT_MAX_DURATION_MS,
    DEFAULT_MIN_DURATION_MS,
    Settings,
)
from visign_api.domain.errors import PredictionFailedException
from visign_api.domain.model_version import ModelMetadata
from visign_api.domain.prediction import PredictionTimings
from visign_api.inference.artifact_loader import ArtifactRejectedError, LoadedArtifact
from visign_api.inference.clip_validator import DurationWindow, validate_extracted_clip
from visign_api.inference.feature_extraction import (
    ExtractedFeatures,
    FeatureExtractor,
    FeatureSource,
    build_visign_ai_binding,
)
from visign_api.inference.gru_bundle import (
    FEATURE_SCHEMA_FILE,
    MODEL_WEIGHTS_FILE,
    GruBundle,
    ServingSchema,
    verify_gru_bundle,
)
from visign_api.inference.predictor import RawPrediction

MILLISECONDS_PER_SECOND = 1000
# Chi co khi cai extra serving; thieu thi pilot/full fail closed va service chay degraded
SERVING_EXTRA_MODULES = ("torch", "visign_ai")
# torch.load nem cac loi nay voi file thieu, hong, bi cat cut hoac pickle ngoai danh sach weights_only
CHECKPOINT_READ_ERRORS = (
    OSError,
    RuntimeError,
    ValueError,
    EOFError,
    pickle.UnpicklingError,
)
# PipelineError cua visign_ai la ValueError: schema sai layout hoac detector khong khop hash
SCHEMA_READ_ERRORS = (OSError, ValueError, KeyError, TypeError)
STATE_DICT_ERRORS = (RuntimeError, TypeError, ValueError)


class ClipFeatureExtractor(Protocol):
    def extract(self, clip_path: Path) -> ExtractedFeatures: ...


class SequenceClassifier(Protocol):
    def class_probabilities(
        self, feature_tensor: NDArray[np.float32]
    ) -> NDArray[np.float32]: ...


def contract_duration_window() -> DurationWindow:
    return DurationWindow(minMs=DEFAULT_MIN_DURATION_MS, maxMs=DEFAULT_MAX_DURATION_MS)


@dataclass(frozen=True)
class GruRuntime:
    # Thu muc detector MediaPipe tren may phuc vu (VISIGN_MODEL_DIR); None de visign_ai dung mac dinh
    modelDirectory: Path | None
    durationWindow: DurationWindow = field(default_factory=contract_duration_window)

    @classmethod
    def from_settings(cls, runtime_settings: Settings) -> Self:
        return cls(
            modelDirectory=runtime_settings.visign_model_dir,
            durationWindow=DurationWindow(
                minMs=runtime_settings.min_duration_ms,
                maxMs=runtime_settings.max_duration_ms,
            ),
        )


@dataclass(frozen=True)
class GruComponents:
    featureExtractor: ClipFeatureExtractor
    classifier: SequenceClassifier
    durationWindow: DurationWindow


class GruPredictor:
    def __init__(
        self, loaded_artifact: LoadedArtifact, gru_components: GruComponents
    ) -> None:
        self._loaded_artifact = loaded_artifact
        self._gru_components = gru_components

    @property
    def metadata(self) -> ModelMetadata:
        return self._loaded_artifact.metadata

    def predict(self, clip_path: Path) -> RawPrediction:
        extracted_features = self._gru_components.featureExtractor.extract(clip_path)
        # T049: clip qua ngan/dai, khong nguoi hoac thieu landmark bi chan truoc khi GRU doan bua
        validate_extracted_clip(extracted_features, self._gru_components.durationWindow)
        inference_started = time.perf_counter()
        class_probabilities = self._gru_components.classifier.class_probabilities(
            extracted_features.tensor
        )
        stage_timings = PredictionTimings(
            decode=extracted_features.decodeMs,
            extract=extracted_features.extractMs,
            infer=elapsed_milliseconds(inference_started),
        )
        ensure_probability_vector(class_probabilities, len(self.metadata.classLabels))
        best_class_index = int(np.argmax(class_probabilities))
        class_label = self.metadata.classLabels[best_class_index]
        meaning_id = self.metadata.meaningMap[class_label]
        return RawPrediction(
            classLabel=class_label,
            displayText=self._loaded_artifact.displayTextMap[meaning_id],
            confidence=float(class_probabilities[best_class_index]),
            timingsMs=stage_timings,
            qualityHints=extracted_features.qualityHints,
        )


def elapsed_milliseconds(started_at: float) -> int:
    return round((time.perf_counter() - started_at) * MILLISECONDS_PER_SECOND)


def ensure_probability_vector(
    class_probabilities: NDArray[np.float32], class_count: int
) -> None:
    probability_values = np.asarray(class_probabilities, dtype=np.float64)
    is_probability_vector = (
        probability_values.shape == (class_count,)
        and bool(np.isfinite(probability_values).all())
        and bool((probability_values >= 0.0).all())
        and bool((probability_values <= 1.0).all())
    )
    if not is_probability_vector:
        # Dau ra lech so lop hoac khong phai xac suat: 500 an toan thay vi gan nham nghia
        raise PredictionFailedException()


class TorchSequenceClassifier:
    # Bao GRUClassifier cua visign_ai: batch 1, do dai bang so frame nhu collate_sequences luc train
    def __init__(self, gru_network: Any) -> None:
        self._gru_network = gru_network

    def class_probabilities(
        self, feature_tensor: NDArray[np.float32]
    ) -> NDArray[np.float32]:
        import torch

        sequences = torch.tensor(np.asarray(feature_tensor, dtype=np.float32))
        sequence_lengths = torch.tensor([sequences.shape[0]], dtype=torch.long)
        with torch.inference_mode():
            class_logits = self._gru_network(sequences.unsqueeze(0), sequence_lengths)
            class_probabilities: NDArray[np.float32] = class_logits.softmax(dim=1)[
                0
            ].numpy()
        return class_probabilities


def load_gru_predictor(
    loaded_artifact: LoadedArtifact, gru_runtime: GruRuntime
) -> GruPredictor:
    ensure_serving_extra_installed()
    schema_path = loaded_artifact.directory / FEATURE_SCHEMA_FILE
    gru_bundle = GruBundle(
        schema=read_serving_schema(schema_path, gru_runtime.modelDirectory),
        checkpoint=read_checkpoint(loaded_artifact.directory / MODEL_WEIGHTS_FILE),
    )
    verify_gru_bundle(loaded_artifact, gru_bundle)
    # Trich dac trung bang chinh schema da train, khong dung schema mac dinh cua may phuc vu
    feature_source = FeatureSource(
        expectedSchemaVersion=loaded_artifact.metadata.featureSchemaVersion,
        schemaPath=schema_path,
        modelDirectory=gru_runtime.modelDirectory,
    )
    gru_components = GruComponents(
        featureExtractor=FeatureExtractor(build_visign_ai_binding(), feature_source),
        classifier=TorchSequenceClassifier(build_network(gru_bundle.checkpoint)),
        durationWindow=gru_runtime.durationWindow,
    )
    return GruPredictor(loaded_artifact, gru_components)


def ensure_serving_extra_installed() -> None:
    missing_modules = [
        module_name
        for module_name in SERVING_EXTRA_MODULES
        if importlib.util.find_spec(module_name) is None
    ]
    if missing_modules:
        raise ArtifactRejectedError(
            f"Thieu {missing_modules}; cai extra serving de phuc vu pilot/full"
        )


def read_serving_schema(
    schema_path: Path, model_directory: Path | None
) -> ServingSchema:
    from visign_ai.landmarks.holistic_extractor import extractor_identity
    from visign_ai.landmarks.sequence_transform import load_schema, schema_digest

    try:
        schema_content = load_schema(schema_path)
        installed_extractor = extractor_identity(schema_content, model_directory)
    except SCHEMA_READ_ERRORS as schema_error:
        raise ArtifactRejectedError(
            f"{FEATURE_SCHEMA_FILE} hoac detector MediaPipe khong hop le"
        ) from schema_error
    if installed_extractor["version"] != schema_content.get("extractorVersion"):
        raise ArtifactRejectedError("Detector tren may phuc vu khac extractorVersion")
    return ServingSchema(content=schema_content, digest=schema_digest(schema_content))


def read_checkpoint(weights_path: Path) -> Mapping[str, Any]:
    import torch

    try:
        # weights_only: model.pt chi duoc chua tensor va kieu co ban, khong chay pickle tuy y
        trained_checkpoint = torch.load(
            weights_path, map_location="cpu", weights_only=True
        )
    except CHECKPOINT_READ_ERRORS as read_error:
        raise ArtifactRejectedError(
            f"Khong nap an toan duoc {MODEL_WEIGHTS_FILE}"
        ) from read_error
    if not isinstance(trained_checkpoint, Mapping):
        raise ArtifactRejectedError(
            f"{MODEL_WEIGHTS_FILE} phai chua checkpoint dang dict"
        )
    return trained_checkpoint


def build_network(trained_checkpoint: Mapping[str, Any]) -> Any:
    from visign_ai.training.gru_classifier import GRUClassifier

    gru_network = GRUClassifier(**trained_checkpoint["modelConfig"])
    try:
        gru_network.load_state_dict(trained_checkpoint["stateDict"], strict=True)
    except STATE_DICT_ERRORS as weights_error:
        raise ArtifactRejectedError(
            "stateDict khong khop kien truc GRU trong modelConfig"
        ) from weights_error
    # Che do suy luan giong buoc validate luc train
    return gru_network.eval()
