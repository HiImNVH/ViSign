# CP2 — P5 review response, error và CORS

- Base được review: `39209c7`, bao gồm T020/T021, T022/T026 và quy ước T099.
- Môi trường: Windows, Python 3.12; API Ruff và mypy PASS, pytest 158 PASS / 1 SKIPPED.
- **T021 — P5_VERIFIED:** error catalog, mã và status theo test contract hiện có, gồm `CLIP_DECODE_FAILED` 422 và `SERVICE_BUSY` 503. Đây là xác nhận catalog, không phải luồng prediction thực tế.
- **T020 — CHANGES_REQUESTED:** thử tạo `PredictionResponse` với `accepted=false`, `classLabel=null`, `text="unexpected"` thành công; quy ước yêu cầu text `Không nhận diện được`. Cần bổ sung validation và test trước khi verify.
- **CORS T022/T026 — CHANGES_REQUESTED:** test mặc định xác nhận origin Vite, preflight, header và không credential; tuy nhiên `Settings(cors_allow_credentials=True)` vẫn được chấp nhận và middleware dùng giá trị này, trái quy ước không credential. Cần chặn override và kiểm thử lại.
- Preflight bị từ chối không có request ID và trả plain text; P1 đã ghi chấp nhận ngoại lệ này trong review T026, nhưng wording trong quy ước nói mọi response có request ID và lỗi dùng envelope. Cần thống nhất wording/ngoại lệ.
- Router thực tế chưa có health/model-info/predictions; chưa thể xác nhận luồng trình duyệt tới endpoint thật. Tín xử lý các điểm cần sửa; P5 kiểm tra lại sau khi có commit mới.
