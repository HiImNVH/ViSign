# CP4 T072/T073 smoke evidence — 404/405/307 theo contract HTTP

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T072` (contract test định tuyến); `T073` (catalog, handler, OpenAPI) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P5 Hiển` (hai mã lỗi mới phía FE, D3) |
| Candidate commit | `CP4 T072,T073(api): add 404/405 error envelopes and routing contract` |
| Commit | `d72ab3259547022decdebb1b1382f8ea7f0cce33` — [d72ab32](https://github.com/HiImNVH/ViSign/commit/d72ab3259547022decdebb1b1382f8ea7f0cce33); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42388018420) |
| Ngày/giờ | `2026-11-07T22:34+07:00` |
| Status | `PASS` local và CI |

## Phạm vi

| File | Nội dung |
|---|---|
| `domain/errors.py` | `ROUTE_NOT_FOUND` (404, "Không tìm thấy tài nguyên API.") và `METHOD_NOT_ALLOWED` (405, "Phương thức HTTP không được hỗ trợ cho tài nguyên này.") theo `docs/team/backend-http-status-contract.md`; exception tương ứng |
| `api/error_handlers.py` | `handle_routing_error`: `HTTPException` 404/405 của router → `ErrorEnvelope` qua đường lỗi miền (log `errorCode`, `X-Request-ID`), giữ header `Allow`; status khác giữ hành vi FastAPI (không tự bịa mã mới, D3); lỗi lạ → 500 an toàn |
| `contracts/openapi.yaml` | Thêm 2 mã vào enum; response dùng chung `NotFound`, `MethodNotAllowed` (`Allow`), `TemporaryRedirect` (`Location`); header `Cache-Control: no-store` cho health; mô tả 404/405/307 và việc không dùng 403/304 trong `info.description` |
| `apps/web/src/types/inference-api.ts` | Thêm 2 mã vào `ERROR_CODES` cùng commit (điểm lệch #2 giao P2 trong quy ước API, D3); drift test khớp OpenAPI ↔ Python ↔ TS |
| Tài liệu | Quy ước API lên `v1.0.2`; checklist trong `backend-http-status-contract.md` đã đánh dấu |

| Trường hợp | Hành vi |
|---|---|
| Route lạ (`/api/v1/not-found`, `/api/v2/health`, `/khong-ton-tai`) | 404 `ROUTE_NOT_FOUND`, không lặp lại URL của client, `X-Request-ID` (echo nếu client gửi UUID hợp lệ) |
| Sai method (`POST /health`, `DELETE /model-info`, `GET`/`PUT /predictions`) | 405 `METHOD_NOT_ALLOWED`, `Allow` đúng router (`GET` hoặc `POST`) |
| Dấu `/` cuối | Giữ 307 của Starlette, `Location` path chuẩn, có `X-Request-ID`; POST multipart đi qua redirect vẫn là POST và dự đoán được |
| 304 | `If-None-Match`/`If-Modified-Since` trên health và model-info vẫn 200, không `ETag`; health `Cache-Control: no-store` |
| 403 | Không có: preflight từ origin lạ vẫn là 400 của lớp CORS (ngoại lệ preflight, quy ước T099); GET thường 200 không có header CORS |
| CORS | 404/405 cho origin Vite có `access-control-allow-origin` và expose `X-Request-ID` |

FE hiện hiển thị lỗi bằng nhánh chung và luôn có fallback cho mã lạ, nên thêm mã không làm vỡ UI. Câu chữ riêng cho
404/405 ("lệch phiên bản FE/BE", theo `fe-be-api-convention.md`) chờ P5 bổ sung vào `vi.ts`.

## Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `cf44cd6` trước khi sửa (đã pull review T059/T062 của P1).
- Trước commit: pull T051/T052 của P5, T083 và review T052/T065 của P1, T065 của P3 (không trùng file); gate chạy lại: API + contract + integration 372 passed, 2 skipped; web lint, typecheck, Vitest 122/122.
- `origin/main...HEAD` = `0 0` tại `cfa9f04`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 8 failed (404/405 còn trả `{"detail"}`), test catalog lỗi collection (chưa có mã); 6 test hành vi cần giữ (307, POST qua redirect, không 304, preflight 400, CORS) xanh ngay để khóa hồi quy |
| GREEN | 14 contract định tuyến, 3 unit handler, 11 unit catalog |
| Bắt hồi quy | 6/6 mutation bị bắt: bỏ đăng ký handler, bỏ giữ `Allow`, 404 ánh xạ nhầm sang 405, status lạ thành 500, lỗi lạ đi nhánh mặc định, catalog 405 sai status |
| Toàn bộ API + contract | Như CI: 351 passed, 2 skipped. Extra `serving`: 369 passed, 1 skipped. Ruff, format, mypy 56 files; drift test khớp enum ba nơi |
| Web | `npm run lint`, `npm run typecheck`, Vitest 88/88 PASS |
| Live uvicorn (fixture) | `GET /api/v1/not-found` → 404, body chỉ `code/message/requestId`, `requestId` khớp header, có CORS; `POST /api/v1/health` → 405 `Allow: GET`; `GET /api/v1/predictions` → 405 `Allow: POST`; `GET /api/v1/health/` → 307 `Location: http://127.0.0.1:8016/api/v1/health`, có `X-Request-ID`; `POST /api/v1/predictions/` theo redirect → `[307]` rồi 200 "Cảm ơn", vẫn là POST |

## Ghi chú cho T092

FastAPI vẫn mở `/docs`, `/redoc`, `/openapi.json` (200). Không thuộc T073; đưa vào audit bảo mật để quyết định tắt hay giữ
khi chạy production.

**Reviewer result**: `PENDING`

## Independent review — P1/Huy

Review `2026-11-07T23:12:53+07:00` trên `28de816` (theo uỷ quyền của Huy). Gate: API + contract + integration 372 passed, 2 skipped; web lint, typecheck, Vitest 129/129; CI `quality.yml` xanh.

Probe P1 trên app thật (`TestClient`, không theo redirect):

| Request | Kết quả |
|---|---|
| `GET /api/v1/../v1/x%3Cscript%3E` | 404 `ROUTE_NOT_FOUND`, không lặp URL, echo `X-Request-ID` |
| `POST /health`, `PATCH /predictions` | 405 `METHOD_NOT_ALLOWED`, `Allow: GET` / `Allow: POST` |
| `GET /health/`, `POST /predictions/` | 307, `Location` đường dẫn chuẩn, có `X-Request-ID` |
| `GET /health` + `If-None-Match: *` | 200, `Cache-Control: no-store` (không bật 304) |

Ghi chú mang sang P5: `ERROR_CODES` (TS) tăng lên 13 nhưng `apps/web/src/content/vi.ts` mới có câu riêng cho 11
mã; `ROUTE_NOT_FOUND`/`METHOD_NOT_ALLOWED` đang dùng câu dự phòng (đạt D3) — bổ sung câu `apiRouteNotFound`,
`apiMethodNotAllowed` theo `docs/team/frontend-http-status-placeholders.md`.

**Reviewer result**: `P1_VERIFIED` → T072, T073 `[X]`.
