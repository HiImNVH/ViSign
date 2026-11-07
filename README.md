# ViSign source of truth

Repository chính thức: `https://github.com/HiImNVH/ViSign`.

`main` là nguồn sự thật cho yêu cầu, kế hoạch, contract, task và source code. Nhóm không dùng nhánh
vai trò dài hạn; mỗi thành viên làm trong clone cục bộ, ghi evidence tại `members/<person>/` và push
theo integration queue/checkpoint nhỏ.

## Start here

- Feature spec: `specs/001-vsl-recognition-mvp/spec.md`
- Technical plan: `specs/001-vsl-recognition-mvp/plan.md`
- Authoritative backlog: `specs/001-vsl-recognition-mvp/tasks.md`
- Rubric mapping: `docs/team/judging-criteria-mapping.md`
- Commit/push checkpoints: `docs/team/git-checkpoints.md`
- Team status: `docs/team/implementation-status.md`
- Member work logs: `members/README.md`

## Spec Kit

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-vsl-recognition-mvp'
```

## Integration rule

Mỗi checkpoint chỉ được push khi Huy mở integration window, owner pull/rebase `origin/main`, chạy
quality gate, cập nhật member evidence, commit nhỏ, pull/rebase lần cuối, rerun gate ảnh hưởng và push
thường. Cấm force-push, raw video/model/secret và full-code dump.

Chi tiết CP0–CP8 nằm trong `docs/team/git-checkpoints.md`.

## Conventions

- Dữ liệu (T098): `docs/team/data-convention.md` — lead đã bàn giao, P4 còn đóng băng manifest/validator.
- API FE–BE (T099): `docs/contracts/api-conventions.md` — đã đóng băng, có drift test trong CI.

## Cấu trúc module

```text
apps/web/                 React + TypeScript + Vite: camera, kết quả, lỗi tiếng Việt, bản dịch/lịch sử 24 giờ
services/inference-api/   FastAPI /api/v1: health, model-info, predictions; registry fixture/pilot/full
ai/                       Pipeline dùng chung: decode WebM → MediaPipe → tensor 32×234 → GRU; train/eval/gate
data/                     README dữ liệu và manifest (raw video luôn nằm ngoài Git)
tests/                    contract, integration, security xuyên module
infra/aws/                Kế hoạch triển khai AWS (chưa có workload production)
docs/                     model card, báo cáo hiệu năng/chi phí/bảo mật/an toàn AI, evidence checkpoint
specs/001-vsl-recognition-mvp/  spec, plan, data-model, contracts, tasks (nguồn sự thật)
```

Train và API gọi **cùng** `visign_ai.landmarks.pipeline` để tránh lệch tiền xử lý (parity offline ↔ API được test).

## Cài đặt

Yêu cầu: Python 3.12 qua [`uv`](https://docs.astral.sh/uv/), Node.js `^22.22.2 || ^24.15.0 || >=26` và npm.

```powershell
uv sync --locked --project services/inference-api            # API (fixture)
uv sync --locked --project services/inference-api --extra serving  # API chạy GRU + MediaPipe thật
uv sync --locked --project ai                                  # train/eval
uv run --project ai python ai/setup_models.py                  # tải detector MediaPipe đã ghim SHA-256
npm ci --prefix apps/web
```

## Chạy local

```powershell
# API với fixture (luôn trả kết quả cố định, chỉ để kiểm tích hợp)
$env:MODEL_ARTIFACT_PATH = (Resolve-Path services/inference-api/tests/fixtures/model-artifacts/fixture).Path
uv run --project services/inference-api uvicorn visign_api.main:app --host 127.0.0.1 --port 8000

# Web (proxy /api sang 127.0.0.1:8000)
npm --prefix apps/web run dev
```

Mở URL Vite in ra (mặc định `http://127.0.0.1:5173`). Thiếu `MODEL_ARTIFACT_PATH` hoặc artifact hỏng →
`/api/v1/health` báo `degraded`, dự đoán trả 503 `MODEL_NOT_READY`; API **không** tự lùi về fixture.

Cấu hình thường dùng (biến môi trường): `MODEL_ARTIFACT_PATH`, `VISIGN_MODEL_DIR` (thư mục detector),
`CORS_ORIGINS` (danh sách origin, cấm `*` và credential), `API_DOCS_ENABLED` (mặc định tắt).

## Train, đánh giá và phát hành model

Cần manifest đã audit (T013/T076–T077) và feature schema `APPROVED`; schema v0.3 đã được lead duyệt (`APPROVED`, 2026-11-08).

1. Trích landmark: `python -m visign_ai.landmarks.extract_manifest` (T017).
2. Train: `python -m visign_ai.training.train` với `ai/configs/pilot-gru.yaml` hoặc `p0-gru.yaml` (T036).
3. Đánh giá tập test: `python -m visign_ai.evaluation.evaluate` (T058).
4. Ghi metric và cổng phát hành: `python -m visign_ai.evaluation.release_gate` (T059).
   `demoReady=true` chỉ khi model full đủ 10 nghĩa P0 đạt Macro-F1 ≥ 0,80, recall từng nghĩa ≥ 0,65 trên
   split theo video gốc (FR-015) **và** lead thêm `--approve-demo`.

Chạy mỗi lệnh qua `uv run --locked --project ai ...`; `--help` liệt kê đối số.

## Đổi artifact và rollback

Artifact là một thư mục bất biến (`model.pt`, `feature_schema.json`, `model_info.json`, báo cáo train/eval).
Đổi model: đặt `MODEL_ARTIFACT_PATH` sang thư mục mới rồi **khởi động lại** API, kiểm `/api/v1/health` và
`/api/v1/model-info` (`artifactKind`, `modelVersion`, `demoReady`). Rollback: trỏ lại thư mục cũ đã
smoke-test và khởi động lại. Kịch bản fixture → pilot → full → fixture được test tại
`tests/integration/test_prediction_pipeline.py`.

## Kiểm thử và CI

`.github/workflows/quality.yml` chạy trên mọi push/PR: Ruff, mypy, pytest (API + contract, AI), lint,
typecheck, Vitest, build web, `npm audit` production và hygiene (chặn video/model/secret/file nén).
Audit bảo mật đầy đủ: `python scripts/security_audit.py` (`docs/security-report.md`).

## Cloud

Kế hoạch AWS (`ap-southeast-2`, EC2 + CloudFront + ECR + S3, deploy bằng GitHub OIDC) nằm tại
`infra/aws/` và `specs/001-vsl-recognition-mvp/contracts/deployment.md`. Hiện **chưa có URL production**:
OIDC bị AWS Free Plan chặn (evidence T096); tạo tài nguyên cần lead duyệt phạm vi/chi phí.

## Giới hạn MVP

- Nhận diện **một ký hiệu mỗi lần**; bản dịch trực tiếp chỉ ghép các kết quả được chấp nhận, không dịch câu.
- 10 nghĩa P0: Giấy tờ, Đau bụng, Sốt, Nhận, Bạn, Cảm ơn, Giúp đỡ, Xin lỗi, Đau đầu, Không.
- Chưa có model VSL thật: fixture/pilot luôn `demoReady=false`; split theo video gốc không chứng minh
  nhận diện người ký mới.
- Latency local hiện chưa đạt mục tiêu p95 ≤ 3 s (`docs/performance-report.md`).
- Không lưu video; lịch sử bản dịch chỉ nằm trên trình duyệt 24 giờ. Không thay thế phiên dịch viên.
