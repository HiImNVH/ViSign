# P4 Quang - Data

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P4` |
| Current member | Quang |
| Role | Data collection, audit, manifest và dataset evidence |
| Canonical ownership | `data/`, `ai/dataset/`, `docs/dataset-card.md` |
| Allowed commit scopes | `data`, `dataset` |
| Current checkpoint | Chuẩn bị `CP2` |
| Integration window | Người dùng yêu cầu trực tiếp commit/push T008 trong phiên; không ghi nhận xác nhận thay Huy |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T098 / CP2` | `TODO` | data convention, manifest schema/tests | Lead đã gửi `docs/team/data-convention.md` (cập nhật mục 8: ánh xạ tên file của Quang, không cần signer/license từng video); xác nhận D1–D4 và 2 điểm mục 8 (vùng `O`, variant), tạo `p0-meanings.csv` theo danh sách chốt 2026-11-07 rồi đóng băng | P3/Cường và P1/Huy |
| `T008 / CP1` | `PUSHED` | `data/README.md`, evidence T008 | Hướng dẫn đã kiểm tra cục bộ; người dùng yêu cầu commit/push, chờ review độc lập của Huy/Cường | P1/Huy, P3/Cường |
| `T009-T013 / CP2` | `PLANNED` | dataset entities/schema/validator/coverage | Chuẩn bị phần không phụ thuộc T098 | P3/Cường |
| `T076-T077 / CP5` | `PLANNED` | pilot/full manifest và dataset card | Chờ raw material audit | P3/Cường và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T008 / CP1` — được người dùng yêu cầu commit/push |
| Proposed commit | `CP1 T008(data): clarify raw material intake and rights audit` |
| Exact staged paths | `data/README.md`, `members/p4-quang/README.md`, `docs/evidence/checkpoints/CP1/T008-p4-quang-smoke.md` |
| Pre-commit sync | Fetch origin/main; candidate dựng trên `3815e45`; gate chạy lại trên worktree riêng |
| Gate commands | link trong Git tree, ignore probes, `git diff --cached --check` |
| Smoke evidence | `docs/evidence/checkpoints/CP1/T008-p4-quang-smoke.md` |
| Local commit | [c034e6e421f3788fdb7ecbc90ab558476ae310b0](https://github.com/HiImNVH/ViSign/commit/c034e6e421f3788fdb7ecbc90ab558476ae310b0) |
| Pre-push sync | git pull --rebase origin main: up to date; diff --check PASS; origin/main...HEAD = 0 1 |
| Push status | PUSHED — T008 đã lên origin/main; independent review PENDING |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP1/T008` | Raw material intake/rights guidance | `CP1 T008(data): clarify raw material intake and rights audit` | c034e6e421f3788fdb7ecbc90ab558476ae310b0 | [Commit](https://github.com/HiImNVH/ViSign/commit/c034e6e421f3788fdb7ecbc90ab558476ae310b0) | PASS: tracked links, ignore probes, whitespace | P1/Huy, P3/Cường | PUSHED, review PENDING |
| `CP2/T098` | Freeze data naming/normalization | `CP2 T098(data): freeze dataset naming convention` | `PENDING` | `PENDING` | `NOT_RUN` | P3/Cường, P1/Huy | `BLOCKED` |

## Handoff

- Current risks: tự đặt quy ước trước khi lead bàn giao sẽ tạo drift dữ liệu.
- Required input: quy ước tên file, normalization và version do lead cung cấp.
- Next owner/action: Quang chuẩn bị inventory raw material nhưng chưa rename/bulk-process.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P1/Huy | P4/Quang | T098 giữ `BLOCKED` chờ data convention |
