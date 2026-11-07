# services/inference-api/tests/integration/test_prepared_detector_serving.py
# T065/SC-002 phia API: bo detector that duoc tao o thread nen cho dung schema cua artifact; trich dac trung bang
# bo tao san giong het duong tao detector theo tung clip; candidate bi tu choi khong de lai thread nen.
import os
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import pytest

SERVING_EXTRA_REASON = (
    "Can extra serving: uv sync --project services/inference-api --extra serving"
)
pytest.importorskip("torch", reason=SERVING_EXTRA_REASON)
pytest.importorskip("visign_ai.training.train", reason=SERVING_EXTRA_REASON)

from visign_ai.landmarks.holistic_extractor import resolve_model_dir
from visign_ai.landmarks.sequence_transform import load_schema
from visign_api.inference import gru_predictor as gru_predictor_module
from visign_api.inference.artifact_loader import ArtifactRejectedError, load_artifact
from visign_api.inference.detector_pool import DetectorPool
from visign_api.inference.feature_extraction import (
    FeatureExtractor,
    FeatureSource,
    build_visign_ai_binding,
    open_visign_ai_detectors,
)
from visign_api.inference.gru_bundle import FEATURE_SCHEMA_FILE
from visign_api.inference.gru_predictor import GruRuntime, load_gru_predictor
from visign_api.inference.temporary_clip import open_temporary_clip

if not all(
    (resolve_model_dir() / detector_file).is_file()
    for detector_file in load_schema()["modelFiles"].values()
):
    pytest.skip(
        "Chay ai/setup_models.py de tai detector MediaPipe", allow_module_level=True
    )

from t036_artifact_builder import PILOT_SPEC, train_artifact

REFERENCE_CLIP_VARIABLE = "VISIGN_CP2_REFERENCE_WEBM"
PARITY_ABSOLUTE_TOLERANCE = 1e-6


@pytest.fixture(scope="module")
def t036_artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return train_artifact(tmp_path_factory.mktemp("t036-prewarm"), PILOT_SPEC)


def artifact_detector_pool(artifact_directory: Path) -> DetectorPool:
    return DetectorPool(
        partial(
            open_visign_ai_detectors, artifact_directory / FEATURE_SCHEMA_FILE, None
        )
    )


def test_real_detector_set_is_prepared_for_the_artifact_schema(
    t036_artifact: Path,
) -> None:
    detector_pool = artifact_detector_pool(t036_artifact)

    with detector_pool.lease() as prepared_detectors:
        leased = prepared_detectors
    detector_pool.close(wait=True)

    assert leased is not None


def test_rejected_candidate_starts_no_background_detectors(
    t036_artifact: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started_pools: list[Any] = []

    def record_pool(*pool_arguments: Any) -> None:
        started_pools.append(pool_arguments)

    def reject_network(trained_checkpoint: Any) -> Any:
        raise ArtifactRejectedError("stateDict khong khop kien truc GRU")

    monkeypatch.setattr(gru_predictor_module, "DetectorPool", record_pool)
    monkeypatch.setattr(gru_predictor_module, "build_network", reject_network)

    with pytest.raises(ArtifactRejectedError):
        load_gru_predictor(
            load_artifact(t036_artifact, None),
            GruRuntime(modelDirectory=None, prewarmDetectors=True),
        )

    assert started_pools == []


def test_prepared_detectors_extract_the_same_features_as_per_clip_detectors(
    t036_artifact: Path, tmp_path: Path
) -> None:
    configured_clip = os.environ.get(REFERENCE_CLIP_VARIABLE, "")
    if not configured_clip:
        pytest.skip(f"Dat {REFERENCE_CLIP_VARIABLE} toi clip WebM co nguoi")
    feature_source = FeatureSource(schemaPath=t036_artifact / FEATURE_SCHEMA_FILE)
    per_clip_extractor = FeatureExtractor(build_visign_ai_binding(), feature_source)
    prepared_extractor = FeatureExtractor(
        build_visign_ai_binding(), feature_source, artifact_detector_pool(t036_artifact)
    )

    with open_temporary_clip(
        Path(configured_clip).read_bytes(), tmp_path
    ) as uploaded_clip:
        per_clip_features = per_clip_extractor.extract(uploaded_clip.path)
        # Lan hai dung bo moi duoc chuan bi sau request dau: moi bo chi dung mot lan
        prepared_runs = [
            prepared_extractor.extract(uploaded_clip.path) for _ in range(2)
        ]
    prepared_extractor.close()

    for prepared_features in prepared_runs:
        np.testing.assert_allclose(
            prepared_features.tensor,
            per_clip_features.tensor,
            atol=PARITY_ABSOLUTE_TOLERANCE,
            rtol=0,
        )
        np.testing.assert_array_equal(
            prepared_features.tensorMask, per_clip_features.tensorMask
        )
        np.testing.assert_array_equal(
            prepared_features.groupMask, per_clip_features.groupMask
        )
