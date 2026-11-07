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

## Independent review — P1/Huy

Review `2026-11-07T22:16:40+07:00` trên `0f3c557` (P1 review do trợ lý thực hiện theo uỷ quyền của Huy).

| Gate | Kết quả |
|---|---|
| `pytest ai/tests -q` | 75 passed, 5 skipped (thiếu fixture clip local) |
| Ruff, mypy | PASS (26 files) |
| Probe `passes_release_gate` | PASS đúng ngưỡng Macro-F1 0,80 / recall 0,65; FAIL với Macro-F1 0,79, recall 0,64, pilot đạt 100%, 9 nghĩa, mode `session`, 0 mẫu test, `macroF1=True` |
| Probe `build_model_metadata` | Chặn `--approve-demo` khi không có báo cáo đánh giá |

Đạt: `demoReady=true` cần đồng thời **gate full** và **phê duyệt lead tường minh** (`--approve-demo`);
trước khi ghi kiểm provenance (SHA-256 weights, manifest, schema `APPROVED`, split audit theo
`recordingSessionId`), ghi `model_info.json` nguyên tử.

Ghi chú không chặn:

1. `passes_release_gate` chấp nhận mode `signer-held-out` nhưng `update_model_metadata` chỉ nhận
   `groupedBy == recordingSessionId` → đường signer chưa ghi được metadata. Đủ cho MVP (FR-015 dùng video
   gốc); thống nhất lại nếu sau này có `signerId`.
2. Lệnh ghi đè `model_info.json` trong thư mục artifact sau khi train; nếu sau này thêm manifest checksum
   cho artifact (đóng gói/xuất bản) thì phải tạo lại checksum sau bước này.

**Reviewer result**: `P1_VERIFIED` → T059 `[X]`.
