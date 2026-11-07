# Quy trình checkpoint commit/push trên `main`

## Mục tiêu

Tạo lịch sử nhỏ, có thể review và rollback; không branch theo thành viên, không full-code dump.

## Integration queue

Huy ghi thứ tự owner/checkpoint trong `docs/team/implementation-status.md`. Chỉ owner đang có window
mới được push. Các thành viên khác có thể làm local nhưng chờ window, sau đó rebase và rerun gate.

## Quy ước commit chung

Mỗi commit chỉ có **một owner chính**, một kết quả có thể kiểm thử và tối đa một nhóm task liên quan
trực tiếp. Owner phải cập nhật member log và smoke evidence trong cùng commit với source/config/docs
mà bằng chứng đó xác nhận.

```text
CP<0-8> T<task hoặc dải task>(<scope>): <kết quả ở thể mệnh lệnh>
```

Ví dụ hợp lệ:

```text
CP2 T019-T021(api): add versioned health and error contract
CP3 T033-T036(train): add reproducible pilot training pipeline
CP4 T051-T053(web): handle retry and HTTP status placeholders
```

Quy tắc:

- Dòng đầu tối đa 72 ký tự, dùng tiếng Anh không dấu để log/tool đọc ổn định.
- `CPx` và task ID phải khớp `tasks.md`; không dùng `misc`, `update`, `final` làm scope/kết quả.
- Một commit không trộn owner hoặc module độc lập. Pair work vẫn chọn một owner; người còn lại ghi
  `Co-authored-by` và review/handoff trong evidence.
- Commit docs/evidence phát sinh từ một thay đổi phải đi cùng thay đổi đó. Báo cáo tổng hợp độc lập
  dùng scope `verify` hoặc `docs`.
- Không amend commit đã push. Sửa bằng commit nhỏ mới, ví dụ
  `CP3 T038(api): fix predictor cleanup on timeout`.

## Scope và checkpoint của từng thành viên

| Thành viên | Scope được dùng | Checkpoint/commit dự kiến | Smoke tối thiểu | Reviewer chính |
|---|---|---|---|---|
| P1 Huy | `spec`, `docs`, `ci`, `verify`, `release` | CP0 Spec Kit; CP3/4 E2E; CP7 CI; CP8 nghiệm thu | Spec Kit validation; E2E/rehearsal; link Actions | Owner module liên quan; cả nhóm ở CP8 |
| P2 Tín | `api`, `backend`, `security`, `cloud` | CP1 monorepo/toolchain T001–T007; CP2 contract; CP3 predictor; CP4 errors/security; CP6 admin API; CP7 cloud | unit/contract; live health/predict; negative/security; Cloud Run health/rollback | Huy; Cường cho predictor; Hiển cho API contract |
| P3 Cường | `ai`, `extractor`, `train`, `eval`, `model` | CP1 review T003; CP2 preprocessing/schema; CP3 fixture/predictor; CP5 pilot rồi full; CP7 cost | tensor/mask parity; deterministic train; model load/predict; metrics/cost | Huy; Tín cho serving; Quang cho manifest |
| P4 Quang | `data`, `dataset` | CP1 data skeleton; CP2 convention/schema; CP5 pilot/full manifest | schema/filename validator; provenance/license audit; split/coverage audit | Huy và Cường |
| P5 Hiển | `web`, `ui`, `ux`, `e2e` | CP1 review T004/T006; CP2 API client/types; CP3 happy path; CP4 placeholders/accessibility; CP6 admin UI; CP8 UX evidence | lint/build/unit; fake-camera E2E; status/accessibility/responsive checks | Huy và Tín |

Một người có thể có nhiều commit trong một CP, nhưng mỗi commit phải độc lập review/rollback. Không
chờ đến cuối CP mới dồn toàn bộ thay đổi của người đó vào một commit.

## Quy trình bắt buộc cho mỗi checkpoint

```powershell
git switch main
git pull --rebase origin main
git status --short
```

1. Chỉ sửa file thuộc task và canonical ownership; cập nhật `members/<owner>/README.md`.
2. Chạy gate, ghi command/result/skip reason; kiểm tra không có secret/raw/model binary.
3. Stage đúng path, không dùng `git add .` khi worktree có thay đổi ngoài task.

```powershell
git add -- <exact-paths>
git diff --cached --check
git diff --cached --stat
git commit -m "CPx Txxx(scope): concise outcome"
```

4. Ngay trước push, đồng bộ lần cuối. Nếu rebase đổi source, chạy lại gate bị ảnh hưởng.

```powershell
git pull --rebase origin main
# rerun affected checkpoint gate
git push origin main
```

5. Ghi full commit SHA và handoff vào member log. Reviewer chạy gate độc lập rồi đổi status
thành `VERIFIED`.

6. Tạo/cập nhật smoke evidence theo
[`checkpoint-evidence-template.md`](checkpoint-evidence-template.md) tại đường dẫn:

```text
docs/evidence/checkpoints/CPx/Txxx-<owner>-smoke.md
```

Chỉ ghi `PASS` khi có command, exit code/kết quả, môi trường và link/path bằng chứng. `NOT_RUN` phải
có lý do; gate bắt buộc bị `FAIL`, `BLOCKED` hoặc `NOT_RUN` thì không được push/đóng checkpoint.

## Cấm

- `git push --force`, `--force-with-lease`, reset lịch sử remote.
- Commit raw video, landmark bulk, model weights, `.env`, token hoặc cloud credential.
- Gộp nhiều checkpoint độc lập vào một commit full code.
- Push khi member khác đang giữ integration window.
- Đánh dấu task `[x]` chỉ vì code có trong legacy repo hoặc máy cá nhân.

## Checkpoint gates

| CP | Task/artifact chính | Gate trước push | Cách chia commit |
|---|---|---|---|
| CP0 | Spec Kit, rubric, `members/`, Git rules | task-format, prerequisites, Spec Kit analyze | Một docs-only commit sau lead duyệt |
| CP1 | T001–T008 | install, lint, empty/unit smoke, web build | Setup theo module, không application dump |
| CP2 | T009–T028, T098–T099 | dataset schema, extractor, API contract/type tests | 3–5 commit data/AI/API/web |
| CP3 | T029–T043 | unit/contract + happy-path fake-camera E2E | AI, API, web, E2E riêng |
| CP4 | T044–T053, T063–T066, T072–T075, T089/T092 liên quan | negative E2E, privacy, routing, security | Backend/frontend/security riêng |
| CP5 | T054–T062, T065, T076–T077, T083, T089, T094 | split audit, reproducible eval, quality/cost | Pilot và full là hai checkpoint |
| CP6 | T078–T084 | admin auth/cleanup/concurrency/UI tests | Không deploy admin production |
| CP7 | T085–T096 | CI green, reports, cloud smoke/rollback | Deploy chỉ sau quality commit |
| CP8 | T067–T071, T097 | full quickstart, usability, rubric, rehearsal/Q&A | Evidence only, no feature dump |

## Chính sách smoke test và link bằng chứng

- Mỗi micro-commit chạy test liên quan trực tiếp; commit đóng CP chạy full smoke của checkpoint.
- Link chính phải bền vững: commit SHA trên GitHub, file/report trong repo, GitHub Actions run và
  Cloud Run revision/URL công khai. Không dùng signed URL hết hạn, token hoặc đường dẫn chỉ tồn tại
  trên máy cá nhân làm bằng chứng duy nhất.
- Với model/data, ghi version, manifest/schema, SHA-256 artifact và report; không đưa binary/raw data
  vào Git.
- Với API, ít nhất ghi `/api/v1/health`, contract/type tests và các status liên quan thay đổi.
- Với web, ít nhất ghi lint, build, unit/component hoặc E2E liên quan; screenshot chỉ bổ trợ, không
  thay test result.
- Reviewer phải mở được link từ tài khoản repo bình thường và ghi `VERIFIED`; link hỏng trả evidence
  về `BLOCKED`.

## Contract freeze gate

CP2 bị chặn ở bước đóng checkpoint cho đến khi:

- T098: lead bàn giao data filename/normalization convention.
- T099: lead bàn giao FE-BE API convention.
- AI–backend contract v0.0.1 đã được Cường và Tín xác nhận; schema v0.3 chỉ APPROVED sau representative-clip review.
