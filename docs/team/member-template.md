# Pn Name - Role

> File này là nhật ký task/commit/handoff. Source code luôn nằm trong canonical module, không sao
> chép vào `members/`.

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P1`–`P5` |
| Current member | `[name]` |
| Role | `[role]` |
| Canonical ownership | `[paths/responsibility]` |
| Allowed commit scopes | `[scope trong git-checkpoints.md]` |
| Current checkpoint | `CP0`–`CP8` |
| Integration window | `WAITING` / `ACTIVE` / `CLOSED` |
| Last updated | `YYYY-MM-DD` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `TXXX / CPx` | `TODO` | `path/` | Một hành động có thể kiểm chứng | `Pn` |

## Commit đang chuẩn bị

Mỗi lần chỉ giữ một dòng `ACTIVE`. Xóa giá trị mẫu sau khi điền; không dùng `git add .`.

| Field | Value |
|---|---|
| Task/checkpoint | `TXXX / CPx` |
| Proposed commit | `CPx Txxx(scope): outcome` |
| Exact staged paths | `path/a`, `path/b`, member README và smoke evidence |
| Pre-commit sync | `PENDING` hoặc timestamp + `origin/main` SHA đã fetch/rebase |
| Gate commands | Lệnh lint/test/build/contract liên quan |
| Smoke evidence | `docs/evidence/checkpoints/CPx/Txxx-<owner>-smoke.md` |
| Local commit | `PENDING` hoặc short SHA |
| Pre-push sync | `PENDING` hoặc timestamp + kết quả `git pull --rebase origin main` |
| Push status | `NOT_PUSHED` / `PUSHED` / `VERIFIED` / `BLOCKED` |

## Commit ledger

Không sửa hoặc xóa dòng lịch sử. Full SHA và GitHub link được bổ sung sau push bằng evidence commit.

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CPx/TXXX` | Kết quả nhỏ, rollback được | `CPx Txxx(scope): outcome` | `PENDING` | `PENDING` | `NOT_RUN` | `Pn` | `PLANNED` |

## Handoff

- Current risks: None recorded.
- Required input: None recorded.
- Next owner/action: `[person/action]`.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| YYYY-MM-DD | — | `[name]` | Initial assignment |
