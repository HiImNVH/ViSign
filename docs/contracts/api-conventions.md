# Quy ước API v1 FE–BE — bản đóng băng (T099)

| Trường | Giá trị |
|---|---|
| Phiên bản quy ước | `api-conventions-v1.0.0` |
| Trạng thái | `FROZEN` phía owner P2/Tín ngày 2026-11-07; P5/Hiển (consumer) xác nhận `PENDING` |
| Đầu vào | Lead handoff [fe-be-api-convention.md](../team/fe-be-api-convention.md) (P1/Huy, `377ac98`) |
| Nguồn chân lý | [`openapi.yaml`](../../specs/001-vsl-recognition-mvp/contracts/openapi.yaml), `info.version = 0.0.1`, namespace `/api/v1` |
| Đồng bộ | Python domain `services/inference-api/src/visign_api/domain/`, TypeScript `apps/web/src/types/inference-api.ts` |
| Drift test | [`tests/contract/test_api_contract_drift.py`](../../tests/contract/test_api_contract_drift.py), chạy trong job `api` của `quality.yml` |

Văn bản này đóng băng toàn bộ mục 1–7 của lead handoff, không mở endpoint, field hay status mới. Mọi
thay đổi sau đây phải đi qua quy trình ở mục 4.

## 1. Quyết định bổ sung đã chốt

| # | Quyết định | Cách áp dụng và kiểm chứng |
|---|---|---|
| D1 | Giữ `CLIP_DECODE_FAILED` ở 422; mô tả 422 của `POST /api/v1/predictions` là "Clip cannot be decoded or does not satisfy inference constraints" | Đã sửa `openapi.yaml`; `test_unprocessable_clip_description_follows_decision_d1` khóa câu chữ; `ERROR_CATALOG` giữ 422 |
| D2 | FE timeout 15 s cho prediction, 5 s cho health/model-info, có abort khi reset/unmount | Thuộc client FE (T040/T053); gate p95 ≤ 3 s vẫn đo riêng (SC-002) |
| D3 | Error code mới chỉ phát hành khi FE đã có xử lý; FE luôn có fallback cho code lạ | `ERROR_CODES` trong TS phải bằng enum OpenAPI và `ErrorCode` Python (drift test); `ErrorEnvelope.code` kiểu `KnownErrorCode \| string` + `isKnownErrorCode()` cho nhánh fallback |
| D4 | MVP không codegen type | `inference-api.ts` viết tay; drift test so enum, field, required và nullable cho `HealthResponse`, `ModelInfo`, `PredictionResponse`, `PredictionTimings`, `PredictionQualityHints`, `ErrorEnvelope` |

## 2. Quy tắc tóm tắt (chi tiết tại lead handoff mục 1–7)

- Path lowercase kebab-case, không trailing slash; JSON field camelCase giống nhau ở Python, TS và OpenAPI;
  enum trạng thái lowercase; error code UPPER_SNAKE_CASE bất biến; hậu tố `Ms` cho mili giây.
- Required + nullable luôn có mặt (có thể `null`); optional (`timingsMs`, `qualityHints`) bị bỏ khi
  vắng, không bao giờ `null`, cấm field lạ và không chứa frame/landmark.
- Mọi lỗi dùng `ErrorEnvelope {code, message, requestId}`; FE hiển thị câu chữ theo `code`, không render
  `message` của server. Status theo bảng mục 5 của lead handoff.
- Mọi response có `X-Request-ID`; server tạo UUID khi thiếu/sai. CORS chỉ origin cấu hình, không `*`,
  không credential.
- Clip `video/webm` VP8/VP9, ≤ 10,485,760 byte, 300–6000 ms đo bằng PTS phía server.

## 3. Điểm lệch phát hiện khi đóng băng

| # | Điểm lệch | Xử lý đóng băng | Owner |
|---|---|---|---|
| 1 | Lead handoff mục 4 ghi `HealthResponse.modelVersion` là required + nullable; OpenAPI chỉ nullable, không required | Theo OpenAPI (nguồn chân lý): TS `modelVersion?: string \| null`, FE xử lý cả vắng lẫn `null`. Chuyển sang required là thay đổi cần lead duyệt | P1/Huy quyết định |
| 2 | `ROUTE_NOT_FOUND`, `METHOD_NOT_ALLOWED` có trong lead handoff mục 5 nhưng chưa có trong enum OpenAPI | Thêm ở T073 cùng lúc với TS `ERROR_CODES` (D3) | P2/Tín |
| 3 | So khớp MIME hiện là chuỗi chính xác (review T022 của P1) | T049 chuẩn hóa base type `video/webm` không phân biệt hoa thường, bỏ khoảng trắng/ngoặc kép tham số | P2/Tín |

## 4. Quy trình thay đổi sau đóng băng

1. Sửa `openapi.yaml` trước; thay đổi phá vỡ (đổi tên/xóa field, đổi kiểu, thêm field required, đổi
   nghĩa status/code) cần lead duyệt và `/api/v2`.
2. Cập nhật Python domain và `inference-api.ts` trong cùng commit; drift test phải xanh.
3. Error code mới: FE thêm vào `ERROR_CODES` và câu chữ `vi.ts` trước hoặc cùng lúc (D3).
4. Tăng `info.version` theo semver cho thay đổi tương thích khi lead yêu cầu phát hành.
