from contextlib import contextmanager
from copy import deepcopy

import numpy as np
import pytest
from visign_ai.landmarks import holistic_extractor as landmarks
from visign_ai.landmarks.errors import PipelineError
from visign_ai.landmarks.sequence_transform import load_schema


@pytest.fixture
def fake_detectors(monkeypatch):
    opened, closed, used = [], [], []

    @contextmanager
    def create_detector(*args):
        detector = object()
        opened.append(detector)
        try:
            yield detector
        finally:
            closed.append(detector)

    def detect_sequence(detector, frames, timestamps):
        used.append(detector)
        return []

    monkeypatch.setattr(landmarks, "_read_model", lambda *args: b"model")
    monkeypatch.setattr(
        landmarks,
        "_verify_models",
        lambda schema, read_model: {"version": schema["extractorVersion"]},
    )
    monkeypatch.setattr(landmarks, "_create_detector", create_detector)
    monkeypatch.setattr(landmarks, "_detect_sequence", detect_sequence)
    return opened, closed, used


def test_prepared_detectors_are_consumed_once_and_closed_by_owner(
    tmp_path, fake_detectors
):
    opened, closed, used = fake_detectors
    schema = load_schema()
    frames = [np.zeros((2, 2, 3), dtype=np.uint8)]
    with landmarks.prepare_detectors(schema, tmp_path) as prepared:
        assert len(opened) == 3 and not used
        landmarks.extract(frames, [0], schema, tmp_path, prepared_detectors=prepared)
        assert set(used) == set(opened) and not closed
        with pytest.raises(RuntimeError, match="one clip"):
            landmarks.extract(
                frames, [0], schema, tmp_path, prepared_detectors=prepared
            )
    assert closed == opened[::-1]


def test_discard_unused_set_and_reject_incompatible_schema_or_directory(
    tmp_path, fake_detectors
):
    opened, closed, used = fake_detectors
    schema = load_schema()
    with landmarks.prepare_detectors(schema, tmp_path) as prepared:
        changed = deepcopy(schema)
        changed["preExtractionSampling"]["maxFrames"] = 48
        with pytest.raises(PipelineError) as error:
            landmarks.extract([], [], changed, tmp_path, prepared_detectors=prepared)
        assert error.value.code == "FEATURE_SCHEMA_MISMATCH"
        with pytest.raises(PipelineError) as error:
            landmarks.extract(
                [], [], schema, tmp_path / "other", prepared_detectors=prepared
            )
        assert error.value.code == "MODEL_ASSET_MISMATCH"
    assert len(closed) == len(opened) == 3 and not used
    with pytest.raises(RuntimeError, match="one clip"):
        landmarks.extract([], [], schema, tmp_path, prepared_detectors=prepared)


def test_partial_preparation_failure_closes_opened_detectors(
    tmp_path, fake_detectors, monkeypatch
):
    opened, closed, used = fake_detectors
    create = landmarks._create_detector

    def fail_on_second(*args):
        if opened:
            raise RuntimeError("setup failed")
        return create(*args)

    monkeypatch.setattr(landmarks, "_create_detector", fail_on_second)
    with (
        pytest.raises(RuntimeError, match="setup failed"),
        landmarks.prepare_detectors(load_schema(), tmp_path),
    ):
        pytest.fail("Partially prepared detectors were returned")
    assert len(closed) == len(opened) == 1 and not used


def test_detector_failure_still_consumes_the_set(tmp_path, fake_detectors, monkeypatch):
    opened, closed, _ = fake_detectors
    schema = load_schema()

    def fail_detection(*args):
        raise RuntimeError("detection failed")

    monkeypatch.setattr(landmarks, "_detect_sequence", fail_detection)
    with landmarks.prepare_detectors(schema, tmp_path) as prepared:
        with pytest.raises(RuntimeError, match="detection failed"):
            landmarks.extract([], [], schema, tmp_path, prepared_detectors=prepared)
        with pytest.raises(RuntimeError, match="one clip"):
            landmarks.extract([], [], schema, tmp_path, prepared_detectors=prepared)
    assert len(closed) == len(opened) == 3
