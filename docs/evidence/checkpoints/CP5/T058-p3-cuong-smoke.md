# CP5 T058 · P3/Cường

Owner P3/Cường. Reviewer P1/Huy và P4/Quang. Candidate kiểm thử trên baseline 18a7f60 sau khi đồng bộ lại.

## Cách chạy

Từ thư mục gốc repo, dùng thư mục artifact tạo bởi T036, manifest đúng bản đã train và thư mục chứa tensor NPZ của tập test. Đặt output là thư mục mới.

```powershell
uv run --locked --project ai python -m visign_ai.evaluation.evaluate --artifact "PATH/pilot-gru-v1" --manifest "PATH/pilot.csv" --feature-root "PATH/dataset" --output "PATH/pilot-eval-v1"
```

- evaluation-report.json ghi metric theo nghĩa, phiên bản model/dataset/schema/extractor, hash manifest/schema và audit split theo video gốc. Chỉ ghi signer-held-out khi mọi mẫu có mã người ký và các split không chung người ký.
- confusion-matrix.png có cột riêng cho mẫu dưới ngưỡng. Dự đoán dùng lớp xác suất cao nhất rồi ánh xạ sang nghĩa, theo thứ tự lớp và ngưỡng đã lưu từ T036.
- Latency đo GRU forward, softmax và chọn lớp trên tensor đã nạp. Không bao gồm giải mã video, MediaPipe hoặc thời gian web/API.
- CLI chỉ đọc NPZ test. Báo cáo giữ demoReady=false. T059 tiếp nhận báo cáo để ghi metadata sau khi kiểm tra cổng full.

## Gate cục bộ

| Gate | Kết quả |
|---|---|
| python -m ruff check --no-cache ai | PASS |
| python -m mypy ai/src ai/tests | PASS · 26 file |
| python -m pytest ai/tests -q -rs | 77 passed, gồm 2 test T058. 1 skipped do quyền tạo symlink Windows |
| python -m pytest services/inference-api/tests tests/contract -q -rs | 332 passed. 2 skipped do môi trường API thiếu serving extra và MediaPipe |

Test tích hợp tạo artifact GRU từ tensor tổng hợp, xoá NPZ train/validation trước khi chạy evaluate, kiểm JSON và PNG, chặn ghi đè và chặn manifest khác hash. Test split kiểm video gốc trùng giữa hai tập và phân biệt video-held-out với signer-held-out. Chưa chạy đánh giá trên dữ liệu dự án.

**Reviewer result** PENDING
