# CP2 — P5 review response, error và CORS

- Review base: `0c7b38c` (bao gồm T099, T020–T022 và T026); Windows, Python 3.12.
- Gate: API Ruff PASS, mypy PASS (36 files), pytest 158 PASS / 1 SKIPPED.
- T021: `P5_VERIFIED` cho error catalog và mapping hiện có: enum, status, `CLIP_DECODE_FAILED` 422, `SERVICE_BUSY` 503 và Retry-After; runtime endpoint thực tế vẫn chờ các task tiếp theo.
- T020: `CHANGES_REQUESTED`. Response rejected hiện chấp nhận `text` tùy ý dù quy ước yêu cầu `Không nhận diện được`; accepted cho phép classLabel chỉ gồm khoảng trắng. Cần sửa và thêm test trước khi xác nhận.
- CORS T022/T026: `CHANGES_REQUESTED`. Mặc định cho origin Vite, từ chối wildcard, expose `X-Request-ID`/`Retry-After` và test preflight đạt; tuy nhiên `cors_allow_credentials` có thể bật qua cấu hình, trái quy ước không credential. Cần chặn override và kiểm thử lại.
- Preflight bị từ chối trả plain text và không có request ID; cần làm rõ ngoại lệ này với quy ước yêu cầu envelope và request ID cho mọi response. Các endpoint thực chưa triển khai nên chưa verify luồng frontend–backend thực tế.
- Xác nhận phía consumer D1–D4: FE áp dụng decode 422; timeout 15s prediction và 5s health/model-info; fallback cho error code lạ; type viết tay cùng drift test. Việc xác nhận quy ước không có nghĩa T040 đã hoàn thành.
