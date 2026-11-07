# ViSign · Model card

**Trạng thái** · T062, bản mô tả triển khai. Kết quả trên dữ liệu VSL đã duyệt đang chờ đánh giá.
**Phụ trách** · P3/Cường. P4/Quang bàn giao dữ liệu, P2/Tín phụ trách serving, P1/Huy duyệt phát hành.

## Phạm vi model

ViSign nhận diện một ký hiệu VSL trong một clip camera và trả về một nghĩa tiếng Việt hoặc trạng thái “Không nhận diện được”. Class map giữ các biến thể vùng ở lớp riêng khi cần, rồi ánh xạ lớp dự đoán sang nghĩa. Luồng ghép chữ trên web sử dụng các kết quả đã chấp nhận từ nhiều lượt riêng lẻ.

| Artifact | Phạm vi | Trạng thái |
|---|---|---|
| `fixture` | Fixture mẫu trong repo công bố **Cảm ơn, Sốt, Giấy tờ**. Phạm vi lấy từ metadata fixture được cấu hình. | Dùng để kiểm tích hợp. `demoReady=false`. |
| `pilot` | Tối đa 3 nghĩa. Mục tiêu T083 là **Sốt, Chờ** trên bản pilot đã audit. | Đã thử nạp và dự đoán bằng artifact tổng hợp. Chờ run T083 thật. `demoReady=false`. |
| `full` | 10 nghĩa P0 theo danh mục cập nhật ngày 07/11/2026. | Đã thử luồng với artifact tổng hợp 10 nghĩa. Chờ manifest full và đánh giá trước khi Huy duyệt phát hành. |

**P0 hiện tại** · Giấy tờ (giấy), Đau bụng, Sốt, Nhận, Bạn, Cảm ơn, Giúp đỡ, Xin lỗi, Đau đầu, Không. Chờ thuộc pilot và nằm ngoài danh mục full P0 hiện tại. [Đặc tả MVP](../specs/001-vsl-recognition-mvp/spec.md#clarifications) · [Metadata fixture mẫu](../services/inference-api/tests/fixtures/model-artifacts/fixture/model_info.json)

## Kiến trúc và quyết định dự đoán

MediaPipe trích landmark hai tay, thân trên và vùng mặt. Pipeline dùng chung chuẩn hóa chuỗi thành tensor **32 × 234** với tọa độ và tín hiệu landmark hợp lệ. GRU đọc chuyển động theo thời gian trên chuỗi đã xử lý. Nhóm chọn GRU một tầng làm baseline gọn để chạy và tái lập trên CPU, đồng thời giữ thông tin thứ tự động tác. Đây là lựa chọn kiến trúc của MVP, chưa có benchmark đối chứng với kiến trúc khác.

Backend kiểm tra clip và chất lượng landmark trước khi gọi GRU. Model chọn lớp có xác suất softmax cao nhất, sau đó tra nghĩa qua class map. Khi confidence thấp hơn ngưỡng lưu trong artifact, giao diện trả “Không nhận diện được”. Confidence là điểm softmax của lớp, chưa có bằng chứng hiệu chuẩn để diễn giải như xác suất đúng ngoài thực tế.

## Protocol tái lập

1. Cố định commit, phiên bản manifest, class map, schema đã duyệt, extractor và detector. Lưu hash cùng cấu hình môi trường Python, PyTorch và thiết bị. Schema trong repo tại thời điểm viết vẫn là `DRAFT_PENDING_LEAD_REVIEW`. [Feature schema](../ai/configs/feature_schema.json)
2. Audit theo FR-015. Tất cả clip cắt từ cùng video gốc thuộc một split theo `recordingSessionId`. Báo cáo ghi `video-held-out` nếu thiếu mã người ký hoặc có người ký xuất hiện ở nhiều split. Chỉ ghi `signer-held-out` khi đủ mã và các split không chung người ký.
3. Chạy T017 để trích tensor. Train GRU bằng T036, seed mặc định 42. Preset pilot dùng hidden size 64 và 30 epoch, full dùng 128 và 60 epoch. Dùng validation loss chọn checkpoint và dùng validation chọn threshold. [T017](evidence/checkpoints/CP2/T017-p3-cuong-smoke.md) · [T036](evidence/checkpoints/CP3/T036-p3-cuong-smoke.md) · [Preset pilot](../ai/configs/pilot-gru.yaml) · [Preset full](../ai/configs/p0-gru.yaml)
4. Chạy T058 trên tập test với đúng trọng số, schema và manifest từ T036. Giữ `evaluation-report.json` và `confusion-matrix.png` cùng nhau. T059 kiểm tra provenance và ghi metric vào metadata. [T058](evidence/checkpoints/CP5/T058-p3-cuong-smoke.md) · [T059](evidence/checkpoints/CP5/T059-p3-cuong-smoke.md)

## Kết quả và cổng phát hành

| Chỉ số hoặc bằng chứng | Hiện trạng |
|---|---|
| Accuracy và Macro-F1 | Chờ kết quả tập test VSL đã audit. Fixture để trống metric. |
| Precision, recall và số clip từng nghĩa | Chờ báo cáo T058 từ artifact thật. Mẫu dưới ngưỡng vẫn nằm trong mẫu số. |
| Confusion matrix | CLI đã xuất ảnh với dữ liệu tổng hợp. Ma trận VSL thật chờ dữ liệu test. Cột từ chối thể hiện những mẫu dưới ngưỡng. |
| Split FR-015 | Đã kiểm thử cơ chế phát hiện rò rỉ video gốc. Chờ audit manifest thật, báo cáo số clip mỗi split và mức độ nhận diện được người ký. |
| OOD và false accept | Chờ T089 đo trên ký hiệu ngoài phạm vi, không ký hiệu và các điều kiện camera khác nhau. Smoke API đã kiểm mã lỗi không có người và thiếu landmark bằng đặc trưng có kiểm soát. |
| Latency | Smoke local của Tín trên 32 clip thật với GRU trọng số tổng hợp ghi p95 xử lý API 4,73 s, trong đó p95 trích landmark 4,48 s. T058 đo p50/p95 của GRU trên tensor đã nạp. Chờ T065 đo decode, extract, infer và tổng thời gian local/production. Mục tiêu SC-002 là p95 không quá 3 giây từ lúc gửi đến khi UI hiện kết quả hoặc lỗi có thể xử lý. |

[T058 và ma trận](evidence/checkpoints/CP5/T058-p3-cuong-smoke.md) · [Smoke HTTP T037](evidence/checkpoints/CP3/T037-p2-tin-gru-adapter-smoke.md) · [Smoke clip thật của Tín](evidence/checkpoints/CP3/T037-p2-tin-real-clip-smoke.md) · [Benchmark serving tham chiếu](evidence/checkpoints/CP7/T095-p2-tin-serving-ram-benchmark.md)

Chỉ full đủ 10 nghĩa P0, có mẫu test mỗi nghĩa, audit FR-015 đạt, Macro-F1 ≥ 80% và recall từng nghĩa ≥ 65% mới đủ cổng chất lượng. T059 mặc định ghi `demoReady=false`. Bật cờ phát hành sau khi Huy duyệt và chạy quy trình T059 với danh mục P0. [FR-015 và FR-016](../specs/001-vsl-recognition-mvp/spec.md#functional-requirements) · [T059](evidence/checkpoints/CP5/T059-p3-cuong-smoke.md)

## Giới hạn và fallback

- Dữ liệu ưu tiên biến thể TP.HCM. Độ phủ vùng miền, người ký, tốc độ ký, ánh sáng, góc máy và mức che khuất vẫn cần đo. Split theo video gốc chỉ xác nhận đã tách video. Khi thiếu `signerId`, mức độ tổng quát sang người ký mới vẫn chưa xác định.
- Có thể giải thích đầu ra qua phiên bản artifact, lớp → nghĩa, confidence, threshold và lý do từ chối. Overlay landmark giúp chẩn đoán đầu vào, còn việc model dựa vào phần động tác nào để phân loại vẫn chưa xác định.
- Bản chạy local và artifact đã smoke-test là phương án rollback khi trình diễn, chờ tổng duyệt T067. Backend cần cấu hình `MODEL_ARTIFACT_PATH` tường minh. Khi thiếu artifact, API báo degraded. Fixture được chọn tường minh để kiểm tích hợp và hiển thị đúng trạng thái. [Cấu hình backend](../services/inference-api/src/visign_api/config.py)
- ViSign là công cụ hỗ trợ thử nghiệm. Kết quả có thể sai. Trong tình huống quan trọng, cần phiên dịch viên chuyên nghiệp để xác nhận thông tin.
