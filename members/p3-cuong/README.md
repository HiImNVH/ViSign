# P3 Cường - AI/Training/Evaluation

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P3` |
| Current member | Cường |
| Role | AI preprocessing, training và evaluation |
| Canonical ownership | `ai/landmarks/`, `ai/training/`, `ai/evaluation/` |
| Allowed commit scopes | `ai`, `extractor`, `train`, `eval`, `model` |
| Current checkpoint | `CP1 review`, chuẩn bị `CP2` |
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T003 / CP1` | `REVIEW` | `ai/pyproject.toml` do Tín tạo | Review dependency/toolchain AI | P1/Huy |
| `T014-T017 / CP2` | `PLANNED` | decoder, extractor, transform, CLI/tests | Review representative WebM trước khi APPROVED schema v0.3 `32×234` | P2/Tín và P1/Huy |
| `CP5` | `PLANNED` | training/evaluation/artifact reports | Chờ manifest Quang bàn giao | P4/Quang và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | Chưa có commit active; hiện chỉ review T003 |
| Proposed commit | `CP2 T014-T016(extractor): add shared WebM feature pipeline` |
| Exact staged paths | `PENDING` sau khi CP2 mở |
| Pre-commit sync | `PENDING` |
| Gate commands | decoder fixtures, tensor/mask parity, extractor schema/hash tests |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `BLOCKED` — chờ CP2 window và schema review |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T014-T016` | Shared WebM feature pipeline | `CP2 T014-T016(extractor): add shared WebM feature pipeline` | `PENDING` | `PENDING` | `NOT_RUN` | P2/Tín, P1/Huy | `PLANNED` |

## Handoff

- Current risks: feature schema v0.3 chưa được APPROVED; không được bulk-extract trước review.
- Required input: representative WebM clips và data manifest đã audit.
- Next owner/action: review T003; sau đó chờ Huy mở CP2.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P2/Tín | P3/Cường | Review AI toolchain T003 |
