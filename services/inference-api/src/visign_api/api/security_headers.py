# services/inference-api/src/visign_api/api/security_headers.py
# Security header cho moi response cua API (T092, FR-027): chong sniff MIME, nhung khung, ro ri Referer va
# cache ket qua nhan dien; chi trang HTML docs dang bat (dev) duoc mien CSP vi can tai script.
from collections.abc import Collection

from fastapi import FastAPI
from starlette.datastructures import MutableHeaders

BASE_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}
# API chi tra JSON: khong can tai bat ky nguon nao, khong cho trang khac nhung vao
STRICT_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'"
NO_STORE = "no-store"


def served_documentation_pages(service_app: FastAPI) -> frozenset[str]:
    # Doc tu cau hinh FastAPI: docs tat (mac dinh) thi tap rong, nen 404 cua /docs va /redoc van nhan du header
    if not service_app.openapi_url:
        return frozenset()
    candidate_pages = [service_app.redoc_url]
    if service_app.docs_url:
        candidate_pages += [
            service_app.docs_url,
            service_app.swagger_ui_oauth2_redirect_url,
        ]
    return frozenset(page for page in candidate_pages if page)


def apply_security_headers(
    response_headers: MutableHeaders,
    request_path: str,
    documentation_pages: Collection[str],
) -> None:
    for header_name, header_value in BASE_SECURITY_HEADERS.items():
        response_headers.setdefault(header_name, header_value)
    if request_path in documentation_pages:
        return
    response_headers.setdefault(
        "Content-Security-Policy", STRICT_CONTENT_SECURITY_POLICY
    )
    # Giu Cache-Control rieng neu route da dat (health), mac dinh khong luu ket qua
    response_headers.setdefault("Cache-Control", NO_STORE)
