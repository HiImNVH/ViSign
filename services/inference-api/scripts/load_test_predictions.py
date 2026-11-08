# services/inference-api/scripts/load_test_predictions.py - Kiem tai POST /api/v1/predictions (T065/T097).
# Cach dung: python load_test_predictions.py <base-url> <thu-muc-webm> <giay-moi-muc> <so-client,...>
# N client gui lien tuc trong D giay; in moi muc mot dong JSON: so request, 200, 503, loi khac, ky hieu/phut, p50/p95.
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def post(base: str, clip: bytes) -> tuple[int, float]:
    boundary = uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="clip"; filename="c.webm"\r\n'
        "Content-Type: video/webm\r\n\r\n"
    ).encode() + clip + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        base + "/api/v1/predictions",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response.read()
            code = response.status
    except urllib.error.HTTPError as error:
        error.read()
        code = error.code
    except OSError:
        code = 0
    return code, time.perf_counter() - start


def run_level(base: str, clips: list[bytes], clients: int, duration: float) -> dict[str, object]:
    records: list[tuple[int, float]] = []
    lock = threading.Lock()
    stop = time.perf_counter() + duration

    def worker(offset: int) -> None:
        index = offset
        while time.perf_counter() < stop:
            result = post(base, clips[index % len(clips)])
            index += 1
            with lock:
                records.append(result)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(clients)]
    started = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed = time.perf_counter() - started
    ok = [seconds for code, seconds in records if code == 200]
    busy = sum(1 for code, _ in records if code == 503)
    return {
        "clients": clients,
        "requests": len(records),
        "ok": len(ok),
        "busy503": busy,
        "other": len(records) - len(ok) - busy,
        "okPerMin": round(len(ok) / elapsed * 60, 1),
        "p50": round(statistics.median(ok), 2) if ok else None,
        "p95": round(statistics.quantiles(ok, n=20)[18], 2) if len(ok) >= 2 else None,
    }


def main() -> None:
    base = sys.argv[1].rstrip("/")
    clips = [path.read_bytes() for path in sorted(Path(sys.argv[2]).glob("*.webm"))]
    duration = float(sys.argv[3])
    for clients in (int(value) for value in sys.argv[4].split(",")):
        print(json.dumps(run_level(base, clips, clients, duration)), flush=True)
        time.sleep(3)


if __name__ == "__main__":
    main()
