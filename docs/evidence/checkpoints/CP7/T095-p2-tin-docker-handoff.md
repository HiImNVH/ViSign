# CP7 T095 evidence — đóng gói Docker/Compose local, bàn giao cho P1/Huy

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP7 / T095` — phần chuẩn bị local: image `web`, `inference-api` và Compose hai container; chưa tạo tài nguyên AWS |
| Owner | `P2 Tín` soạn; bàn giao phần build/smoke Docker và các bước AWS cho `P1 Huy` theo quyết định của P2 |
| Reviewer | `P1 Huy` |
| Candidate commit | `CP5-CP7 T065,T095(cloud): record detector review and hand off Docker` |
| Commit | `02cb36a9a350d01826cea033639b3f47f1317197` — [02cb36a](https://github.com/HiImNVH/ViSign/commit/02cb36a9a350d01826cea033639b3f47f1317197); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42403346511) |
| Ngày/giờ | `2026-11-08T01:48+07:00` |
| Status | `PARTIAL` — build qua mọi bước; chưa chạy stack và smoke vì ổ C: của máy build hết chỗ |

## Phạm vi

| File | Nội dung |
|---|---|
| `infra/aws/docker/inference-api.Dockerfile` | Python 3.12.15 slim; `uv sync --locked` extra `serving`; `visign-ai` cài editable để giữ cấu trúc `ai/`; tải 3 detector MediaPipe theo `ai/configs/download-manifest.json`, sai SHA-256 thì dừng build; runtime chỉ thêm `libgl1`, `libglib2.0-0`; user 10001; uvicorn 1 worker, `--no-server-header`, `--no-access-log`; healthcheck `/api/v1/health` |
| `infra/aws/docker/web.Dockerfile` | `npm ci` + `npm run build` (typecheck như CI) trên Node 24.18.0; phục vụ bằng `nginx-unprivileged` 1.30 |
| `infra/aws/nginx/default.conf`, `security-headers.conf` | Static kèm CSP `'self'`, `Permissions-Policy: camera=(self)`; `/api/` chuyển nguyên trạng tới `inference-api:8000`; body tối đa 11 MiB (trên giới hạn 10 MiB + 64 KiB của API để API tự trả 413 envelope) |
| `infra/aws/compose.production.yml` | Root chỉ đọc, `/tmp` tmpfs, `cap_drop: ALL`, `no-new-privileges`, giới hạn RAM (API 1.536 MiB, web 128 MiB), log xoay vòng; artifact gắn chỉ đọc từ `MODEL_ARTIFACT_DIR`; `CORS_ORIGINS=[]`, docs tắt |
| `infra/aws/compose.local.yml` | Build từ mã nguồn, chỉ mở `127.0.0.1:8080` |
| `infra/aws/docker/*.dockerignore` | Context dạng allowlist: không gửi `.venv`, `node_modules`, dữ liệu, video |
| `services/inference-api/pyproject.toml`, `uv.lock` | Extra `serving` khai báo `torch==2.11.0`, nguồn index PyTorch CPU chỉ cho Linux: lock bỏ 15 gói `nvidia-*`, `cuda-*`, `triton`; Windows/macOS vẫn lấy torch từ PyPI |

## Đã kiểm

| Kiểm tra | Kết quả |
|---|---|
| `docker compose ... config` | Gộp đúng hai file; context là gốc repo; thiếu `MODEL_ARTIFACT_DIR` thì dừng với thông báo rõ |
| Image `web` | Build và unpack thành `visign/web:local` |
| Image `inference-api` | Qua đủ 11 bước builder và 5 bước runtime (gồm `uv sync --locked`, tải và kiểm SHA-256 detector); export xong, hỏng ở bước unpack vì ổ C: máy build còn 0 GB |
| Lock torch CPU | `uv sync --locked` trên Windows không đổi gói; API + contract + integration + security 417 passed, 3 skipped; pip-audit API 0 lỗ hổng chưa đánh giá |
| Base image (digest lúc build) | `python:3.12.15-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70`; `ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490`; `node:24.18.0-alpine@sha256:a0b9bf06e4e6193cf7a0f58816cc935ff8c2a908f81e6f1a95432d679c54fbfd`; `nginxinc/nginx-unprivileged:1.30-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03` |

Sự cố máy build: Docker Desktop đặt ổ đĩa ảo `docker_data.vhdx` trên C: (16,3 GB, ổ C: khoảng 116 GB). Build lần
đầu tạo khoảng 7 GB build cache và làm C: về 0 GB; đã dừng build, xóa clip tạm. Cần chuyển **Settings → Resources →
Advanced → Disk image location** sang ổ khác (máy này còn 106 GB ở D:) hoặc build trên máy còn ít nhất 15 GB trống.

## Chưa kiểm

Chưa chạy stack nên chưa có: image size, RAM đỉnh dưới giới hạn 1.536 MiB, hành vi root chỉ đọc và tmpfs khi chạy
MediaPipe/torch, healthcheck, header thật qua nginx, độ trễ clip thật trong container Linux.

## Bàn giao cho P1/Huy

1. Chuyển ổ đĩa Docker ra khỏi C: (hoặc dùng máy build khác).
2. Chạy local:
   `$env:MODEL_ARTIFACT_DIR = "<thư mục artifact>"; docker compose -f infra/aws/compose.production.yml -f infra/aws/compose.local.yml up --build -d`
3. Smoke qua `http://127.0.0.1:8080`: `/healthz` 200; `/` có CSP và `Permissions-Policy`; `/api/v1/health` 200 có
   `Content-Security-Policy: default-src 'none'...`, `no-store`, `X-Request-ID` echo, không có `server: uvicorn`;
   `/api/v1/x` 404 và `POST /api/v1/health` 405 đều là envelope; upload 10,5 MiB → 413 `CLIP_TOO_LARGE` từ API,
   12 MiB → 413 của nginx; clip thật → 200; `docker compose exec inference-api id` → uid 10001; `docker stats` lấy
   RAM đỉnh; ghi image size cho T094.
4. Hiển xem CSP/`Permissions-Policy` trong `infra/aws/nginx/security-headers.conf` với bản build thật.
5. AWS (T095): chốt tài khoản (project `Rubber Ducking` của nhóm hay tài khoản mới) và instance (≥ 2 GB RAM, x86_64
   vì image build `linux/amd64`), xác nhận phạm vi/credit theo `infra/aws/README.md`; rồi ECR, S3 artifact, EC2 +
   Elastic IP + Docker, CloudFront hai behavior; T096 cho IAM, SSM, CloudWatch, Budget, HSTS.

**Reviewer result**: `PENDING`

## Independent review — P1/Huy (local Docker, 2026-11-08)

Máy: Windows 11 + Docker Desktop 29.9.2 (engine Linux x86_64, 12 CPU, ~12 GB RAM). Build và chạy đúng lệnh bàn giao
(`compose.production.yml` + `compose.local.yml`), qua nginx `127.0.0.1:8080`.

| Kiểm | Kết quả | Trạng thái |
|---|---|---|
| Build lần đầu (cả hai image) | 9 phút 51 giây; `inference-api` 2,86 GB, `web` 90,5 MB | PASS |
| Smoke artifact fixture (14 mục bàn giao) | `/healthz` 200; `/` có CSP `default-src 'self'` + `Permissions-Policy camera=(self)`; API có CSP `default-src 'none'`, `no-store`, echo `X-Request-ID`, `Server: nginx` (không lộ uvicorn/phiên bản); 404/405 là envelope; 10,5 MiB → 413 `CLIP_TOO_LARGE` từ API; 12 MiB → 413 của nginx; clip WebM → 200 | PASS |
| Hardening | `id` = uid 10001; `ReadonlyRootfs=true`; `CapDrop=[ALL]`; giới hạn 1,5 GiB; healthcheck `healthy`; `/tmp` tmpfs ghi được | PASS |
| Luồng GRU thật (artifact pilot tổng hợp `pilot-gru-test-v1`, MediaPipe thật) | **Lỗi:** mọi `POST /predictions` trả 500 `PREDICTION_FAILED`; log: `OSError: libEGL.so.1: cannot open shared object file` khi MediaPipe Tasks nạp thư viện C | **FAIL → đã sửa** |
| Sau bản vá Dockerfile (thêm `libegl1 libgles2` ở stage runtime) | Rebuild 2 phút 46 giây; clip không có người → 422 `NO_PERSON_DETECTED` đúng contract, 0,94–2,23 s/clip qua nginx | PASS |
| Bộ detector tạo sẵn của `a214a3c` trong container | RAM nghỉ 447,5 MiB; 6 clip liên tiếp 0,94–1,25 s; **RAM đỉnh 962 MiB** (< 1.536 MiB); không có cảnh báo detector | PASS |

Bản vá `infra/aws/docker/inference-api.Dockerfile` do P1 viết nên **P2/Tín cần review** (không tự xác nhận). CI hiện
không build image, nên lỗi này chỉ lộ khi chạy MediaPipe thật trong container; đề xuất thêm job build + smoke
`/predictions` cho Docker (T091/T095).

Chưa kiểm: clip có người thật trong container (chỉ dùng clip không có người, không dùng video mặt người khác), CSP với
trình duyệt thật (Hiển), toàn bộ phần AWS. Việc AWS cần lead quyết: tài khoản, instance ≥ 2 GB RAM x86_64 (đề xuất
≥ 2 GB vì API đỉnh ~1 GB + web ~12 MB + hệ điều hành), hạn mức chi phí; quyết định rate limit 429.

**Reviewer result**: `P1_PARTIAL` — Docker local đạt sau bản vá libEGL; T095 giữ `[ ]` chờ Tín review bản vá và deploy AWS.

## Cập nhật AWS — P1/Huy (2026-11-08)

Đã deploy origin EC2 bằng CloudFormation (`visign-storage`, `visign-origin`), image `3b29d4a2cec1` từ ECR và artifact
fixture từ S3; smoke 14/14 qua `http://52.65.207.133`. CloudFront bị AWS chặn (tài khoản cần xác minh qua Support).
Chi tiết: [deployment-report.md](../../../deployment-report.md). T095 giữ `[ ]` chờ CloudFront HTTPS và Tín review.

## Review bản vá libEGL — P2/Tín

Review `2026-11-08` trên `fe17fad` (bản vá ở `f9232cd`). Đọc ELF trong wheel
`mediapipe-1.1.1-py3-none-manylinux_2_28_x86_64.whl`: `mediapipe/tasks/c/libmediapipe.so` bắt buộc nạp `libEGL.so.1`,
`libGLESv2.so.2` và các thư viện glibc (`libm`, `libpthread`, `libdl`, `librt`, `libc`). Image
`python:3.12.15-slim-bookworm` chỉ có glibc; `libegl1` và `libgles2` cung cấp đúng hai thư viện còn thiếu, nên bản vá
vừa cần vừa đủ cho phần phụ thuộc trực tiếp. Khớp smoke runtime của P1 sau bản vá (MediaPipe chạy, 422
`NO_PERSON_DETECTED`, bộ detector tạo sẵn hoạt động).

Không build lại image trên máy P2 vì Docker Desktop không khởi động được (ổ C: còn khoảng 5 GB). Đồng ý thêm job CI
build image và smoke `/predictions` để lỗi thiếu thư viện hệ thống lộ sớm.

**Reviewer result**: `P2_VERIFIED` bản vá `libegl1 libgles2`.
