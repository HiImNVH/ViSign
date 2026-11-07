# ai/tests/landmarks/test_extract_manifest.py — Test batch extraction T017.
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from visign_ai.landmarks import extract_manifest as batch
from visign_ai.landmarks.errors import PipelineError
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest

SAMPLE_ID = "fixture_0123456789ab"
HEADER = "sampleId,rawPath\n"


def invoke_cli(root: Path, csv_text: str, monkeypatch: pytest.MonkeyPatch) -> int:
    samples = root / "samples.csv"
    samples.write_text(csv_text, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["extract_manifest", "--samples", str(samples), "--dataset-root", str(root)],
    )
    return batch.main()


def make_sample(root: Path) -> tuple[str, Path]:
    path = root / "clip.mp4"
    contents = b"synthetic fixture; extraction is stubbed"
    path.write_bytes(contents)
    return "fixture_" + hashlib.sha256(contents).hexdigest()[:12], path


@pytest.mark.parametrize(
    "csv_text",
    [
        "rawPath,sampleId\n",
        HEADER,
        HEADER + f"{SAMPLE_ID},clip.webm,extra\n",
        HEADER + "bad-id,clip.webm\n",
        HEADER + f"{SAMPLE_ID},one.webm\n{SAMPLE_ID},two.webm\n",
    ],
    ids=["header", "empty", "columns", "sample-id", "duplicate"],
)
def test_bad_batch_returns_exit_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    csv_text: str,
) -> None:
    assert invoke_cli(tmp_path, csv_text, monkeypatch) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "T017:" in captured.err
    assert not (tmp_path / "processed").exists()


@pytest.mark.parametrize(
    "raw_path", ["/clip.webm", "../clip.webm", r"raw\clip.webm", "C:clip.webm"]
)
def test_rejects_invalid_raw_paths(tmp_path: Path, raw_path: str) -> None:
    with pytest.raises(batch.BatchSampleError) as error:
        batch.source_path(tmp_path.resolve(), raw_path)
    assert error.value.code == "INVALID_RAW_PATH"


def test_rejects_symlink_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    root.mkdir()
    outside = tmp_path / "outside.webm"
    outside.touch()
    try:
        (root / "link.webm").symlink_to(outside)
    except OSError as error:
        pytest.skip(f"Symlink unavailable: {error}")
    with pytest.raises(batch.BatchSampleError) as rejection:
        batch.source_path(root.resolve(), "link.webm")
    assert rejection.value.code == "INVALID_RAW_PATH"


def test_missing_source_and_bad_hash_return_exit_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, path = make_sample(tmp_path)
    missing_id = "fixture_fedcba987654"
    samples = HEADER + f"{missing_id},missing.webm\n{SAMPLE_ID},{path.name}\n"

    def unexpected_extraction(*args: object, **kwargs: object) -> None:
        pytest.fail("Invalid samples must be rejected before extraction.")

    monkeypatch.setattr(batch, "process_video", unexpected_extraction)
    assert invoke_cli(tmp_path, samples, monkeypatch) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["accepted"] == []
    assert report["rejected"] == [
        {"sampleId": missing_id, "code": "SOURCE_NOT_FOUND"},
        {"sampleId": SAMPLE_ID, "code": "SAMPLE_HASH_MISMATCH"},
    ]
    assert not list(tmp_path.rglob("*.npz"))


@pytest.mark.parametrize("code", ["INSUFFICIENT_LANDMARKS", "INVALID_TIMESTAMPS"])
def test_pipeline_rejection_code_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    code: str,
) -> None:
    sample_id, path = make_sample(tmp_path)

    def reject(*args: object, **kwargs: object) -> dict[str, Any]:
        if code == "INSUFFICIENT_LANDMARKS":
            return {"report": {"inputStatus": code}}
        raise PipelineError(code, "fixture")

    monkeypatch.setattr(batch, "process_video", reject)
    assert invoke_cli(tmp_path, HEADER + f"{sample_id},{path.name}\n", monkeypatch) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["rejected"] == [{"sampleId": sample_id, "code": code}]
    assert not list(tmp_path.rglob("*.npz"))


def test_writes_npz_and_rerun_preserves_existing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sample_id, source = make_sample(tmp_path)
    schema = load_schema()
    validity: NDArray[np.bool_] = np.ones((32, 78), dtype=bool)
    validity[0, [0, 21, 42, 48]] = False
    features: NDArray[np.float32] = np.zeros((32, 234), dtype=np.float32)
    features[:, 156:] = validity
    timestamps: NDArray[np.float64] = np.arange(32, dtype=np.float64) * 10
    pipeline_calls: list[Path] = []

    def process(
        path: Path, *, model_dir: Path | None, allow_mp4: bool
    ) -> dict[str, Any]:
        assert path == source.resolve()
        assert model_dir is None and allow_mp4
        pipeline_calls.append(path)
        return {
            "report": {"inputStatus": "HAS_USABLE_FRAMES"},
            "schema": schema,
            "tensor": features,
            "tensor_mask": validity,
            "target": timestamps,
        }

    monkeypatch.setattr(batch, "process_video", process)
    samples = HEADER + f"{sample_id},{source.name}\n"
    assert invoke_cli(tmp_path, samples, monkeypatch) == 0
    report = json.loads(capsys.readouterr().out)
    version = schema["featureSchemaVersion"]
    relative = f"processed/{version}/{sample_id}.npz"
    assert report["acceptedCount"] == 1 and report["rejectedCount"] == 0
    assert report["accepted"][0]["landmarkPath"] == relative
    destination = tmp_path / relative
    with np.load(destination, allow_pickle=False) as archive:
        assert archive["sampleId"].item() == sample_id
        assert archive["features"].dtype == np.float32
        assert archive["features"].shape == (32, 234)
        np.testing.assert_array_equal(archive["features"], features)
        assert archive["missingPointMask"].dtype == np.bool_
        np.testing.assert_array_equal(archive["missingPointMask"], ~validity)
        expected_groups: NDArray[np.bool_] = np.zeros((32, 4), dtype=bool)
        expected_groups[0, :] = True
        assert archive["missingMask"].dtype == np.bool_
        np.testing.assert_array_equal(archive["missingMask"], expected_groups)
        assert archive["timestampsMs"].dtype == np.int64
        np.testing.assert_array_equal(archive["timestampsMs"], timestamps)
        assert archive["featureSchemaVersion"].item() == version
        assert archive["extractorVersion"].item() == schema["extractorVersion"]
        assert archive["schemaSha256"].item() == schema_digest(schema)
        assert archive["normalization"].item() == schema["normalization"]["origin"]
    original = destination.read_bytes()

    assert invoke_cli(tmp_path, samples, monkeypatch) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["rejected"] == [{"sampleId": sample_id, "code": "OUTPUT_EXISTS"}]
    assert len(pipeline_calls) == 1
    assert destination.read_bytes() == original
    assert not list(destination.parent.glob("*.tmp"))
