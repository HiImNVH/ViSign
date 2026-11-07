import json
import os
from pathlib import Path

import av
import numpy as np
import pytest
from visign_ai.landmarks.errors import PipelineError
from visign_ai.landmarks.holistic_extractor import extractor_identity
from visign_ai.landmarks.pipeline import process_video
from visign_ai.landmarks.sequence_transform import load_schema, transform
from visign_ai.landmarks.temporal_sampling import select_frame_indices
from visign_ai.landmarks.video_decoder import VideoDecoder


def make_clip(path, codec, count, *, rate=25, format="webm"):
    rgb = np.zeros((48, 64, 3), dtype=np.uint8)
    rgb[:, :32, 0] = 255
    rgb[:, 32:, 2] = 255
    with av.open(str(path), mode="w", format=format) as output:
        stream = output.add_stream(codec, rate=rate)
        stream.width = 64
        stream.height = 48
        stream.pix_fmt = "yuv420p"
        for _ in range(count):
            output.mux(stream.encode(av.VideoFrame.from_ndarray(rgb, format="rgb24")))
        output.mux(stream.encode(None))
    return path


@pytest.mark.parametrize("codec", ["libvpx", "libvpx-vp9"])
def test_webm_keeps_orientation_and_pts(tmp_path, codec):
    path = make_clip(tmp_path / "clip.webm", codec, 10)
    frames, pts, stamps = VideoDecoder().decode(path)
    np.testing.assert_array_equal(pts, np.arange(10) * 40)
    np.testing.assert_array_equal(stamps, pts)
    assert all(f[24, 8, 0] > 200 and f[24, 56, 2] > 200 for f in frames)


@pytest.mark.parametrize(
    ("count", "code"), [(3, "CLIP_TOO_SHORT"), (152, "CLIP_TOO_LONG")]
)
def test_duration_rejection(tmp_path, count, code):
    path = make_clip(tmp_path / "clip.webm", "libvpx", count)
    with pytest.raises(PipelineError) as error:
        VideoDecoder().decode(path)
    assert error.value.code == code


@pytest.mark.parametrize("count", [7, 121])
def test_inclusive_duration_limits(tmp_path, count):
    path = make_clip(tmp_path / "clip.webm", "libvpx", count, rate=20)
    _, pts, _ = VideoDecoder().decode(path)
    assert pts[-1] in {300, 6000}


def test_corrupt_webm(tmp_path):
    path = make_clip(tmp_path / "clip.webm", "libvpx", 10)
    path.write_bytes(path.read_bytes()[:48])
    with pytest.raises(PipelineError) as error:
        VideoDecoder().decode(path)
    assert error.value.code == "CLIP_DECODE_FAILED"


def test_mp4_requires_explicit_offline_opt_in(tmp_path):
    path = make_clip(tmp_path / "clip.mp4", "mpeg4", 10, format="mp4")
    with pytest.raises(PipelineError) as error:
        VideoDecoder().decode(path)
    assert error.value.code == "UNSUPPORTED_MEDIA_TYPE"
    assert len(VideoDecoder().decode(path, allow_mp4=True)[0]) == 10


def test_rejects_matroska_even_with_vp8(tmp_path):
    path = make_clip(tmp_path / "clip.webm", "libvpx", 10, format="matroska")
    with pytest.raises(PipelineError) as error:
        VideoDecoder().decode(path)
    assert error.value.code == "UNSUPPORTED_MEDIA_TYPE"


def test_size_checked_before_decoder(tmp_path):
    path = tmp_path / "large.webm"
    with path.open("wb") as file:
        file.truncate(10 * 1024 * 1024 + 1)
    with pytest.raises(PipelineError) as error:
        VideoDecoder().decode(path)
    assert error.value.code == "CLIP_TOO_LARGE"


def test_draft_schema_tensor_normalization_and_missing_points():
    schema = load_schema()
    assert schema["featureSchemaVersion"] == "visign-xy-32-v0.3-draft"
    assert schema["status"] == "DRAFT_PENDING_LEAD_REVIEW"
    coords = np.zeros((3, 78, 2), dtype=np.float32)
    valid = np.zeros((3, 78), dtype=bool)
    coords[:, 42:44] = [[0.25, 0.5], [0.75, 0.5]]
    coords[:, 0] = [0.75, 1]
    valid[:, [0, 42, 43]] = True
    valid[1, 0] = False
    valid[2, 42] = False
    tensor, mask, target = transform(coords, valid, [0, 150, 300], 200, 100, schema)
    assert tensor.shape == (32, 234) and tensor.dtype == np.float32
    assert mask.shape == (32, 78) and mask.dtype == bool
    assert (target[0], target[-1]) == (0, 300)
    np.testing.assert_array_equal(tensor[0, :2], [0.5, 0.5])
    np.testing.assert_array_equal(tensor[1:, :2], 0)
    np.testing.assert_array_equal(tensor[:, 156:], mask)
    assert not mask[-1].any()


def test_sampling_caps_frames_and_preserves_endpoints():
    pts = np.arange(121) * 40
    indices = select_frame_indices(pts, load_schema())
    assert len(indices) == 64
    assert (indices[0], indices[-1]) == (0, 120)
    assert np.all(np.diff(indices) > 0)


@pytest.mark.parametrize("browser", ["chrome", "msedge"])
@pytest.mark.parametrize("codec", ["vp8", "vp9"])
def test_browser_recordings(browser, codec):
    root = os.environ.get("VISIGN_BROWSER_FIXTURES")
    if not root:
        pytest.skip("Set VISIGN_BROWSER_FIXTURES to local MediaRecorder fixtures.")
    path = Path(root) / f"{browser}-{codec}.webm"
    with av.open(str(path)) as container:
        assert container.streams.video[0].codec_context.name == codec
    frames, pts, milliseconds = VideoDecoder().decode(path)
    assert len(frames) > 10
    assert np.all(np.diff(pts) > 0) and np.all(np.diff(milliseconds) > 0)
    assert 2000 <= pts[-1] <= 3500


def test_real_extractor_repeatability():
    clip = os.environ.get("VISIGN_CP2_REFERENCE_WEBM")
    if not clip:
        pytest.skip("Set VISIGN_CP2_REFERENCE_WEBM to a local reference clip.")
    first = process_video(clip)
    second = process_video(clip)
    assert first["tensor"].shape == (32, 234)
    assert np.isfinite(first["tensor"]).all()
    assert first["report"]["inputStatus"] == "HAS_USABLE_FRAMES"
    assert (
        first["report"]["extractor"]["version"] == first["schema"]["extractorVersion"]
    )
    assert len(first["report"]["extractor"]["sha256"]) == 3
    np.testing.assert_allclose(first["tensor"], second["tensor"], rtol=0, atol=1e-6)
    for key in ("point_valid", "masks", "tensor_mask"):
        np.testing.assert_array_equal(first[key], second[key])


def test_rejects_incompatible_schema(tmp_path):
    schema = load_schema()
    schema["targetFrameCount"] = 64
    path = tmp_path / "feature_schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(PipelineError) as error:
        load_schema(path)
    assert error.value.code == "FEATURE_SCHEMA_MISMATCH"


def test_rejects_unpinned_detector_assets(tmp_path):
    schema = load_schema()
    for filename in schema["modelFiles"].values():
        (tmp_path / filename).write_bytes(b"not a pinned detector")
    with pytest.raises(PipelineError) as error:
        extractor_identity(schema, tmp_path)
    assert error.value.code == "MODEL_ASSET_MISMATCH"
