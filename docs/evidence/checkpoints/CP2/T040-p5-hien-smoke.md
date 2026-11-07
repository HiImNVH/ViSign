# T040 — frontend API client

- Client sends a single camera blob as multipart `clip`, sends UUID `X-Request-ID` and reads response correlation and `Retry-After`. It supports model-info and health, request cancellation, 15 s prediction and 5 s metadata timeouts.
- Responses receive runtime shape checks; unknown error codes remain available to a future UI fallback without exposing server messages. Optional diagnostics can be absent.
- Windows / Node 26.7.0: lint, typecheck, Vitest and production build passed. Tests use mocked transport; no live endpoint or UI recognition integration is claimed. T041/T043/T053 remain separate.
- Candidate includes only the client, its tests and this evidence. Existing uncommitted camera/README changes were present during tests and are excluded from the commit.
- Status: local implementation for independent P2/P1 review; not verified end-to-end.

## Independent review — P2/Tín (API contract)

Review time `2026-11-07T19:25+07:00` trên `origin/main` `9abd2f3` (chứa `240d290`); Windows, Node 24.18.0.

| Kiểm tra theo `docs/contracts/api-conventions.md` | Kết quả |
|---|---|
| Path | `/api/v1/health`, `/api/v1/model-info`, `/api/v1/predictions`, không trailing slash; base URL bỏ `/` cuối |
| Upload | `multipart/form-data` đúng một field `clip` |
| Correlation | Gửi `X-Request-ID` = `crypto.randomUUID()` mỗi request; đọc header server trả, fallback ID đã gửi |
| CORS | `credentials: 'omit'` |
| D2 timeout | 15 s prediction, 5 s health/model-info; abort khi caller hủy; phân biệt `timeout`/`cancelled`/`network`/`http`/`invalid-response` |
| D3 / lỗi | Giữ `code` lạ, đọc `Retry-After`, `Error.message` chỉ là `kind` — không mang `message` của server |
| Shape | Guard runtime cho `PredictionResponse`, `ModelInfo`, `HealthResponse`; diagnostics optional; field lạ được bỏ qua (tương thích khi thêm field optional) |
| Gate | Vitest (gồm `tests/inferenceApi.test.ts`) 47 passed; lint, typecheck, build PASS |
| Live API | `NOT_RUN` — router chưa có endpoint (T038/T060) |

Ghi chú không chặn:

1. `MEDIUM` `isModelInfo` nhận `meanings: []` và không kiểm `acceptanceThreshold` ∈ [0,1], trong khi OpenAPI yêu cầu
   1–10 meanings; test model-info đang dùng `meanings: []` (dữ liệu không hợp lệ theo contract). Đề xuất siết guard và
   dùng dữ liệu hợp lệ trong test.
2. `LOW` `isPrediction` chưa kiểm khoảng của `qualityHints`/`timingsMs` (≥0, ratio ∈ [0,1], `frameCount` ≥1) và bất biến
   bị từ chối (`accepted=false` ⇒ `classLabel=null`, `text="Không nhận diện được"`; server đã bảo đảm từ `6ee9e61`).
3. `LOW` Chưa có test cho timeout 15 s của prediction, lỗi `network`, và fallback khi thiếu header `X-Request-ID`.
4. `LOW` `inferenceApi.ts` thiếu dòng header path theo `.agent/core.md` §4.1 (các file web khác đã có);
   `InferenceApiError` nhận 5 tham số (§6.1).

**Reviewer result**: `P2_VERIFIED` cho phần API contract của T040; tích hợp endpoint thật chờ T038/T060.

## Live integration follow-up — P5/Hiển — 2026-11-07

Sau khi T038/T060 có router và fixture predictor, P5 kiểm tra lại **frontend thực sự gọi FastAPI** trên Windows / Node `v26.7.0`, Playwright Microsoft Edge. Kết quả này bổ sung cho review contract của P2 ở trên; phần tích hợp live mới **chờ review độc lập**, không tự đánh dấu `[X]` cho T040.

| Đầu việc | Cách kiểm chứng / kết quả |
|---|---|
| Backend trực tiếp | Uvicorn `127.0.0.1:8000` dùng `services/inference-api/tests/fixtures/model-artifacts/fixture`; `:8001` dùng `fixture-low-confidence`; `:8002` trỏ tới artifact không tồn tại. `GET /api/v1/health` xác nhận lần lượt `ok`, `ok`, `degraded`. |
| Metadata/API client | `VISIGN_LIVE_API_URL`, `VISIGN_LIVE_API_REJECT_URL`, `VISIGN_LIVE_API_DEGRADED_URL` trỏ tới ba cổng; `tests/liveInferenceApi.integration.test.ts` gọi `fetch` thật qua typed client, không mock. Metadata có `artifactKind=fixture`, `demoReady=false`, meanings hợp lệ. |
| Prediction | Multipart `clip` có EBML + WebM DocType: accepted `Cảm ơn` / confidence `0.95`, low-confidence rejected `Không nhận diện được` / `0.42`, correlation ID khớp header/payload; MIME không hỗ trợ trả `415`, degraded trả `503 MODEL_NOT_READY`, `Retry-After: 5`. Fixture predictor kiểm chữ ký nhưng không decode video. |
| Guards | Siết UUID, probability `[0,1]`, meanings `1..10`, integer timings/processing, quality hints, RFC 3339 datetime, accepted/rejected invariants và correlation header/payload; unit cases cho lỗi network, thiếu response correlation header, diagnostics không có, metadata/prediction không hợp lệ. |
| Browser ↔ backend thật | Build với `VITE_API_BASE_URL=http://127.0.0.1:8000` (cross-origin trực tiếp); Playwright Edge dùng fake camera, ghi WebM và chỉ gửi khi bấm **Gửi nhận diện**; đúng một POST, hiển thị `Cảm ơn` cùng cảnh báo `demoReady=false`; chạy trên desktop, mobile và landscape. Không intercept API trong bài test này. |
| Web gate | `cd apps/web; $env:VISIGN_LIVE_API_URL='http://127.0.0.1:8000'; $env:VISIGN_LIVE_API_REJECT_URL='http://127.0.0.1:8001'; $env:VISIGN_LIVE_API_DEGRADED_URL='http://127.0.0.1:8002'; $env:VITE_API_BASE_URL='http://127.0.0.1:8000'; $env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check` — exit code `0`: lint/typecheck/Vitest/build/Playwright **PASS**, 156 Vitest + 51 browser tests, gồm trường hợp datetime thiếu timezone. |

Giới hạn: đây là **fixture integration**; chưa xác nhận webcam vật lý, giải mã WebM/landmark, chất lượng mô hình thật hoặc latency production. API OpenAPI tự sinh và YAML frozen có drift ở phần mô tả route/errors/diagnostics; cần P2 xử lý riêng trong ownership backend, không nằm trong thay đổi T040 của P5.

## Independent review — P1/Huy

Review `2026-11-07T23:47:41+07:00` trên `24a9e21` (theo uỷ quyền của Huy). Web lint, typecheck, Vitest 152 passed / 4 skipped;
`liveInferenceApi.integration.test.ts` dùng `describe.skipIf` theo `VISIGN_LIVE_API_*` nên không làm đỏ CI
khi không có backend. Client gọi FastAPI thật đã được P1 smoke độc lập trước đó qua proxy Vite (health,
model-info, predictions 200/415, `X-Request-ID`). P2 đã verify phần contract.

**Reviewer result**: `P1_VERIFIED` → T040 `[X]`.
