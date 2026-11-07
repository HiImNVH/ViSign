# services/inference-api/tests/integration/test_serving_feature_parity.py
# Parity T037: cung mot WebM, duong offline va duong API (bytes -> clip tam -> adapter) phai ra cung tensor/mask.
import os
from pathlib import Path

import numpy as np
import pytest
from visign_api.inference.feature_extraction import (
    FeatureExtractor,
    FeatureSource,
    build_visign_ai_binding,
)
from visign_api.inference.temporary_clip import open_temporary_clip

# Cung bien moi truong voi test pipeline cua P3 de hai ben chay tren cung clip tham chieu
REFERENCE_CLIP_VARIABLE = "VISIGN_CP2_REFERENCE_WEBM"
PARITY_ABSOLUTE_TOLERANCE = 1e-6


def reference_clip_path() -> Path:
    configured_path = os.environ.get(REFERENCE_CLIP_VARIABLE, "")
    if not configured_path:
        pytest.skip(
            f"Dat {REFERENCE_CLIP_VARIABLE} toi clip WebM tham chieu de chay parity"
        )
    return Path(configured_path)


def test_api_path_matches_offline_extraction(tmp_path: Path) -> None:
    clip_path = reference_clip_path()
    # Can cai extra serving: uv sync --project services/inference-api --extra serving
    pipeline_module = pytest.importorskip("visign_ai.landmarks.pipeline")

    offline_result = pipeline_module.process_video(clip_path)
    extractor = FeatureExtractor(build_visign_ai_binding(), FeatureSource())
    with open_temporary_clip(clip_path.read_bytes(), tmp_path) as uploaded_clip:
        served_features = extractor.extract(uploaded_clip.path)

    np.testing.assert_allclose(
        served_features.tensor,
        offline_result["tensor"],
        rtol=0,
        atol=PARITY_ABSOLUTE_TOLERANCE,
    )
    np.testing.assert_array_equal(
        served_features.tensorMask, offline_result["tensor_mask"]
    )
    np.testing.assert_array_equal(served_features.groupMask, offline_result["masks"])
    assert (
        served_features.featureSchemaVersion
        == offline_result["schema"]["featureSchemaVersion"]
    )
    assert served_features.inputStatus == offline_result["report"]["inputStatus"]
