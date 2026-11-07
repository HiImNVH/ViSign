# ai/src/visign_ai/evaluation/benchmark_inference.py
"""Measure sequential ViSign prediction requests against a running HTTP API."""

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from statistics import median, quantiles
from time import perf_counter
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from visign_ai.cli import make_console_output_safe

STAGES = ("decode", "extract", "infer")


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "p50": round(median(values), 2),
        "p95": round(quantiles(values, n=100, method="inclusive")[94], 2)
        if len(values) > 1
        else round(values[0], 2),
        "max": round(max(values), 2),
    }


def process_snapshot(pid: int) -> tuple[float, int]:
    """Return total CPU seconds and the worker's lifetime peak RSS in bytes."""
    if sys.platform == "win32":
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    f"$p=Get-Process -Id {pid} -ErrorAction Stop; "
                    "ConvertTo-Json -Compress -InputObject @($p.TotalProcessorTime.TotalSeconds,"
                    "$p.PeakWorkingSet64)"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cpu, peak = json.loads(result.stdout)
        return float(cpu), int(peak)
    if sys.platform.startswith("linux"):
        root = Path(f"/proc/{pid}")
        fields = (root / "stat").read_text().rsplit(")", 1)[1].split()
        seconds = (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
        high_water = next(
            line
            for line in (root / "status").read_text().splitlines()
            if line.startswith("VmHWM:")
        )
        return seconds, int(high_water.split()[1]) * 1024
    raise ValueError("--server-pid is supported on Windows and Linux")


def predict(base: str, data: bytes, timeout: float) -> tuple[dict[str, Any], float]:
    boundary = uuid4().hex
    header = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="clip"; '
        'filename="benchmark.webm"\r\nContent-Type: video/webm\r\n\r\n'
    ).encode("ascii")
    request = Request(
        f"{base.rstrip('/')}/api/v1/predictions",
        header + data + f"\r\n--{boundary}--\r\n".encode("ascii"),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    started = perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read())
            request_id = response.headers.get("X-Request-ID")
    except HTTPError as error:
        with error:
            try:
                payload = json.loads(error.read())
            except ValueError:
                payload = None
        raise ValueError(
            f"Prediction failed: HTTP {error.code} ({payload.get('code', 'unknown') if isinstance(payload, dict) else 'unknown'})"
        ) from error
    wall_ms = (perf_counter() - started) * 1000
    if not request_id or result["requestId"] != request_id:
        raise ValueError("Response request ID does not match its header")
    return result, wall_ms


def benchmark(args: argparse.Namespace) -> dict[str, Any]:
    if args.repeats < 1 or args.warmup < 0 or args.timeout <= 0:
        raise ValueError("Require positive repeats/timeout and nonnegative warmup")
    if args.server_pid is not None and args.server_pid < 1:
        raise ValueError("Server PID must be positive")
    clips = [path.read_bytes() for path in args.clips]
    for index in range(args.warmup):
        predict(args.base_url, clips[index % len(clips)], args.timeout)

    samples = []
    resources = []
    model_versions = set()
    for _ in range(args.repeats):
        for index, clip in enumerate(clips, 1):
            if args.server_pid is not None:
                cpu_before, _ = process_snapshot(args.server_pid)
                started = perf_counter()
            response, wall_ms = predict(args.base_url, clip, args.timeout)
            if args.server_pid is not None:
                cpu_after, peak_bytes = process_snapshot(args.server_pid)
                interval = perf_counter() - started
                resources.append(
                    ((cpu_after - cpu_before) / interval * 100, peak_bytes)
                )
            model_versions.add(response["modelVersion"])
            samples.append(
                {
                    "clipIndex": index,
                    "requestMs": wall_ms,
                    "processingTimeMs": response["processingTimeMs"],
                    "timingsMs": {
                        stage: response["timingsMs"][stage] for stage in STAGES
                    },
                    "accepted": response["accepted"],
                }
            )

    if len(model_versions) != 1:
        raise ValueError("Model version changed during benchmark")
    request_ms = [sample["requestMs"] for sample in samples]
    return {
        "modelVersion": model_versions.pop(),
        "clientPlatform": platform.platform(),
        "clipCount": len(clips),
        "warmupCount": args.warmup,
        "requestCount": len(samples),
        "acceptedCount": sum(sample["accepted"] is True for sample in samples),
        "requestMs": summarize(request_ms),
        "processingTimeMs": summarize(
            [sample["processingTimeMs"] for sample in samples]
        ),
        "timingsMs": {
            stage: summarize([sample["timingsMs"][stage] for sample in samples])
            for stage in STAGES
        },
        "sequentialRequestsPerSecond": round(1000 * len(samples) / sum(request_ms), 3),
        "workerResources": {
            "peakRequestWindowCpuPercent": round(max(cpu for cpu, _ in resources), 1),
            "peakWorkingSetMiB": round(max(rss for _, rss in resources) / 2**20, 1),
        }
        if resources
        else None,
        "samples": samples,
    }


def main() -> int:
    make_console_output_safe()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--clips", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--server-pid", type=int, help="Worker PID on the same host")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise FileExistsError(args.output)
        report = benchmark(args)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        print(f"T065: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {report['requestCount']} requests to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
