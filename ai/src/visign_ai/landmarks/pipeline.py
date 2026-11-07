import time
from pathlib import Path

import numpy as np

from .errors import PipelineError
from .holistic_extractor import extract, extractor_identity, group_masks
from .sequence_transform import load_schema, schema_digest, transform
from .temporal_sampling import select_frame_indices
from .video_decoder import VideoDecoder, decode_video

__all__ = ["PipelineError", "decode_video", "load_schema", "process_video", "transform"]


def process_video(
    path,
    expected_schema_version=None,
    schema_path=None,
    model_dir=None,
    *,
    allow_mp4=False,
):
    start = time.perf_counter()
    schema = load_schema(schema_path)
    if (
        expected_schema_version
        and expected_schema_version != schema["featureSchemaVersion"]
    ):
        raise PipelineError("FEATURE_SCHEMA_MISMATCH", "Schema không khớp bên gọi.")
    identity = extractor_identity(schema, model_dir)
    if identity["version"] != schema["extractorVersion"]:
        raise PipelineError(
            "EXTRACTOR_VERSION_MISMATCH", "Extractor khác phiên bản schema đã khóa."
        )
    metadata_checked = time.perf_counter()
    frames, timestamps, integer_ms = VideoDecoder().decode(path, allow_mp4=allow_mp4)
    decoded = time.perf_counter()
    if any(f.shape != frames[0].shape for f in frames):
        raise PipelineError("INVALID_REQUEST", "Kích thước frame thay đổi trong clip.")
    decoded_frame_count = len(frames)
    source_indices = select_frame_indices(timestamps, schema)
    frames = [frames[index] for index in source_indices]
    timestamps = timestamps[source_indices]
    integer_ms = integer_ms[source_indices]
    coords, valid, visibility, presence, hand_scores, ambiguous = extract(
        frames, integer_ms, schema, model_dir
    )
    extracted = time.perf_counter()
    tensor, tensor_valid, target = transform(
        coords, valid, timestamps, frames[0].shape[1], frames[0].shape[0], schema
    )
    finished = time.perf_counter()
    groups = group_masks(valid)
    tensor_groups = group_masks(tensor_valid)
    usable = tensor_groups[:, 2] & tensor_groups[:, :2].any(axis=1)
    both = groups[:, 0] & groups[:, 1]
    report = {
        "demoReady": False,
        "stage": "preprocessing-only",
        "classificationAvailable": False,
        "featureSchemaVersion": schema["featureSchemaVersion"],
        "extractor": identity,
        "schemaSha256": schema_digest(schema),
        "sourceName": Path(path).name,
        "frameCount": len(frames),
        "decodedFrameCount": decoded_frame_count,
        "sourceFrameIndices": source_indices.tolist(),
        "samplingPolicy": schema.get("preExtractionSampling", {"method": "all-frames"}),
        "ptsSpanMs": float(timestamps[-1]),
        "durationNote": "First-to-last frame PTS span; not verified duration",
        "tensorShape": list(tensor.shape),
        "finiteTensor": bool(np.isfinite(tensor).all()),
        "nonzeroTensorValues": int(np.count_nonzero(tensor)),
        "detectionRatios": dict(
            zip(schema["missingMaskSchema"], groups.mean(axis=0).tolist())
        ),
        "pointValidRatios": dict(
            zip(schema["landmarkOrder"], valid.mean(axis=0).tolist())
        ),
        "bothHandsFrames": np.flatnonzero(both).tolist(),
        "bothHandsAndShouldersFrames": np.flatnonzero(both & groups[:, 2]).tolist(),
        "duplicateHandSideFrames": sorted({x["frame"] for x in ambiguous}),
        "usableTensorFrameRatio": float(usable.mean()),
        "inputStatus": "HAS_USABLE_FRAMES"
        if usable.any()
        else "INSUFFICIENT_LANDMARKS",
        "timingsMs": {
            "metadataValidation": round((metadata_checked - start) * 1000, 2),
            "decode": round((decoded - metadata_checked) * 1000, 2),
            "extractIncludingInit": round((extracted - decoded) * 1000, 2),
            "transform": round((finished - extracted) * 1000, 2),
            "total": round((finished - start) * 1000, 2),
        },
        "limitations": [
            "Draft schema, no sign classifier",
            "Hand side labels are detector outputs; mirrored input needs review",
            "Low-confidence pose estimates are retained but masked; not used for normalization",
            "No fabricated missing hand landmarks",
            "Not API parity, browser-camera or release-gate evidence",
        ],
    }
    return {
        "report": report,
        "schema": schema,
        "coords": coords,
        "point_valid": valid,
        "visibility": visibility,
        "presence": presence,
        "hand_scores": hand_scores,
        "ambiguous": ambiguous,
        "masks": groups,
        "timestamps": timestamps,
        "tensor": tensor,
        "tensor_mask": tensor_valid,
        "target": target,
    }
