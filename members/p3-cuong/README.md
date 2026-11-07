# P3 Cường - AI/Training/Evaluation

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P3` |
| Current member | Cường |
| Role | AI preprocessing, training và evaluation |
| Canonical ownership | `ai/landmarks/`, `ai/training/`, `ai/evaluation/` |
| Allowed commit scopes | `ai`, `extractor`, `train`, `eval`, `model` |
| Current checkpoint | `CP2` · kiểm thử cục bộ |
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T003 / CP1` | `REVIEW` | `ai/pyproject.toml` do Tín tạo | Review dependency/toolchain AI | P1/Huy |
| `T014-T016 / CP2` | `REVIEW` | decoder, extractor, transform, schema và tests | Gate cục bộ đạt. Chờ review clip đại diện và parity qua adapter T037 | P2/Tín và P1/Huy |
| `T017 / CP2` | `PLANNED` | CLI trích landmark theo manifest | Bước kế tiếp sau pipeline chung | P2/Tín và P1/Huy |
| `CP5` | `PLANNED` | training/evaluation/artifact reports | Chờ manifest Quang bàn giao | P4/Quang và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `CP2 / T014-T016` · candidate cục bộ |
| Proposed commit | `CP2 T014-T016(extractor): add shared WebM feature pipeline` |
| Exact staged paths | `ai/configs/`, `ai/setup_models.py`, `ai/src/visign_ai/landmarks/`, `ai/tests/landmarks/`, evidence CP2 và README P3 |
| Pre-commit sync | `PENDING` |
| Gate commands | Pytest AI (20 pass), Ruff, mypy. Parity API còn chờ T037 |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `BLOCKED` — chờ CP2 window và schema review |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T014-T016` | Shared WebM feature pipeline | `CP2 T014-T016(extractor): add shared WebM feature pipeline` | `PENDING` | `PENDING` | `PASS` cục bộ | P2/Tín, P1/Huy | `REVIEW` |

## Handoff

- Current risks: feature schema v0.3 chưa được APPROVED; không được bulk-extract trước review.
- Required input: representative WebM clips và data manifest đã audit.
- Next owner/action: Tín review pipeline và nối đường serving. Huy xác nhận lượt tích hợp và review clip đại diện.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P2/Tín | P3/Cường | Review AI toolchain T003 |
