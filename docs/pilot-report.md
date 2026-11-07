# T083 · Review độc lập pilot Giấy tờ / Nhận

P3/Cường chạy lại đánh giá CPU từ gói Quang bàn giao ngày 2026-11-08, baseline repo `b2bb2d5`. Gói dùng dataset `pilot-v2`, model `t083-pilot-v2-approved`, schema v0.3 được Huy duyệt tại `a255a7c` và ngưỡng chấp nhận 0,5. W&B của lần train gốc là `kbj3bpvu` (offline).

## Kết quả kiểm tra

- `tools/verify_package.py`: 292/292 tệp khớp SHA-256.
- `tools/review_t083.py --evaluate --output <thư-mục-mới>`: kiểm 15 video, 15 tensor NPZ hữu hạn dạng 32×234 và đối chiếu hash của manifest, schema và weights trước khi đánh giá. Accuracy, macro-F1, precision/recall, ma trận nhầm lẫn và split audit khớp báo cáo của Quang.
- 15 clip, 4 lớp, chia 7 train / 4 validation / 4 test. Audit tách theo `recordingSessionId` đạt với 13 session. Cả 4 mẫu test thiếu `signerId`, nên kết quả chỉ có phạm vi `video-held-out`.

| Nghĩa thật | Test | Dự đoán Giấy tờ | Dự đoán Nhận | Từ chối | Recall |
|---|---:|---:|---:|---:|---:|
| Giấy tờ | 2 | 0 | 0 | 2 | 0% |
| Nhận | 2 | 1 | 1 | 0 | 50% |

**Accuracy 25% (1/4), macro-F1 0,3333, `demoReady=false`.** Đây là kết quả đánh giá lại weights đã bàn giao, với đúng tập test của pilot.

| Thành phần | SHA-256 |
|---|---|
| Manifest pilot-v2 | `0a6b1402d3e8cbcdccface08a58c5550f581c82efb1f791b96d8bb24b7260d92` |
| Schema digest | `6f1e32eeb8be9e6fbf3e13f7dded063ad9b4ea7ad387593ddfb658c66d92c389` |
| Weights | `0c9a991bb95a90cac433470adf3f1640ac520461d9da86459243c5df7a27c252` |

Huy đã chốt ngày 2026-11-08: phạm vi pilot [T083](../specs/001-vsl-recognition-mvp/tasks.md) là Giấy tờ / Nhận. T076 chờ P4 ghi đúng `sourceUri` từng clip (bộ dữ liệu gồm cả video giáo dục công khai và video tự quay; manifest hiện ghi cả 15 là `dataset:self-recorded`). T083 giữ mở đến khi có nghiệm thu T078–T082 cho luồng admin. Kết quả trên bốn mẫu test chỉ dùng làm bằng chứng pilot nội bộ.
