# services/inference-api/scripts/benchmark_serving_memory.py
# Do RAM dinh va do tre cua duong dac trung phuc vu (T037) de chon instance AWS (T095).
# Chay: uv run --project services/inference-api --extra serving python
#       services/inference-api/scripts/benchmark_serving_memory.py --runs 2
import argparse
import importlib
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

MEGABYTE = 1024 * 1024
KIBIBYTE = 1024
MILLISECONDS_PER_SECOND = 1000
GRADIENT_STEP_PER_FRAME = 4
DEFAULT_RUNS = 2


@dataclass(frozen=True)
class ClipSpec:
    name: str
    codec: str
    width: int
    height: int
    framesPerSecond: int
    durationMs: int


# Gan muc toi da contract cho phep (6000 ms) voi do phan giai/frame rate camera pho bien
CLIP_SPECS = (
    ClipSpec("vp8-640x480-30fps-5.9s", "libvpx", 640, 480, 30, 5900),
    ClipSpec("vp9-640x480-30fps-5.9s", "libvpx-vp9", 640, 480, 30, 5900),
    ClipSpec("vp8-1280x720-30fps-5.9s", "libvpx", 1280, 720, 30, 5900),
    ClipSpec("vp8-640x480-60fps-5.9s", "libvpx", 640, 480, 60, 5900),
)


def peak_resident_megabytes() -> float:
    if sys.platform == "win32":
        return windows_peak_working_set_bytes() / MEGABYTE
    import resource

    # Linux tra ru_maxrss theo KiB; EC2 dich chay Linux
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * KIBIBYTE / MEGABYTE


def windows_peak_working_set_bytes() -> int:
    import ctypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    from ctypes import wintypes

    # Khai bao kieu ro rang: HANDLE 64-bit bi cat ve int 32-bit thi API that bai va tra toan so 0
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = wintypes.HANDLE
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    get_process_memory_info.restype = wintypes.BOOL
    memory_counters = ProcessMemoryCounters()
    memory_counters.cb = ctypes.sizeof(memory_counters)
    if not get_process_memory_info(
        get_current_process(), ctypes.byref(memory_counters), memory_counters.cb
    ):
        raise OSError("[ERROR] GetProcessMemoryInfo that bai, khong do duoc RAM dinh")
    return int(memory_counters.PeakWorkingSetSize)


def moving_gradient(clip_spec: ClipSpec, frame_index: int) -> Any:
    import numpy as np

    # Noi dung nen duoc (khong phai nhieu) de clip 6 s van duoi gioi han 10 MiB nhu camera that
    columns: Any = np.arange(clip_spec.width, dtype=np.uint32)
    rows: Any = np.arange(clip_spec.height, dtype=np.uint32)
    shifted = (
        columns[None, :] + rows[:, None] + frame_index * GRADIENT_STEP_PER_FRAME
    ) % 256
    return np.repeat(shifted.astype(np.uint8)[:, :, None], 3, axis=2)


def write_synthetic_clip(clip_spec: ClipSpec, output_dir: Path) -> Path:
    import av

    clip_path = output_dir / f"{clip_spec.name}.webm"
    frame_count = (
        clip_spec.framesPerSecond * clip_spec.durationMs // MILLISECONDS_PER_SECOND + 1
    )
    with av.open(str(clip_path), "w", format="webm") as container:
        stream = container.add_stream(clip_spec.codec, rate=clip_spec.framesPerSecond)
        stream.width, stream.height, stream.pix_fmt = (
            clip_spec.width,
            clip_spec.height,
            "yuv420p",
        )
        stream.codec_context.time_base = Fraction(1, MILLISECONDS_PER_SECOND)
        for frame_index in range(frame_count):
            video_frame = av.VideoFrame.from_ndarray(
                moving_gradient(clip_spec, frame_index), format="rgb24"
            )
            video_frame.pts = round(
                frame_index * MILLISECONDS_PER_SECOND / clip_spec.framesPerSecond
            )
            video_frame.time_base = Fraction(1, MILLISECONDS_PER_SECOND)
            for packet in stream.encode(video_frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return clip_path


def time_one_extraction(feature_extractor: Any, clip_bytes: bytes) -> dict[str, Any]:
    from visign_api.inference.temporary_clip import open_temporary_clip

    started_at = time.perf_counter()
    with open_temporary_clip(clip_bytes) as uploaded_clip:
        extracted = feature_extractor.extract(uploaded_clip.path)
    return {
        "wallMs": round((time.perf_counter() - started_at) * MILLISECONDS_PER_SECOND),
        "decodeMs": extracted.decodeMs,
        "extractMs": extracted.extractMs,
        "peakMb": round(peak_resident_megabytes(), 1),
        "decodedFrames": extracted.qualityHints.frameCount,
    }


def measure_clip(clip_path: Path, runs: int) -> dict[str, Any]:
    # Thu tu import giong tien trinh phuc vu: app FastAPI, pipeline dac trung, roi torch cho GRU
    importlib.import_module("visign_api.main")
    api_imported_mb = round(peak_resident_megabytes(), 1)
    from visign_api.inference.feature_extraction import (
        FeatureExtractor,
        FeatureSource,
        build_visign_ai_binding,
    )

    feature_extractor = FeatureExtractor(build_visign_ai_binding(), FeatureSource())
    pipeline_imported_mb = round(peak_resident_megabytes(), 1)
    importlib.import_module("torch")
    torch_imported_mb = round(peak_resident_megabytes(), 1)
    clip_bytes = clip_path.read_bytes()
    return {
        "apiImportedMb": api_imported_mb,
        "pipelineImportedMb": pipeline_imported_mb,
        "torchImportedMb": torch_imported_mb,
        "runs": [
            time_one_extraction(feature_extractor, clip_bytes) for _ in range(runs)
        ],
    }


def measure_in_fresh_process(clip_path: Path, runs: int) -> dict[str, Any]:
    # Moi clip mot tien trinh moi de RAM dinh khong bi clip truoc lam sai lech
    completed = subprocess.run(
        [sys.executable, __file__, "--measure", str(clip_path), "--runs", str(runs)],
        capture_output=True,
        text=True,
        check=True,
    )
    measured: dict[str, Any] = json.loads(completed.stdout.strip().splitlines()[-1])
    return measured


def run_benchmark(runs: int) -> list[dict[str, Any]]:
    benchmark_rows: list[dict[str, Any]] = []
    # Clip tong hop chi nam trong thu muc tam va bi xoa khi ket thuc
    with tempfile.TemporaryDirectory(prefix="visign_bench_") as clip_directory:
        for clip_spec in CLIP_SPECS:
            clip_path = write_synthetic_clip(clip_spec, Path(clip_directory))
            benchmark_rows.append(
                {
                    **asdict(clip_spec),
                    "sizeBytes": clip_path.stat().st_size,
                    **measure_in_fresh_process(clip_path, runs),
                }
            )
    return benchmark_rows


def main() -> None:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "--measure", type=Path, help="Do mot clip trong tien trinh hien tai"
    )
    argument_parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    arguments = argument_parser.parse_args()
    if arguments.measure:
        print(json.dumps(measure_clip(arguments.measure, arguments.runs)))
        return
    print(
        json.dumps(
            {"platform": sys.platform, "results": run_benchmark(arguments.runs)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
