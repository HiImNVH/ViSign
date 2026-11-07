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
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T098 / CP2` | `BLOCKED` | data convention, manifest schema/tests | Chờ lead gửi quy ước tên và chuẩn hóa file | P3/Cường và P1/Huy |
| `T009-T013 / CP2` | `PLANNED` | dataset entities/schema/validator/coverage | Chuẩn bị phần không phụ thuộc T098 | P3/Cường |
| `T076-T077 / CP5` | `PLANNED` | pilot/full manifest và dataset card | Chờ raw material audit | P3/Cường và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T098 / CP2` — chưa active |
| Proposed commit | `CP2 T098(data): freeze dataset naming convention` |
| Exact staged paths | `docs/contracts/data-conventions.md`, validator/tests và member/evidence files |
| Pre-commit sync | `PENDING` |
| Gate commands | filename/manifest validator, valid/invalid fixture tests, `git diff --cached --check` |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T098-p4-quang-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `BLOCKED` — chờ lead input và CP2 window |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
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
