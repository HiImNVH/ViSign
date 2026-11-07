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
| Integration window | `CLOSED` sau push; P1 đang review |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T001-T007 / CP1` | `P1_VERIFIED` | monorepo dirs, root/API/AI pyproject + `uv.lock`, web Vite/lint/test config, `.gitignore` | Huy đã tái lập gate; chờ Cường (AI) và Hiển (web) review | P3/Cường, P5/Hiển |
| `T086 / CP1 review` | `TODO` | `docs/evidence/checkpoints/CP1/T086-p1-huy-member-frame-smoke.md` | Verify member frame của Huy từ `origin/main` | P2/Tín là reviewer |
| `T019-T021 / CP2` | `P1_VERIFIED` | `services/inference-api/src/visign_api/domain/`, unit tests | Huy đã tái lập gate; chờ Cường (T019) và Hiển (T020/T021) review; `ruff format` nằm trong candidate T022–T023 | P3/Cường, P5/Hiển |
| `T022-T023 / CP2` | `DOING` | `services/inference-api/src/visign_api/{config,observability}.py`, unit tests | Gate local PASS; chờ integration window | P1/Huy, P5/Hiển (CORS) |
| `T014-T016 / CP2 review` | `DOING` | review ranh giới API trong `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` | Đã tái lập gate + probe; kết quả `P2_VERIFIED` sẽ ghi vào evidence của Cường khi có window | P2/Tín là reviewer |
| `T099 / CP2` | `TODO` | API convention, OpenAPI và client types | Lead đã gửi `docs/team/fe-be-api-convention.md`; xác nhận D1–D4 cùng Hiển rồi đóng băng | P5/Hiển và P1/Huy |
| `CP3-CP7` | `PLANNED` | predictor, errors/security, admin API, Cloud Run | Chờ checkpoint tương ứng | P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T022-T023 / CP2` |
| Proposed commit | `CP2 T022-T023(api): add runtime settings and privacy-safe logging` |
| Exact staged paths | `services/inference-api/src/visign_api/{config,observability}.py`, `services/inference-api/tests/unit/{test_config,test_observability}.py`, `ruff format` cho `services/inference-api/src/visign_api/domain/{errors,model_version,request_id}.py` và `services/inference-api/tests/unit/{test_error_catalog,test_model_version,test_prediction_response}.py`, `members/p2-tin/README.md`, `docs/evidence/checkpoints/CP2/T022-T023-p2-tin-smoke.md` |
| Pre-commit sync | `PASS` — stash/pull/apply qua `38cc955`; gate chạy lại; `origin/main...HEAD` = `0 0` lúc 2026-11-07T14:29+07:00 |
| Gate commands | pytest RED→GREEN (73 passed, `-W error`), `uv sync --locked`, Ruff check + format check, `python -m mypy` — khớp job `api` của `quality.yml` |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T022-T023-p2-tin-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `NOT_PUSHED` — chờ P1 mở lại integration window |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP0/T086` | Independent CP0 verification | `CP0 T086(verify): record independent P2 verification` | `c77fd98264a6b22cff2a203de9380d5c3dd92f53` | [commit](https://github.com/HiImNVH/ViSign/commit/c77fd98264a6b22cff2a203de9380d5c3dd92f53) | 5/5 PASS | P1/Huy | `VERIFIED` |
| `CP1/T001-T007` | Assign setup toolchain | `CP1 T001-T007(spec): assign setup toolchain to P2 Tin` | `abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4` | [commit](https://github.com/HiImNVH/ViSign/commit/abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4) | Docs check | P1/Huy | `PUSHED` |
| `CP1/T001-T007` | Implement monorepo toolchain | `CP1 T001-T007(setup): scaffold monorepo toolchain` | `84958a34c44bc5e1d7e655cae6b6ed85e07d0c08` | [commit](https://github.com/HiImNVH/ViSign/commit/84958a34c44bc5e1d7e655cae6b6ed85e07d0c08) | Owner + P1 independent PASS | P3/Cường, P5/Hiển | `PARTIAL_VERIFIED` |
| `CP2/T019-T021` | API domain models | `CP2 T019-T021(api): add model metadata, prediction and error domain` | `9b888a182592a2739b665a287ec37a8a4aa9f8f3` | [commit](https://github.com/HiImNVH/ViSign/commit/9b888a182592a2739b665a287ec37a8a4aa9f8f3) | 44 passed, Ruff, mypy; P1 independent PASS | P3/Cường, P5/Hiển | `PARTIAL_VERIFIED` |
| `CP2/T022-T023` | Runtime settings và structured logging | `CP2 T022-T023(api): add runtime settings and privacy-safe logging` | `PENDING` | `PENDING` | 73 passed, Ruff, format, mypy | P1/Huy, P5/Hiển | `LOCAL-DRAFT` |

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
