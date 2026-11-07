# CP5 T062 · P3/Cường

Owner P3/Cường. Reviewer P1/Huy.

- Đã viết [model card ViSign](../../../model-card.md) theo T062 và FR-014–FR-018. Phân biệt fixture, pilot Sốt–Chờ và full P0 theo danh mục 07/11/2026.
- Kiểm 16 liên kết nội bộ, đối chiếu danh sách P0 với spec, kích thước/trạng thái schema với feature_schema.json và phạm vi fixture với model_info.json mẫu. Các mục accuracy, precision/recall, Macro-F1, confusion matrix, latency, split FR-015, OOD, bias, khả năng giải thích, fallback và disclaimer đều có.
- Thay đổi tài liệu. Gate git diff --check và kiểm liên kết đạt. Kết quả smoke được dẫn từ evidence T036–T059 và T095. Các chỉ số thật chờ manifest đã audit, schema được duyệt và kết quả T058, T065, T089.
- Handoff P1/Huy review. P3 bổ sung modelVersion, datasetVersion, metric và minh chứng vào card khi có run đã audit.

**Reviewer result** PENDING

## Independent review — P1/Huy

Review `2026-11-07T22:18:19+07:00` trên `cedd013` (theo uỷ quyền của Huy).

| Kiểm tra | Kết quả |
|---|---|
| Đủ mục T062 | Lý do chọn GRU, protocol tái lập, artifact kind, nghĩa hỗ trợ, metric, confusion matrix, latency, split FR-015/OOD, bias, giới hạn giải thích, fallback, disclaimer: có đủ |
| Link | 13/13 link tương đối trỏ tới file đang track |
| Khẳng định đối chiếu | Fixture công bố Cảm ơn / Sốt / Giấy tờ khớp `model_info.json`; schema ghi `DRAFT_PENDING_LEAD_REVIEW` đúng; latency p95 4,73 s khớp evidence clip thật của P2 |
| Trung thực | Ghi rõ metric chờ dữ liệu, confidence chưa hiệu chuẩn, chưa xác định tổng quát sang người ký mới |

Ghi chú:

1. Mục tiêu pilot "Sốt, Chờ" lấy đúng từ T083 trong `tasks.md`, nhưng T083 **lỗi thời**: "Chờ" đã ra khỏi P0
   ngày 2026-11-07 và raw material mới không có thư mục "Chờ". Lead cần chốt lại cặp nghĩa pilot trong P0
   (sửa T083), sau đó card cập nhật theo.
2. Latency p95 4,73 s vượt SC-002 (≤ 3 s) — rủi ro đã nêu đúng trong card.

**Reviewer result**: `P1_VERIFIED` cho cấu trúc và nội dung hiện có. T062 giữ `[ ]` đến khi điền accuracy,
Macro-F1, precision/recall, confusion matrix và latency từ artifact đánh giá thật (T083/T058), rồi review lại.
