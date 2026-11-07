# CP5 T059 · P3/Cường

Owner P3/Cường. Review P1/Huy và P2/Tín.

## Cách chạy

Sau khi có artifact T036 và báo cáo T058, ghi số đo vào model_info.json trong artifact local.

```powershell
uv run --locked --project ai python -m visign_ai.evaluation.release_gate --artifact "PATH/pilot-gru-v1" --report "PATH/pilot-eval-v1/evaluation-report.json"
```

- Fixture không cần báo cáo và giữ metrics null. Pilot và full cần báo cáo khớp phiên bản, schema, trọng số, manifest và audit tách video gốc. Thứ tự lớp, chữ hiển thị và ngưỡng từ validation được giữ nguyên.
- Báo cáo T058 cũ thiếu weightsSha256 phải tạo lại bằng CLI evaluate mới. Trọng số và manifest cũ vẫn dùng được.
- Mặc định demoReady=false. Sau khi Huy duyệt phát hành, với full thêm --p0-meanings "PATH/p0-meanings.csv" --approve-demo. CSV cần cột meaningId với đúng 10 nghĩa P0. Điều kiện là Macro-F1 ≥ 0.80, recall từng nghĩa ≥ 0.65, đủ mẫu test mỗi nghĩa và audit FR-015 đạt.
- CLI thay metadata nguyên file sau khi kiểm tra xong. Lỗi đầu vào giữ nguyên metadata hiện có.

## Gate cục bộ

| Gate | Kết quả |
|---|---|
| python -m ruff check --no-cache ai | PASS |
| python -m mypy ai/src ai/tests | PASS · 26 file |
| python -m pytest ai/tests -q -rs | 79 passed, 1 skipped do quyền symlink trên Windows |
| python -m pytest services/inference-api/tests tests/contract -q -rs | 332 passed, 2 skipped do thiếu serving extra và MediaPipe trong môi trường API |

Test tổng hợp kiểm writer từ artifact T036 và report T058, chặn báo cáo lệch trọng số, chặn fixture/pilot qua full gate và kiểm full đủ điểm chỉ bật readiness khi có cờ duyệt. Chưa có điểm đánh giá VSL thật hoặc phê duyệt phát hành.

**Reviewer result** PENDING
