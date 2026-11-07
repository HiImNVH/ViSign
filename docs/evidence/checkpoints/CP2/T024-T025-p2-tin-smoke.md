# CP2 T024–T025 smoke evidence — clip tạm luôn bị xóa

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP2` |
| Task | `T024-T025` |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy` |
| Candidate commit | `CP2 T024-T025(api): guarantee temporary clip deletion on every path` |
| Commit | `e3c5d8ae57e8ec33a956bb13a0bcb87c39845d30` — [e3c5d8a](https://github.com/HiImNVH/ViSign/commit/e3c5d8ae57e8ec33a956bb13a0bcb87c39845d30); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42357998638) |
| Ngày/giờ | `2026-11-07T15:56:35+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15 |
| Status | `PASS` local và CI; chờ reviewer verify |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh (FR-011, hiến pháp IV): bytes clip upload được ghi ra file tạm `visign_clip_*.webm`
  và file luôn bị xóa khi thoát context — thành công, exception, `BaseException` (ngắt/hủy), ghi file
  hỏng; xóa idempotent; nếu hệ điều hành từ chối xóa thì log `ERROR` kèm traceback, không raise để không
  che lỗi gốc, và message không chứa đường dẫn file.
- File: `services/inference-api/src/visign_api/inference/temporary_clip.py`,
  `services/inference-api/tests/unit/test_temporary_clip.py`.
- Nguồn tham khảo legacy `backend` `b708c72`. Khác legacy: hàm tối đa 2 tham số (đuôi `.webm` cố định vì API
  chỉ nhận WebM); thư mục do người gọi truyền thay vì đọc biến global `settings`; lỗi xóa log `ERROR`
  thay vì `WARNING`; `TemporaryClip` là dataclass bất biến, bỏ `size_bytes` chưa dùng.
- Không thuộc phạm vi: endpoint gọi context (T038/T050), thư mục tạm cấu hình qua env (thêm khi T026/T095 cần).

## 3. Pre-commit synchronization

- Remote tiến tới `5ab1b97` (P1 đổi spec T013/T098, không chạm file candidate): stash/pull/apply, so nội dung
  không lệch; gate chạy lại lúc `2026-11-07T16:02:04+07:00`: 110 passed, Ruff/format/mypy đạt.
- `origin/main...HEAD` = `0 0` tại `5ab1b97`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `pytest services/inference-api/tests/unit/test_temporary_clip.py -q` trước khi có module | Fail | 1 collection error | `PASS` |
| 2 | GREEN | Cùng command | 7 test đạt | 7 passed | `PASS` |
| 3 | Độc lập thứ tự | Chạy riêng; trước và sau `test_observability.py` | Đều đạt | 7 / 24 / 24 passed | `PASS` |
| 4 | Bắt hồi quy | Đổi `finally` thành chỉ xóa khi thành công; hạ log `ERROR` → `WARNING` | Fail | 4 failed; 1 failed; khôi phục giống hệt | `PASS` |
| 5 | Toàn bộ API + contract | `pytest services/inference-api/tests tests/contract -q -W error` ×3; Ruff; format check; `python -m mypy` | Không lỗi | 110 passed ×3; Ruff/format đạt; mypy 20 files | `PASS` |
| 6 | Git hygiene | `git diff --cached --check`; quét file bị cấm | Không lỗi | exit 0; không có file bị cấm/secret trong 4 path staged | `PASS` |

Ghi chú quá trình: phiên bản test đầu dùng `caplog` cho kết quả phụ thuộc thứ tự (2 bản ghi khi logger bật
`propagate`); đã xác nhận `delete` chỉ chạy một lần và chuyển sang handler ghi nhận gắn trực tiếp vào logger.

## 5. Rủi ro và handoff

- Trên Windows, file đang mở bởi tiến trình khác không xóa được; trường hợp này chỉ còn log `ERROR`. T066
  (privacy audit) và T092 nên kiểm thư mục tạm sau chạy tải.
- Rollback: `git revert` riêng commit này.

**Reviewer result**: `PENDING`
