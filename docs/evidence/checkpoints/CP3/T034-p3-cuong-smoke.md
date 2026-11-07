# CP3 T034 · P3/Cường

Baseline origin/main: d258baf666eeeffebf8d3cbdb0290c9bfca3029c. Candidate LOCAL-DRAFT, chờ push và review P1/Huy, P2/Tín.

- SequenceDataset nhận các dòng đã chọn từ manifest với sampleId, classLabel và landmarkPath tương đối. Caller chọn split và cung cấp class map có thứ tự. Loader giữ nguyên chỉ số theo class map và báo lỗi lớp ngoài phạm vi.
- Đọc NPZ theo từng mẫu, kiểm sampleId, feature schema, extractor version, schema SHA-256, tensor float32 hữu hạn và tính nhất quán giữa hai cách lưu mask. Giữ đủ 32 bước của schema v0.3, kể cả bước thiếu landmark. Collate chỉ pad cuối chuỗi khi cần và trả features, lengths, targets.
- Đối chiếu loader cũ ở 7nghiep367 commit 267419b, ai/src/visign_ai/training/sequence_dataset.py. Giữ tuple features/label và pad_sequence, đổi sang đọc theo mẫu và kiểm NPZ theo đầu ra T017 của repo mới.

| Gate cục bộ | Kết quả |
|---|---|
| NPZ tổng hợp tạo bằng writer T017 → DataLoader → GRU | PASS · giữ class map và batch order |
| Pytest toàn AI có fixture browser/detector | 55 passed, 1 skipped vì quyền tạo symlink trên Windows. Gồm 12 test T034 |
| Pytest API và contract | 179 passed, 1 skipped |
| Ruff và mypy AI | PASS |

Chưa chạy manifest hoặc train chính thức. Bước tiếp theo là T035 cấu hình pilot/full, rồi T036 nối manifest và training CLI.
