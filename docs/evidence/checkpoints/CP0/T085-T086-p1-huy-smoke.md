# CP0 smoke evidence — Spec Kit và quy trình nhóm

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP0` |
| Task | `T085-T086` |
| Owner | `P1 Huy` |
| Reviewer | `P2 Tín` — review độc lập sau khi baseline có trên `origin/main` |
| Commit | `5102bbbbe7efcf327a64477051bfc6137e9b5bce` |
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
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/5102bbbbe7efcf327a64477051bfc6137e9b5bce` | CP0 baseline trên `origin/main` |
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
- [x] Full SHA và link đã được điền sau push.
- [x] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

**Reviewer result**: `VERIFIED`

**Reviewer note**: P2 Tín tái lập độc lập ngày `2026-11-07` trên `origin/main` =
`22226b25d17e70ce48b153914d7eee1e15e8d3f4` (gồm baseline `5102bbb` và commit evidence), Windows 11,
Windows PowerShell 5.1, Git Bash, Python có PyYAML.

| # | Gate | Command/thao tác reviewer | Kết quả | Trạng thái |
|---|---|---|---|---|
| 1 | Prerequisites | `powershell -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` với `SPECIFY_FEATURE_DIRECTORY=specs/001-vsl-recognition-mvp` | Nhận diện `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`; exit 0 | `PASS` |
| 2 | Spec/task format | Regex đếm `**FR-nnn**`, `**SC-nnn**`, `- [ ] Tnnn [P]? [USn]? ...` | `FR=33 SC=15 TASKS=99 UNIQUE=99 BAD=0`, dải T001–T099, 0 checkbox đã đóng | `PASS` |
| 3 | Analyze | Đối chiếu ngữ nghĩa spec↔tasks↔constitution; script kiểm owner và link nội bộ | 32/32 FR cần task có ≥1 task (FR-017 là loại trừ phạm vi), 15/15 SC có task; không có CRITICAL/HIGH | `PASS` |
| 4 | OpenAPI | `yaml.safe_load` + kiểm `openapi`, `info.version`, paths, `$ref` | `3.1.0`, `0.0.1`, 3 path `/api/v1/*` không trailing slash, 12/12 `$ref` resolve | `PASS` |
| 5 | Git hygiene | `git diff --check <empty-tree> HEAD`; quét đuôi raw/model/secret, file >1 MB, pattern credential | exit 0; không có file bị cấm/lớn; chỉ trúng placeholder `'<local-token>'` trong `quickstart.md`; lịch sử tuyến tính 2 commit, subject ≤72 ký tự | `PASS` |

Ghi chú không chặn CP0, chuyển Huy xử lý trước/trong CP1:

- `MEDIUM` T001–T007 chưa có owner trong bảng phân công `tasks.md`; cần gán trước khi mở CP1.
- `MEDIUM` T090 xuất hiện ở cả P1 và P5, trái quy ước "đúng một người chịu trách nhiệm chính".
- `LOW` 4 link nội bộ hỏng trỏ tới evidence legacy: `docs/verification/ai-backend-handoff.json`,
  `docs/verification/tin-integration-next-step.json` (trong `ai-backend-contract.md` và
  `training-models.md`) và `docs/performance-report.md`.
- `LOW` `.agent/core.md` §11.2 (Conventional Commits, mô tả tiếng Việt không dấu) khác
  `git-checkpoints.md` (`CPx Txxx(scope)`, tiếng Anh); nên ghi rõ quy ước dự án ghi đè.
- `INFO` OpenAPI chưa có `ROUTE_NOT_FOUND`/`METHOD_NOT_ALLOWED`; đúng kỳ vọng vì thuộc T073.
