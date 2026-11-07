"""Smoke HTTP cho stack Docker/AWS cua ViSign (T091/T095), chi dung thu vien chuan.

Cach dung: python infra/aws/smoke/stack_smoke.py <base-url> <clip.webm> [--expect-kind fixture|pilot|full]
Vi du CI: python infra/aws/smoke/stack_smoke.py http://127.0.0.1:8080 /tmp/smoke.webm --expect-kind fixture
Thoat khac 0 neu co muc FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid

REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"


def call(base: str, method: str, path: str, body: bytes | None = None,
         headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(base + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read()


def multipart(data: bytes, content_type: str = "video/webm") -> tuple[bytes, dict[str, str]]:
    boundary = f"visign-{uuid.uuid4().hex}"
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"clip.webm\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n").encode()
    return head + data + f"\r\n--{boundary}--\r\n".encode(), {
        "Content-Type": f"multipart/form-data; boundary={boundary}"}


def code_of(body: bytes) -> str | None:
    try:
        value = json.loads(body)
    except ValueError:
        return None
    return value.get("code") if isinstance(value, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("clip")
    parser.add_argument("--expect-kind", choices=["fixture", "pilot", "full"])
    args = parser.parse_args()
    base = args.base.rstrip("/")
    results: list[bool] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}".rstrip(), flush=True)

    status, _, body = call(base, "GET", "/healthz")
    check("/healthz 200", status == 200)

    status, headers, _ = call(base, "GET", "/")
    check("/ CSP self + camera Permissions-Policy", status == 200
          and "default-src 'self'" in headers.get("content-security-policy", "")
          and "camera=(self)" in headers.get("permissions-policy", ""))
    check("/ khong lo phien ban server", "/" not in headers.get("server", ""), headers.get("server", ""))

    status, headers, body = call(base, "GET", "/api/v1/health", headers={"X-Request-ID": REQUEST_ID})
    health = json.loads(body) if status == 200 else {}
    check("/api/v1/health modelReady", status == 200 and health.get("modelReady") is True, body.decode()[:120])
    check("API CSP default-src 'none'", headers.get("content-security-policy", "").startswith("default-src 'none'"))
    check("API Cache-Control no-store", headers.get("cache-control") == "no-store")
    check("X-Request-ID duoc tra lai", headers.get("x-request-id") == REQUEST_ID)
    check("khong lo uvicorn", "uvicorn" not in headers.get("server", "").lower())

    status, _, body = call(base, "GET", "/api/v1/x")
    check("route la -> 404 ROUTE_NOT_FOUND", status == 404 and code_of(body) == "ROUTE_NOT_FOUND")
    status, _, body = call(base, "POST", "/api/v1/health")
    check("sai method -> 405 METHOD_NOT_ALLOWED", status == 405 and code_of(body) == "METHOD_NOT_ALLOWED")

    status, _, body = call(base, "GET", "/api/v1/model-info")
    kind = json.loads(body).get("artifactKind") if status == 200 else None
    check("model-info 200", status == 200 and (args.expect_kind is None or kind == args.expect_kind), str(kind))

    payload, form = multipart(b"\x1aE\xdf\xa3" + b"\0" * int(10.5 * 1024 * 1024))
    status, _, body = call(base, "POST", "/api/v1/predictions", payload, form)
    check("10,5 MiB -> 413 CLIP_TOO_LARGE (API)", status == 413 and code_of(body) == "CLIP_TOO_LARGE")
    payload, form = multipart(b"\0" * (12 * 1024 * 1024))
    status, _, body = call(base, "POST", "/api/v1/predictions", payload, form)
    check("12 MiB -> 413 cua nginx", status == 413 and code_of(body) != "CLIP_TOO_LARGE")

    with open(args.clip, "rb") as handle:
        payload, form = multipart(handle.read(), "video/webm;codecs=vp8")
    status, _, body = call(base, "POST", "/api/v1/predictions", payload, form)
    # Clip khong co nguoi: fixture tra 200, model that tra 422 on dinh; 500 nghia la loi moi truong
    ok = (status == 200 and json.loads(body).get("requestId")) or (
        status == 422 and code_of(body) in {"NO_PERSON_DETECTED", "INSUFFICIENT_LANDMARKS"})
    check("du doan clip -> 200 hoac 422 on dinh (khong 5xx)", bool(ok), f"{status} {code_of(body) or ''}")

    print(f"{sum(results)}/{len(results)} PASS")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
