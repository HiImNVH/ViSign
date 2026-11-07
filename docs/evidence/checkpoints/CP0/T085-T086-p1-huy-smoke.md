# CP0 smoke evidence — Spec Kit và quy trình nhóm

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP0` |
| Task | `T085-T086` |
| Owner | `P1 Huy` |
| Reviewer | `P2 Tín` — review độc lập sau khi baseline có trên `origin/main` |
| Commit | Pending first push |
| Ngày/giờ | `2026-11-07T13:02:13+07:00` |
| Môi trường | Windows 11, PowerShell, Git, Spec Kit repository scripts |
| Status | `PASS` |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh: baseline Spec Kit, rubric mapping, checkpoint/member workflow và smoke
  evidence template nhất quán trước khi application code được nhập.
- File/module chính: `.agent/`, `.agents/`, `.specify/`, `specs/`, `docs/`, `members/`, `README.md`.
- Không thuộc phạm vi: source FE/BE/AI/data, dependency install, model artifact và cloud deployment.
- Version: release `0.0.1`, public API `v1`; feature schema v0.3 vẫn chờ representative-clip review.

## 3. Smoke test

| # | Mục tiêu | Command hoặc thao tác tái lập | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Spec Kit prerequisites | `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | Tìm thấy spec, plan và tasks | Feature directory và 5 design artifact được nhận diện, exit 0 | `PASS` |
| 2 | Spec/task format | Đếm FR, SC, task ID và kiểm regex checklist | 33 FR, 15 SC, 99 task duy nhất, 0 task sai | `FR=33 SC=15 TASKS=99 UNIQUE=99 BAD=0`, exit 0 | `PASS` |
| 3 | Spec Kit analyze | Đối chiếu `spec.md`, `plan.md`, `tasks.md` và constitution | Không có critical/high; requirement có task | Coverage 100%, critical 0, high 0, constitution PASS | `PASS` |
| 4 | API version contract | Kiểm `openapi.yaml` | OpenAPI 3.1.0, release 0.0.1, namespace `/api/v1` | Đúng cả ba giá trị, exit 0 | `PASS` |
| 5 | Git hygiene | `git diff --check`; `git diff --cached --check`; quét đuôi raw/model/secret | Không whitespace error hoặc artifact bị cấm | PASS; chỉ có cảnh báo chuyển LF→CRLF, exit 0 | `PASS` |

## 4. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | Pending first push | Bổ sung full SHA/link bằng commit evidence kế tiếp |
| GitHub Actions | `NOT_RUN` — workflow được tạo ở CP7/T091 | CP0 dùng local gates |
| Report trong repo | `docs/team/judging-criteria-mapping.md`; `docs/team/git-checkpoints.md` | Artifact CP0 |
| API/cloud | `NOT_RUN` — chưa thuộc CP0 | Không có application source/deploy |
| Data/model | `NOT_RUN` — chưa thuộc CP0 | Không có raw/model binary trong commit |

## 5. Rủi ro, rollback và handoff

- Rủi ro còn lại: direct-main cần tuân thủ integration queue; T098/T099 vẫn chờ input của lead.
- Rollback: revert riêng commit CP0; không rewrite hoặc force-push lịch sử.
- Việc người kế tiếp cần làm: P2 tái lập gate quan trọng sau push; CP1 chỉ mở sau xác nhận CP0.
- Blocker: không có blocker cho push CP0; independent reviewer verification diễn ra sau push.

## 6. Xác nhận

- [x] Owner đã chạy gate trên candidate tree trước commit.
- [x] Không có secret, raw video, landmark bulk hoặc model binary trong candidate tree.
- [ ] Full SHA và link sẽ được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

**Reviewer result**: `PENDING`

**Reviewer note**: Chờ baseline xuất hiện trên `origin/main`.
