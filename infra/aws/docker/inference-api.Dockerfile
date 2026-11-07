# infra/aws/docker/inference-api.Dockerfile
# Image inference-api (T095): dependency tu services/inference-api/uv.lock (extra serving, torch CPU tren Linux),
# detector MediaPipe tai theo ai/configs/download-manifest.json va kiem SHA-256, chay uvicorn mot worker bang user
# khong phai root. Build tu goc repo: docker build -f infra/aws/docker/inference-api.Dockerfile .
ARG PYTHON_IMAGE=python:3.12.15-slim-bookworm
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.13.7

FROM ${UV_IMAGE} AS uv

FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Metadata truoc: layer dependency (torch, MediaPipe) duoc giu trong cache khi chi doi ma nguon
COPY ai/pyproject.toml ai/
COPY services/inference-api/pyproject.toml services/inference-api/uv.lock services/inference-api/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra serving --no-install-project --no-install-package visign-ai \
        --project services/inference-api
# visign-ai cai editable: pipeline tim configs/ va models/ theo cau truc thu muc ai/
COPY ai/src ai/src
COPY ai/configs ai/configs
COPY services/inference-api/src services/inference-api/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra serving --project services/inference-api
# Detector MediaPipe: URL va SHA-256 lay tu manifest da review; sai hash thi build dung
RUN python - <<'EOF'
import hashlib
import json
import pathlib
import urllib.request

manifest = json.loads(pathlib.Path("ai/configs/download-manifest.json").read_text("utf-8-sig"))
model_dir = pathlib.Path("ai/models")
model_dir.mkdir(exist_ok=True)
for item in manifest:
    with urllib.request.urlopen(item["url"], timeout=120) as response:
        content = response.read()
    if hashlib.sha256(content).hexdigest() != item["sha256"].lower():
        raise SystemExit(f"SHA-256 khong khop: {item['name']}")
    (model_dir / item["name"]).write_bytes(content)
EOF

FROM ${PYTHON_IMAGE} AS runtime
# libGL/glib cho opencv-contrib-python; libEGL/GLES cho thu vien C cua MediaPipe Tasks
# (thieu libEGL.so.1 -> moi POST /predictions tra 500 PREDICTION_FAILED, P1 smoke 2026-11-08)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libegl1 libgles2 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin visign
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    VISIGN_MODEL_DIR=/app/ai/models
WORKDIR /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4)"]
# Mot worker = mot slot suy luan; tat header server va access log rieng (middleware da ghi log theo allowlist)
CMD ["uvicorn", "visign_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-server-header", "--no-access-log"]
