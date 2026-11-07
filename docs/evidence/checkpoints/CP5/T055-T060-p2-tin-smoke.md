# CP5 T055/T060 smoke evidence — health và model-info

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP5 / T055, T060` (P1 giao "tiếp T038/T060 endpoint để mở E2E" trong `implementation-status.md`) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P5 Hiển` (consumer T040); `P3 Cường` (metadata pilot/full) |
| Candidate commit | `CP5 T055,T060(api): add health and model-info endpoints` |
| Commit | `fb94e467d3cb408b2eac3d003bf4d3e4f977f007` — [fb94e46](https://github.com/HiImNVH/ViSign/commit/fb94e467d3cb408b2eac3d003bf4d3e4f977f007); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42375491322) |
| Ngày/giờ | `2026-11-07T20:01+07:00` |
| Status | `PASS` local và CI; chờ reviewer verify |

## Phạm vi

| File | Nội dung |
|---|---|
| `domain/health.py` | `HealthResponse {status: ok\|degraded, modelReady, modelVersion?: string\|null}` |
| `api/system.py` | `GET /api/v1/health` (`Cache-Control: no-store`; `ok` khi có predictor, `degraded` khi không); `GET /api/v1/model-info` (`ModelInfo` của artifact đang phục vụ; chưa có → 503 `MODEL_NOT_READY`, `Retry-After: 5`) |
| `main.py` | `create_app(settings, predictor_factories)`; lifespan tạo `PredictorRegistry` và nạp `MODEL_ARTIFACT_PATH` với `FEATURE_SCHEMA_VERSION`; không cấu hình hoặc nạp lỗi → `degraded` + log `ERROR`, **không lùi về fixture**; `predictor_factories` là điểm gắn adapter GRU pilot/full khi có T036 |
| `api/router.py` | Gắn `system_router` vào `/api/v1` |
| `tests/contract/test_api_contract_drift.py` | So thêm `HealthResponse` Python ↔ OpenAPI ↔ TS và enum `status`; phân biệt field optional bị bỏ khi vắng (`timingsMs`, `qualityHints`) với optional nullable (`modelVersion`) |
| `tests/contract/test_model_info_contract.py` (service) | 9 contract test T055 |

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 5 failed, 4 errors (endpoint/`create_app` chưa có) |
| GREEN T055 | 9 passed: fixture ok/no-store/request ID; degraded khi không có artifact; model-info đủ 11 field, metric null cho fixture; 503 + `Retry-After: 5`; artifact hỏng và lệch schema → degraded; pilot luôn `demoReady=false`; full đạt gate → `true`, `macroF1=0,79` → `false` |
| Drift | 16 passed; đổi `HealthResponse.modelVersion` thành không nullable → 1 failed, khôi phục giống hệt |
| Toàn bộ API + contract | 196 passed, 1 skipped ×3 `-W error`; Ruff, format, mypy (43 files) |
| Live uvicorn | `MODEL_ARTIFACT_PATH=…/fixture`: health 200 `{"status":"ok","modelReady":true,"modelVersion":"vsl-fixture-v0.0.1"}`, `cache-control: no-store`, có `x-request-id`; model-info đúng fixture. Không artifact: health `degraded`, model-info 503 `MODEL_NOT_READY`, `retry-after: 5` |

## Ghi chú

- `LOW` `MODEL_ARTIFACT_PATH=` (chuỗi rỗng) được pydantic hiểu thành `.` nên đi qua nhánh "nạp lỗi" (log `ERROR`) thay vì
  "chưa cấu hình"; kết quả vẫn `degraded`. Xử lý cùng cấu hình deploy (T095), ví dụ `env_ignore_empty=True`.
- Fixture artifact để phát triển/E2E: `MODEL_ARTIFACT_PATH=services/inference-api/tests/fixtures/model-artifacts/fixture`.

## Independent review — P1/Huy

Huy (P1) review endpoint của P2 và kết luận **đạt**; ghi nhận `2026-11-07T21:18:08+07:00` trên `219e10d`. Gate tái chạy: API + contract 211 passed, 1 skipped; CI `quality.yml` xanh.

**Reviewer result**: `P1_VERIFIED` → T055, T060 `[X]`.
