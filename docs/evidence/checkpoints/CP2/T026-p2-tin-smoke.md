# CP2 T026 smoke evidence — nền FastAPI `/api/v1`

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP2` |
| Task | `T026` |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P5 Hiển` (CORS/expose header cho client T040) |
| Candidate commit | `CP2 T026(api): add FastAPI v1 foundation with request id and error mapping` |
| Commit | `4a2dad16d41b13f09a20e6ab90e91d288e838f37` — [4a2dad1](https://github.com/HiImNVH/ViSign/commit/4a2dad16d41b13f09a20e6ab90e91d288e838f37); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42359426590) |
| Ngày/giờ | `2026-11-07T16:19+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15, FastAPI 0.162.0, Starlette 1.10.0, pytest 9.2.0 |
| Status | `PASS` local và CI; chờ reviewer verify |

## 2. Phạm vi thay đổi

| File | Trách nhiệm |
|---|---|
| `src/visign_api/main.py` | `create_app()`: version từ metadata gói (`0.0.1`), lifespan tạo `InferenceCoordinator`, CORS, middleware, error handler, router |
| `src/visign_api/api/router.py` | `api_v1_router` prefix `/api/v1` (chưa có endpoint — T038/T060) |
| `src/visign_api/api/request_context.py` | Nhận UUID hợp lệ từ `X-Request-ID`, tạo UUID mới khi thiếu/sai |
| `src/visign_api/api/request_middleware.py` | Gắn request ID, echo header, một dòng access log, đổi lỗi bất ngờ thành 500 bên trong CORS |
| `src/visign_api/api/error_handlers.py` | `ViSignApiException` → `ErrorEnvelope` + `Retry-After`; `RequestValidationError` → 400 `INVALID_REQUEST`; lỗi khác → 500 `PREDICTION_FAILED`, traceback chỉ ở log |
| `src/visign_api/inference/coordinator.py` | Một slot suy luận; chờ quá `inference_wait_timeout_seconds` → `SERVICE_BUSY` |
| `pyproject.toml`/`uv.lock` | Dev: thêm `httpx2` (Starlette 1.10 `TestClient` cảnh báo `httpx` deprecated), bỏ `httpx` không còn dùng |

Khác legacy `backend` `b708c72`:

1. Legacy khai báo `version="1.0.0"`; nay lấy `importlib.metadata.version("visign-api")` = `0.0.1`.
2. Legacy để lỗi 500 đi tới `ServerErrorMiddleware` (ngoài CORS) nên response 500 cross-origin thiếu
   `Access-Control-Allow-Origin` và trình duyệt chỉ báo lỗi mạng. Nay middleware request nằm trong CORS và tự
   tạo `ErrorEnvelope` 500; test `test_cross_origin_server_error_keeps_cors_headers` khóa hành vi này.
3. Legacy `acquire_slot()`/`release_slot()` tách rời, dễ rò slot; nay là async context manager, slot luôn được trả.
4. Coordinator tạo trong lifespan để `asyncio.Semaphore` gắn với event loop đang chạy.
5. CORS chỉ `GET`/`POST`, header `X-Request-ID`/`Content-Type`, expose `X-Request-ID`/`Retry-After`, không credential.

Không thuộc phạm vi: `ROUTE_NOT_FOUND`/`METHOD_NOT_ALLOWED` và `Cache-Control: no-store` (T073), health/model-info
(T060), predictions (T038), tắt `/docs` trên production (T092/T096).

## 3. Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `e2bdf7f` trước khi sửa.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `pytest .../test_inference_coordinator.py .../test_app_foundation.py -q` trước khi có module | Fail | 2 collection errors | `PASS` |
| 2 | GREEN | Cùng command, `-W error` | Đạt | 19 passed | `PASS` |
| 3 | Bắt hồi quy CORS | Đảo thứ tự middleware về như legacy | Fail | 1 failed (`test_cross_origin_server_error_keeps_cors_headers`); khôi phục giống hệt | `PASS` |
| 4 | Toàn bộ API + contract | `pytest services/inference-api/tests tests/contract -q -W error` ×3; Ruff; format check; `python -m mypy` | Không lỗi | 129 passed ×3; Ruff/format đạt; mypy 29 files | `PASS` |
| 5 | Live HTTP | `uvicorn visign_api.main:app --port 8765`; curl | Version, request ID, CORS đúng | `info.version=0.0.1`; UUID hợp lệ được echo, `abc` bị thay bằng UUID mới; preflight Vite 200 + `access-control-allow-origin`, không credential; origin lạ 400 không header CORS; access log JSON một dòng/request | `PASS` |
| 6 | Route chưa có | `GET /api/v1/health` | Chưa chuẩn hóa | `404 {"detail":"Not Found"}` kèm `x-request-id` — chờ T060/T073 | `NOT_RUN` (ngoài phạm vi) |
| 7 | Git hygiene | `git diff --cached --check`; quét file bị cấm | Không lỗi | exit 0; không có file bị cấm/secret trong 14 path staged | `PASS` |

Ghi chú quá trình: pytest 9 tự gắn handler bắt log vào logger tắt `propagate`. Khi `visign_api.main` tạo `app` lúc
import, logger `visign_api` đã tắt propagate từ lúc collect nên `test_configure_logging_is_idempotent` đếm cả handler
của pytest. Ngoài pytest logger chỉ có một handler; test được sửa để đếm handler JSON của service.

## 5. Rủi ro và handoff

- FastAPI vẫn phục vụ `/docs` và `/openapi.json` sinh tự động; nguồn chân lý contract vẫn là `openapi.yaml`.
  T092/T096 quyết định tắt trên production.
- Hiển (T040): đọc `X-Request-ID`/`Retry-After` cross-origin được vì đã `expose_headers`.
- Rollback: `git revert` riêng commit này; domain/config/clip tạm không phụ thuộc app.

## Independent review — P1/Huy

Review time: `2026-11-07T16:38:40+07:00` trên `origin/main` `d3afdff` (chứa `4a2dad1`). Ngoài test của owner, P1 chạy `create_app()` bằng
`TestClient` với một route tạm ném `RuntimeError("secret /tmp/visign_clip_x.webm")`:

| Tình huống | Kết quả |
|---|---|
| `X-Request-ID: not-a-uuid` | 500 `PREDICTION_FAILED`, header/body cùng UUID mới; body không chứa message hay path của exception |
| Lỗi 500 với `Origin` hợp lệ | Có `Access-Control-Allow-Origin` (CORS bọc ngoài) |
| Traceback | Chỉ trong log server JSON, kèm `requestId` và `errorCode` |
| Preflight origin Vite | 200, cho phép `x-request-id` |
| Origin lạ | 400 `Disallowed CORS origin`, không gắn nhãn 403 |
| Route không tồn tại | 404 `{"detail":"Not Found"}` — đúng phạm vi, chuẩn hoá ở T073 |
| Unit + contract | 129 passed; CI run của `4a2dad1` success |

Ghi chú không chặn:

1. UUID viết hoa trong `X-Request-ID` được trả lại dạng chữ thường. Hợp lệ theo RFC 4122, nhưng FE không
   nên so chuỗi tuyệt đối; `crypto.randomUUID()` vốn sinh chữ thường nên luồng thật không bị ảnh hưởng.
2. Preflight không có `X-Request-ID` vì CORS middleware trả trước middleware request; chấp nhận được.
3. Router `/api/v1` chưa có endpoint; health/model-info thuộc T060, predictions thuộc T038.

**Reviewer result**: `P1_VERIFIED`

## Follow-up sau review P5 — CORS credential

Nguồn giá trị `allow_credentials` của CORS middleware (`Settings.cors_allow_credentials`) nay có kiểu `Literal[False]`;
chi tiết và kiểm thử tại follow-up trong `docs/evidence/checkpoints/CP2/T022-T023-p2-tin-smoke.md`.
