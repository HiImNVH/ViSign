# Quy ước API v1 giữa frontend và backend (lead handoff cho T099)

**Trạng thái**: Lead P1/Huy bàn giao ngày 2026-11-07. Tín (owner T099) và Hiển (consumer) xác nhận
rồi đóng băng tại `docs/contracts/api-conventions.md`, `contracts/openapi.yaml`,
`apps/web/src/types/inference-api.ts` và `tests/contract/`.

**Nguồn đã thống nhất được gom lại**: `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`,
`data-model.md`, [ai-backend-contract.md](ai-backend-contract.md),
[backend-http-status-contract.md](backend-http-status-contract.md) và
[frontend-http-status-placeholders.md](frontend-http-status-placeholders.md). Văn bản này không mở
endpoint, field hay status mới ngoài các nguồn trên; mục 8 là các quyết định lead bổ sung.

## 1. Nguồn chân lý và versioning

| Nội dung | Quy định |
|---|---|
| Nguồn chân lý | `openapi.yaml`. Python domain và TypeScript types phải khớp; lệch là lỗi drift test, không sửa tay một phía |
| Namespace | Mọi endpoint nằm dưới `/api/v1`. Release `0.0.1` ghi ở `info.version`, không nằm trong path |
| Thay đổi tương thích | Thêm field optional, thêm diagnostic optional: tăng patch/minor `info.version`, giữ `/api/v1` |
| Thay đổi phá vỡ | Đổi tên/xoá field, đổi kiểu, thêm field required, đổi nghĩa status/code: cần lead duyệt và `/api/v2`; MVP không dự kiến có |
| Error code mới | Chỉ thêm khi FE đã có xử lý; FE luôn có nhánh fallback "lỗi không xác định" cho code lạ |
| Type generation | MVP viết tay `inference-api.ts`; codegen là M1. Drift test so enum, required và nullable |

## 2. Đặt tên

| Phạm vi | Quy ước | Ví dụ |
|---|---|---|
| Path | lowercase, kebab-case, danh từ số nhiều cho tài nguyên, không trailing slash | `/api/v1/model-info`, `/api/v1/predictions` |
| `operationId` | camelCase động từ + danh từ | `getHealth`, `getModelInfo`, `createPrediction` |
| JSON field | camelCase, giống nhau ở Python, TS và OpenAPI | `processingTimeMs`, `demoReady` |
| Enum giá trị trạng thái | lowercase | `ok`, `degraded`, `fixture`, `pilot`, `full` |
| Error code | UPPER_SNAKE_CASE, bất biến | `CLIP_DECODE_FAILED` |
| ID nghiệp vụ | `meaningId` và `classLabel` theo [data-convention.md](data-convention.md) | `CAM_ON`, `CAM_ON_HN_1` |
| Header | `X-Request-ID`, `Retry-After`, `Allow`, `Location` | — |
| Đơn vị | Hậu tố `Ms` cho mili giây; tỉ lệ trong [0,1]; thời gian ISO 8601 UTC | `evaluatedAt: "2026-11-07T07:00:00Z"` |

## 3. Endpoint

| Method + path | Request | Thành công |
|---|---|---|
| `GET /api/v1/health` | Không body | `200 HealthResponse`, `Cache-Control: no-store`; `modelReady` không thay `demoReady` |
| `GET /api/v1/model-info` | Không body | `200 ModelInfo`; `503` khi chưa nạp được artifact |
| `POST /api/v1/predictions` | `multipart/form-data`, đúng một field `clip` | `200 PredictionResponse` cho cả accepted và rejected |

Clip: `video/webm` VP8/VP9, tối đa 10 MiB (10,485,760 bytes), 300–6000 ms đo bằng PTS phía server.
Frontend dừng ghi mặc định ở 5000 ms (`VITE_MAX_CAPTURE_MS`), không lật dữ liệu gửi đi, không upload file.

## 4. Response và nullability

- Field **required + nullable** (`classLabel`, `macroF1`, `perMeaningRecall`, `evaluatedAt`,
  `HealthResponse.modelVersion`) luôn có mặt; giá trị có thể `null`.
- Field **optional** (`timingsMs`, `qualityHints`) bị bỏ khỏi JSON khi vắng, không bao giờ là `null`.
  Object diagnostics cấm field lạ; không bao giờ chứa frame, landmark hay ảnh.
- Rejected: `200`, `accepted=false`, `classLabel=null`, `text="Không nhận diện được"`.
- Accepted: `text` là chữ hiển thị tiếng Việt không rỗng, `classLabel` khác `null`.
- FE không dùng `timingsMs`/`qualityHints` để quyết định accepted; quyết định thuộc server.
- FE bỏ qua prediction có `modelVersion` khác model-info đang hiển thị và tải lại model-info.

## 5. Lỗi và status

Mọi lỗi dùng `ErrorEnvelope {code, message, requestId}`, không bao giờ dùng shape `{"detail": ...}`.
FE hiển thị câu chữ theo `code` từ `apps/web/src/content/vi.ts`, **không render `message` của server**.

| Status | Code | Ghi chú FE |
|---|---|---|
| 400 | `INVALID_REQUEST` | Thiếu/sai field `clip` |
| 413 | `CLIP_TOO_LARGE` | Ghi lại clip ngắn hơn |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Trình duyệt không hỗ trợ WebM |
| 422 | `CLIP_TOO_SHORT`, `CLIP_TOO_LONG`, `NO_PERSON_DETECTED`, `INSUFFICIENT_LANDMARKS`, `CLIP_DECODE_FAILED` | Hướng dẫn quay lại |
| 503 | `SERVICE_BUSY` (`Retry-After: 3`), `MODEL_NOT_READY` (`Retry-After: 5`) | Thử lại do người dùng bấm, không tự lặp |
| 500 | `PREDICTION_FAILED` | Không lộ stack/path |
| 404 | `ROUTE_NOT_FOUND` | Lệch phiên bản FE/BE; không retry tự động |
| 405 | `METHOD_NOT_ALLOWED` + `Allow` | Lệch phiên bản; tối đa một lần reload do người dùng |
| 307 | — | Chuẩn hoá trailing slash; FE luôn gọi path chuẩn, test xác nhận không bị redirect |
| 403, 304 | — | Dự phòng, chưa triển khai trong MVP |

`ROUTE_NOT_FOUND` và `METHOD_NOT_ALLOWED` được thêm vào enum `ErrorEnvelope.code` của OpenAPI ở T073.
Từ chối quyền camera là lỗi thiết bị phía FE, không ánh xạ sang `403`.

## 6. Correlation, CORS và timeout

- FE gửi `X-Request-ID` (UUID v4) cho mọi request; server tạo UUID nếu thiếu/sai và echo ở mọi
  response header; `requestId` trong body bằng header.
- CORS mặc định chỉ cho origin dev/preview của Vite, không gửi credential; production cấu hình qua
  `CORS_ORIGINS`. CORS bị từ chối không phải `403`.
- FE timeout prediction 15 s, model-info/health 5 s, có abort khi reset/unmount và chặn upload trùng.

## 7. Kiểm thử bắt buộc khi đóng T099

- Drift test: enum `ErrorEnvelope.code`, `artifactKind`, `status` và danh sách field required/nullable
  khớp giữa `openapi.yaml`, Python domain và `inference-api.ts`.
- Contract test: rejected `200`, mỗi status ở mục 5, header `X-Request-ID`/`Retry-After`/`Allow`.
- FE transport test: không render `message` của server, xử lý code lạ bằng fallback.

## 8. Quyết định lead bổ sung — cần Tín/Hiển xác nhận

| # | Quyết định | Lý do |
|---|---|---|
| D1 | Giữ `CLIP_DECODE_FAILED` ở 422; sửa mô tả 422 trong OpenAPI thành "Clip cannot be decoded or does not satisfy inference constraints" | Khớp code T021 đã review; mô tả cũ "readable" mâu thuẫn |
| D2 | FE timeout 15 s cho prediction, 5 s cho health/model-info | Spec chưa có số; gate p95 ≤ 3 s vẫn đo riêng |
| D3 | Error code mới phải có FE fallback trước khi BE phát hành | Tránh UI vỡ khi enum mở rộng |
| D4 | Không codegen type trong MVP | Giữ phạm vi; drift test thay thế |
