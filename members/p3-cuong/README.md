# P3 Cường - AI/Training/Evaluation

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P3` |
| Current member | Cường |
| Role | AI preprocessing, training và evaluation |
| Canonical ownership | `ai/landmarks/`, `ai/training/`, `ai/evaluation/` |
| Allowed commit scopes | `ai`, `extractor`, `train`, `eval`, `model` |
| Current checkpoint | `CP2` · T014–T016 đã push, schema chờ review clip |
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T003 / CP1` | `VERIFIED` | `ai/pyproject.toml` do Tín tạo | Ruff, mypy và 8 import đạt. Pytest 15 passed, 5 skipped. [Review độc lập](../../docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md#independent-review--p3cường) | P3/Cường |
| `T014-T016 / CP2` | `REVIEW` | decoder, extractor, transform, schema và tests | Đã push, gate cục bộ đạt. Chờ review clip đại diện và parity qua adapter T037 | P2/Tín và P1/Huy |
| `T017 / CP2` | `VERIFIED` | CLI trích landmark từ danh sách sampleId/rawPath | D1–D4 đã xác nhận cùng Quang. CI xanh. Test tự động đã push ở 57311bf, 13 pass/1 skip local; Huy/Tín đã duyệt theo xác nhận của Cường; T010 và duyệt schema là gate dữ liệu chính thức | P2/Tín và P1/Huy |
| `CP5` | `PLANNED` | training/evaluation/artifact reports | Chờ manifest Quang bàn giao | P4/Quang và P1/Huy |

## Commit gần nhất

| Field | Value |
|---|---|
| Task/checkpoint | `CP2 / T014-T016` · đã push |
| Commit message | `CP2 T014-T016(extractor): add shared WebM feature pipeline` |
| Paths | `ai/configs/`, `ai/setup_models.py`, `ai/src/visign_ai/landmarks/`, `ai/tests/landmarks/`, evidence CP2 và README P3 |
| Pre-commit sync | Chưa ghi bằng chứng |
| Gate commands | Pytest AI (20 pass), Ruff, mypy. Parity API còn chờ T037 |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` |
| Full SHA | 865547ebe637da010ac7c953bcce38389ecca831 |
| Pre-push sync | Rebase lên 1699464, chạy lại 20 test AI đạt |
| Push status | `PUSHED` · đã có trên `origin/main` |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T014-T016` | Shared WebM feature pipeline | `CP2 T014-T016(extractor): add shared WebM feature pipeline` | 865547ebe637da010ac7c953bcce38389ecca831 | [Commit 865547e](https://github.com/HiImNVH/ViSign/commit/865547ebe637da010ac7c953bcce38389ecca831) | PASS cục bộ · 20 test AI | P2/Tín, P1/Huy | PUSHED · P1/P2 đã review code, schema còn draft |
| `CP2/T017` | Batch extraction CLI | `CP2 T017(extractor): add batch landmark extraction CLI` | 4a5aa5295702197d9509302d4bcf07a1dcd0d154 | [Commit 4a5aa52](https://github.com/HiImNVH/ViSign/commit/4a5aa5295702197d9509302d4bcf07a1dcd0d154) | [PASS cục bộ](../../docs/evidence/checkpoints/CP2/T017-p3-cuong-smoke.md) | P2/Tín, P1/Huy | PUSHED · [CI bản sửa bc642c1](https://github.com/HiImNVH/ViSign/actions/runs/42364019259) đạt · VERIFIED sau 57311bf theo xác nhận của Cường |

## Handoff

- Current risks: feature schema v0.3 chưa được APPROVED; không được bulk-extract trước review.
- Required input: representative WebM clips và data manifest đã audit.
- Next owner/action: P3 đã xuất bộ review 6 WebM gồm 6 JSON và 18 ảnh L/R. Cả 6 tạo được tensor hữu hạn, 20–32/32 bước dùng được. Huy chờ nhận bộ clip để duyệt schema và xác nhận clip nghi lật. T017 đã push, CI xanh. P3 đã push test tự động theo review P2 tại 57311bf; đã được Huy/Tín duyệt; nối T010 khi Quang bàn giao. Tín phối hợp kiểm parity qua đường serving.
- Review T098 (snapshot local của Quang): CHANGES_REQUESTED. Pytest 12 test và 25 subtest đạt, Ruff/mypy còn lỗi. Decoder đọc 24/27 clip. T017 xuất NPZ cho 3/3 clip nhóm S001-R01; nguồn/quyền/nhãn còn chờ xác nhận.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P2/Tín | P3/Cường | Review AI toolchain T003 |
