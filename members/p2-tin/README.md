# P2 Tín - Backend/Cloud/Security

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P2` |
| Current member | Tín |
| Role | Backend/API, cloud và security; CP1 setup coordinator |
| Canonical ownership | `services/inference-api/`, `infra/gcp/`, `tests/security/`; T001–T007 setup paths |
| Allowed commit scopes | `setup` (chỉ T001–T007), `api`, `backend`, `security`, `cloud` |
| Current checkpoint | `CP1` |
| Integration window | `ACTIVE` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T001-T007 / CP1` | `REVIEW` | monorepo dirs, root/API/AI pyproject + `uv.lock`, web Vite/lint/test config, `.gitignore` | Đã push `84958a3`; chờ Cường (AI), Hiển (web), Huy verify từ `origin/main` | P1/Huy |
| `T086 / CP1 review` | `TODO` | `docs/evidence/checkpoints/CP1/T086-p1-huy-member-frame-smoke.md` | Verify member frame của Huy từ `origin/main` | P2/Tín là reviewer |
| `T019-T021 / CP2` | `DOING` | `services/inference-api/src/visign_api/domain/`, unit tests | Gate local PASS; chờ commit/push | P1/Huy, P3/Cường, P5/Hiển |
| `T099 / CP2` | `BLOCKED` | API convention, OpenAPI và client types | Chờ lead gửi quy ước FE–BE API | P5/Hiển và P1/Huy |
| `CP3-CP7` | `PLANNED` | predictor, errors/security, admin API, Cloud Run | Chờ checkpoint tương ứng | P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T019-T021 / CP2` |
| Proposed commit | `CP2 T019-T021(api): add model metadata, prediction and error domain` |
| Exact staged paths | `services/inference-api/{pyproject.toml,uv.lock}`, `services/inference-api/src/visign_api/domain/{__init__,model_version,prediction,errors,request_id}.py`, `services/inference-api/tests/unit/{test_model_version,test_prediction_response,test_error_catalog}.py`, `members/p2-tin/README.md`, `docs/evidence/checkpoints/CP2/T019-T021-p2-tin-smoke.md` |
| Pre-commit sync | `PASS` — `origin/main...HEAD` = `0 0` tại `18a07ae` lúc 2026-11-07T14:05+07:00 |
| Gate commands | pytest RED→GREEN (44 passed), Ruff, `python -m mypy` cho `services/inference-api`; `git diff --cached --check` |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T019-T021-p2-tin-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `NOT_PUSHED` |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP0/T086` | Independent CP0 verification | `CP0 T086(verify): record independent P2 verification` | `c77fd98264a6b22cff2a203de9380d5c3dd92f53` | [commit](https://github.com/HiImNVH/ViSign/commit/c77fd98264a6b22cff2a203de9380d5c3dd92f53) | 5/5 PASS | P1/Huy | `VERIFIED` |
| `CP1/T001-T007` | Assign setup toolchain | `CP1 T001-T007(spec): assign setup toolchain to P2 Tin` | `abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4` | [commit](https://github.com/HiImNVH/ViSign/commit/abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4) | Docs check | P1/Huy | `PUSHED` |
| `CP1/T001-T007` | Implement monorepo toolchain | `CP1 T001-T007(setup): scaffold monorepo toolchain` | `84958a34c44bc5e1d7e655cae6b6ed85e07d0c08` | [commit](https://github.com/HiImNVH/ViSign/commit/84958a34c44bc5e1d7e655cae6b6ed85e07d0c08) | 10/10 PASS local | P1/Huy, P3/Cường, P5/Hiển | `PUSHED` |
| `CP2/T019-T021` | API domain models | `CP2 T019-T021(api): add model metadata, prediction and error domain` | `PENDING` | `PENDING` | 44 passed, Ruff, mypy | P1/Huy, P3/Cường, P5/Hiển | `LOCAL-DRAFT` |

## Handoff

- Current risks: setup chạm web và AI paths ngoài ownership thường kỳ của Tín; `.gitignore` chặn
  mọi `*.webm` nên golden clip T014/T064 cần ngoại lệ có review; vị trí E2E T032 (`tests/e2e/`) khác
  Playwright `testDir` (`apps/web/tests/`).
- Required input: Cường review `ai/pyproject.toml`; Hiển review web toolchain; T099 vẫn chờ lead.
- Next owner/action: Cường verify T003, Hiển verify T004/T006, Huy verify CP1 từ `origin/main`;
  Tín review T086 của Huy; Cường xác nhận T059 ghi `demoReady=true` cho full đạt gate vì API
  không còn tự suy ra từ metric (T019).
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P1/Huy | P2/Tín | Nhận T001–T007, CP1 integration window active |
