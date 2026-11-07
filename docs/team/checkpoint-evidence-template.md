# Mẫu smoke test và bằng chứng checkpoint

Sao chép file này thành
`docs/evidence/checkpoints/CPx/Txxx-<owner>-smoke.md`. Không sửa trực tiếp template để ghi kết quả
của một lần chạy.

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CPx` |
| Task | `Txxx` hoặc `Txxx-Tyyy` |
| Owner | `P1 Huy` / `P2 Tín` / `P3 Cường` / `P4 Quang` / `P5 Hiển` |
| Reviewer | Tên người review độc lập |
| Commit | Full SHA + link GitHub |
| Ngày/giờ | ISO 8601 + múi giờ, ví dụ `2026-11-07T20:30:00+07:00` |
| Môi trường | OS, runtime/browser/device cần thiết để tái lập |
| Status | `PASS` / `FAIL` / `BLOCKED` / `NOT_RUN` |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh:
- File/module chính:
- Không thuộc phạm vi:
- Dependency/contract/version: release `0.0.1`, API `v1`, schema/model/data nếu liên quan.

## 3. Smoke test

| # | Mục tiêu | Command hoặc thao tác tái lập | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Static gate | `<command>` | Không lỗi | `<summary>, exit 0` | `PASS` |
| 2 | Unit/contract | `<command>` | Test liên quan đạt | `<passed/failed>, exit n` | `PASS/FAIL` |
| 3 | Runtime smoke | `<command/steps>` | Luồng chính hoạt động | `<HTTP/UI/model result>` | `PASS/FAIL` |
| 4 | Negative/cleanup | `<command/steps>` | Lỗi đúng contract, không rò dữ liệu | `<status/error/cleanup>` | `PASS/FAIL` |

Nếu không áp dụng một dòng, ghi `NOT_RUN` và lý do cụ thể. Không xóa dòng để che phần chưa chạy.

## 4. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/<sha>` | Bắt buộc sau push |
| GitHub Actions | `<run URL hoặc NOT_RUN + lý do>` | Bắt buộc khi workflow đã tồn tại |
| Report trong repo | `<relative path>` | Log tóm tắt, test/report/ảnh cần thiết |
| API/cloud | `<HTTPS URL + revision>` | Không chứa token/signed query |
| Data/model | `<version, manifest/schema, SHA-256, report path>` | Không commit raw/binary bị cấm |

## 5. Rủi ro, rollback và handoff

- Rủi ro còn lại:
- Cách rollback hoặc artifact/revision ổn định gần nhất:
- Việc người kế tiếp cần làm:
- Blocker (nếu có):

## 6. Xác nhận

- [ ] Owner đã chạy lại gate sau lần rebase cuối.
- [ ] Không có secret, raw video, landmark bulk hoặc model binary bị stage.
- [ ] Full SHA và link đã được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

**Reviewer result**: `PENDING` / `VERIFIED` / `CHANGES_REQUESTED` / `BLOCKED`

**Reviewer note**: `<command/link/kết luận>`
