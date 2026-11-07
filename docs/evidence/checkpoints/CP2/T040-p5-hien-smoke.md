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
