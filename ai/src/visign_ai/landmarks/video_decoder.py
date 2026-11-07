from pathlib import Path

import av
import cv2
import numpy as np

from .errors import PipelineError


def decode_video(path, *, allow_mp4=False):
    """Decode browser WebM without flipping pixels; opt in to offline MP4."""
    path = Path(path)
    if not path.is_file():
        raise PipelineError("INVALID_REQUEST", "Video không tồn tại.")
    if path.stat().st_size > 10 * 1024 * 1024:
        raise PipelineError("CLIP_TOO_LARGE", "Pipeline giới hạn 10 MiB.")
    with path.open("rb") as source:
        header = source.read(4096)
    is_webm = header.startswith(b"\x1aE\xdf\xa3") and b"\x42\x82\x84webm" in header
    if not is_webm and not (allow_mp4 and header[4:8] == b"ftyp"):
        raise PipelineError(
            "UNSUPPORTED_MEDIA_TYPE", "Định dạng video không được hỗ trợ."
        )
    frames, timestamps = [], []
    try:
        with av.open(str(path)) as container:
            if not container.streams.video:
                raise PipelineError("CLIP_DECODE_FAILED", "Không có video stream.")
            stream = container.streams.video[0]
            if is_webm and stream.codec_context.name not in {"vp8", "vp9"}:
                raise PipelineError(
                    "UNSUPPORTED_MEDIA_TYPE", "WebM phải dùng VP8 hoặc VP9."
                )
            for frame in container.decode(stream):
                if frame.pts is None or frame.time_base is None:
                    raise PipelineError("INVALID_TIMESTAMPS", "Frame không có PTS.")
                stamp = float(frame.pts * frame.time_base * 1000)
                if timestamps and stamp <= timestamps[-1]:
                    raise PipelineError(
                        "INVALID_TIMESTAMPS", "PTS không tăng nghiêm ngặt."
                    )
                if timestamps and stamp - timestamps[0] > 6000:
                    raise PipelineError(
                        "CLIP_TOO_LONG", "Video dài quá 6 giây theo PTS."
                    )
                if len(frames) >= 900:
                    raise PipelineError("INVALID_REQUEST", "Video có quá nhiều frame.")
                if frame.width * frame.height > 3840 * 2160:
                    raise PipelineError(
                        "INVALID_REQUEST", "Độ phân giải vượt giới hạn demo 4K."
                    )
                rgb = frame.to_ndarray(format="rgb24")
                scale = min(1.0, 640 / max(rgb.shape[:2]))
                if scale < 1:
                    rgb = cv2.resize(
                        rgb,
                        (
                            max(1, round(rgb.shape[1] * scale)),
                            max(1, round(rgb.shape[0] * scale)),
                        ),
                    )
                frames.append(rgb)
                timestamps.append(stamp)
    except PipelineError:
        raise
    except (av.error.FFmpegError, OSError, ValueError) as exc:
        raise PipelineError("CLIP_DECODE_FAILED", "Không giải mã được video.") from exc
    if not frames:
        raise PipelineError("CLIP_DECODE_FAILED", "Video không có frame đọc được.")
    if timestamps[-1] - timestamps[0] < 300:
        raise PipelineError("CLIP_TOO_SHORT", "Video ngắn hơn 0,3 giây theo PTS.")
    timestamps = np.asarray(timestamps, dtype=np.float64)
    timestamps -= timestamps[0]
    integer_ms = np.rint(timestamps).astype(np.int64)
    if len(integer_ms) > 1 and np.any(np.diff(integer_ms) <= 0):
        raise PipelineError(
            "INVALID_TIMESTAMPS", "PTS quá gần để biểu diễn bằng mili giây nguyên."
        )
    return frames, timestamps, integer_ms


class VideoDecoder:
    def decode(self, path, *, allow_mp4=False):
        return decode_video(path, allow_mp4=allow_mp4)
