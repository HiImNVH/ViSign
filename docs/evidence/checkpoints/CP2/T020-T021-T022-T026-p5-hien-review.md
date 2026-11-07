# CP2 — P5 review response, error và CORS

## Kiểm tra lại bản sửa — P5/Hiển (`2026-11-07`)

- **Kết luận: `P5_VERIFIED` cho T020, T022 và T026.** Kiểm tra độc lập trên `main` tại
  `bb40476` (working tree sạch khi bắt đầu review). Các fix được kiểm:
  `6ee9e61` (text rejected), `542e33f` (nhãn chỉ có khoảng trắng) và `b139007`
  (khóa CORS credentials).
- **T020 — `P5_VERIFIED`:** `accepted=false` phải có `classLabel=null` và
  `text="Không nhận diện được"`; `text="unexpected"`, rejected mang `classLabel`
  khác `null` và accepted có `classLabel` rỗng/toàn khoảng trắng đều bị `ValidationError`.
  Kết quả hợp lệ bỏ optional diagnostics khi vắng và vẫn xuất `classLabel: null`.
- **T022 — `P5_VERIFIED`:** `Settings(cors_allow_credentials=True)` và biến môi trường
  `CORS_ALLOW_CREDENTIALS=true`/`1` đều bị `ValidationError`; mặc định vẫn `False`.
- **T026 — `P5_VERIFIED`:** kiểm thử HTTP bằng `TestClient` với route probe:
  origin Vite hợp lệ nhận `Access-Control-Allow-Origin`, `X-Request-ID` trên response
  thông thường, không có `Access-Control-Allow-Credentials`; preflight hợp lệ `200`,
  preflight origin lạ `400`, không trả `Access-Control-Allow-Origin`.
  Preflight không có `X-Request-ID` theo **ngoại lệ đã được ghi rõ** tại
  `docs/contracts/api-conventions.md` phiên bản `v1.0.1`.
- **Gate chạy lại:**
  `python -m pytest services/inference-api/tests tests/contract -q -W error`:
  **179 passed, 1 skipped**; Ruff **PASS**; mypy **PASS (22 source files)**.
  Các probe domain/config/CORS độc lập đều **PASS**.
- Các task T020/T022/T026 đã được P1 đóng `[X]` trong
  `specs/001-vsl-recognition-mvp/tasks.md`; P5 xác nhận các lỗi từng nêu đã được khắc phục.
  Các endpoint thật (`/health`, `/model-info`, `/predictions`) thuộc T038/T060,
  chưa được kiểm thử E2E trong lần review này.

## Review ban đầu (lịch sử, trước các bản sửa)

- Base được review: `39209c7`, bao gồm T020/T021, T022/T026 và quy ước T099.
- Môi trường: Windows, Python 3.12; API Ruff và mypy PASS, pytest 158 PASS / 1 SKIPPED.
- **T021 — P5_VERIFIED:** error catalog, mã và status theo test contract hiện có, gồm `CLIP_DECODE_FAILED` 422 và `SERVICE_BUSY` 503. Đây là xác nhận catalog, không phải luồng prediction thực tế.
- **T020 — CHANGES_REQUESTED:** thử tạo `PredictionResponse` với `accepted=false`, `classLabel=null`, `text="unexpected"` thành công; quy ước yêu cầu text `Không nhận diện được`. Cần bổ sung validation và test trước khi verify.
- **CORS T022/T026 — CHANGES_REQUESTED:** test mặc định xác nhận origin Vite, preflight, header và không credential; tuy nhiên `Settings(cors_allow_credentials=True)` vẫn được chấp nhận và middleware dùng giá trị này, trái quy ước không credential. Cần chặn override và kiểm thử lại.
- Preflight bị từ chối không có request ID và trả plain text; P1 đã ghi chấp nhận ngoại lệ này trong review T026, nhưng wording trong quy ước nói mọi response có request ID và lỗi dùng envelope. Cần thống nhất wording/ngoại lệ.
- Router thực tế chưa có health/model-info/predictions; chưa thể xác nhận luồng trình duyệt tới endpoint thật. Tín xử lý các điểm cần sửa; P5 kiểm tra lại sau khi có commit mới.
