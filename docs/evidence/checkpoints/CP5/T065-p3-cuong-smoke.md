# CP5 T065 · P3/Cường

P3/Cường đo local trên baseline cedd013. Review P1/Huy và P2/Tín. [Báo cáo và lệnh chạy](../../../performance-report.md)

| Gate | Kết quả |
|---|---|
| Ruff và mypy AI | PASS, mypy kiểm 27 file |
| Pytest AI | 79 passed, 1 skipped do quyền symlink trên Windows |
| CLI benchmark HTTP thật | 18/18 request hợp lệ trả 200. Tách decode/extract/infer, tổng, throughput, CPU/RAM |
| Kiểm lại CLI bản cuối | 1 clip hợp lệ có report. Input sai trả 415, CLI exit 2 và không tạo báo cáo |
| Edge local qua API thật | 6/6 HTTP 200 sau đồng bộ frontend 05d906f. p95 từ bấm gửi đến thấy kết quả 6,42 s. Trước đồng bộ 8,10 s |
| Production | Chờ URL deploy và đo tài nguyên worker trên host |

Local chưa đạt SC-002. Kết quả API p95 5,71 s ở client HTTP, phần trích landmark p95 5,26 s. Artifact pilot dùng trọng số tổng hợp. Evidence này phục vụ tối ưu hiệu năng và chưa đóng T065.

**Reviewer result** PENDING

## Independent review — P1/Huy

Review `2026-11-07T22:43:49+07:00` trên `cc9a214` (theo uỷ quyền của Huy). Ruff, mypy (27 file) PASS; `benchmark_inference --help` chạy.

Số đo local nhất quán với evidence P2 (p95 API 4,73 s) và cho thấy nút thắt rõ: **extract MediaPipe p50
4.644 ms / p95 5.265 ms**, GRU p95 4 ms; web p95 6.425 ms → **SC-002 (≤ 3 s) trượt gấp đôi**.

Nguyên nhân có bằng chứng trong code: `ai/src/visign_ai/landmarks/holistic_extractor.py` dòng ~93 vẫn đọc
model và `create_from_options` 3 detector **cho mỗi clip** (đã ghi ở review T014–T016 mục 4), cộng với decode
toàn bộ frame trước khi lấy mẫu (mục 3). Đề xuất P3 đo tách chi phí khởi tạo, thử giữ detector giữa các
request (reset bằng timestamp mới/instance pool) và lấy mẫu trước khi chuyển RGB; mọi thay đổi phải giữ
parity offline ↔ API.

**Reviewer result**: `P1_VERIFIED` phần local. T065 giữ `[ ]` vì task yêu cầu cả **production** (chưa có
URL/host đo) và SC-002 chưa đạt.

## Candidate khởi tạo detector song song

Baseline đo `cfa9f04`. Dùng cùng 6 clip review, detector đã kiểm SHA-256, cùng
schema và cùng lịch lấy mẫu. Số đo và cách đối chứng ở [báo cáo T065](../../../performance-report.md#thử-tối-ưu-khởi-tạo-detector).
Chạy lại Ruff, mypy, pytest AI/API và T064 trên `5cec97b` sau khi đồng bộ các
commit CP2/CP4 mới. Phần mã AI dùng cho phép đo giống nhau giữa hai mốc.

| Kiểm tra local | Kết quả |
|---|---|
| `ruff check ai` và `python -m mypy ai/src ai/tests` | PASS, mypy kiểm 27 file |
| `pytest ai/tests -q -rs` | 79 pass, 1 skip do Windows thiếu quyền tạo symlink. Có cấp 4 clip VP8/VP9 Chrome/Edge và clip WebM tham chiếu |
| `pytest services/inference-api/tests tests/contract -q -rs` | 374 pass trên `5cec97b`, có cấp `VISIGN_CP2_REFERENCE_WEBM` cho parity. Dùng metadata wheel API 0.0.1 dựng từ mã repo |
| `pytest tests/integration/test_prediction_pipeline.py -q -rs` (T064) | 4 pass trên `5cec97b`, gồm parity clip thật, đổi artifact fixture/pilot/full và cleanup |
| Candidate ↔ baseline trên WebM thật | 12/12 tensor đạt `atol=1e-6, rtol=0`; `point_valid`, `masks` và `tensor_mask` khớp tuyệt đối |
| Uvicorn loopback + artifact T036 tổng hợp | 6/6 HTTP 200 và request ID khớp. Payload sai trả 415. Hai WebM trống đen/trắng trả 422 `NO_PERSON_DETECTED`. Đây là smoke T049, chưa có số đo false accept của model VSL cho T089 |
| Edge web trên candidate ở `c875ae5` | 6/6 HTTP 200, web p95 5,87 giây. SC-002 chưa đạt |
| Production | Chưa có URL/worker production để đo |

Candidate chờ P1/P2 review. T065 giữ mở.
