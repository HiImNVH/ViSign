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
| `T086 / CP1 review` | `DONE` | `docs/evidence/checkpoints/CP1/T086-p1-huy-member-frame-smoke.md` | `VERIFIED`; ghi chú P3 lệch khung sau `a8ea4c6` | P2/Tín là reviewer |
| `T091 / CP7 review` | `DONE` | `docs/evidence/checkpoints/CP7/T091-p1-huy-quality-ci-smoke.md` | `P2_VERIFIED`; 4 ghi chú không chặn | P2/Tín là reviewer |
| `T039 / CP3 review` | `DONE` | `docs/evidence/checkpoints/CP3/T039-p5-hien-smoke.md` | `CHANGES_REQUESTED`: test focus flaky làm đỏ CI; đề xuất `useLayoutEffect` (30/30 pass) | P2/Tín là reviewer |
| `T004 / CP1 fix` | `REVIEW` | `apps/web/package.json`, lockfile | Sửa engines `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0` theo ghi chú của Hiển | P5/Hiển, P1/Huy |
| `T019-T021 / CP2` | `P1_VERIFIED` | `services/inference-api/src/visign_api/domain/`, unit tests | Huy đã tái lập gate; chờ Cường (T019) và Hiển (T020/T021) review; `ruff format` nằm trong candidate T022–T023 | P3/Cường, P5/Hiển |
| `T022-T023 / CP2` | `REVIEW` | `services/inference-api/src/visign_api/{config,observability}.py`, unit tests | Đã push `fb56354`; CI [run 42351545729](https://github.com/HiImNVH/ViSign/actions/runs/42351545729) xanh; chờ Huy/Hiển verify | P1/Huy, P5/Hiển (CORS) |
| `T014-T016 / CP2 review` | `DONE` | review ranh giới API trong `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` | Đã ghi `P2_VERIFIED`; chờ Cường xác nhận quy tắc `NO_PERSON_DETECTED` | P2/Tín là reviewer |
| `T026 / CP2` | `REVIEW` | `services/inference-api/src/visign_api/{main.py,api/,inference/coordinator.py}` | Đã push `4a2dad1`; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42359426590); chờ Huy verify, Hiển xem CORS/expose header | P1/Huy, P5/Hiển (CORS) |
| `T024-T025 / CP2` | `REVIEW` | `services/inference-api/src/visign_api/inference/temporary_clip.py`, unit tests | Đã push `e3c5d8a`; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42357998638); chờ Huy verify | P1/Huy |
| `T099 / CP2` | `REVIEW` | `docs/contracts/api-conventions.md`, OpenAPI, `apps/web/src/types/inference-api.ts`, `tests/contract/` | Đã push `5add400`; chờ P1 verify (lead) và P5 xác nhận consumer | P5/Hiển và P1/Huy |
| `T037 / CP3` | `PAUSED` | `services/inference-api/src/visign_api/inference/` | Ánh xạ lỗi đã push; dừng CP3 theo chỉ đạo P1 (chốt CP1 → đóng CP2 → mở CP3) | P3/Cường, P1/Huy |
| `CP3-CP7` | `PLANNED` | predictor, errors/security, admin API, Cloud Run | Chờ checkpoint tương ứng | P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T026 / CP2` |
| Proposed commit | `CP2 T026(api): add FastAPI v1 foundation with request id and error mapping` |
| Exact staged paths | `services/inference-api/src/visign_api/{main.py,api/__init__.py,api/router.py,api/request_context.py,api/request_middleware.py,api/error_handlers.py,inference/coordinator.py}`, `services/inference-api/tests/unit/{test_app_foundation,test_inference_coordinator,test_observability}.py`, `services/inference-api/{pyproject.toml,uv.lock}`, `members/p2-tin/README.md`, `docs/evidence/checkpoints/CP2/T026-p2-tin-smoke.md` |
| Pre-commit sync | `PASS` — `origin/main...HEAD` = `0 0` tại `e2bdf7f` |
| Gate commands | RED→GREEN 19 passed, mutation CORS fail, API+contract 129 passed ×3 `-W error`, Ruff/format/mypy, live uvicorn smoke |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T026-p2-tin-smoke.md` |
| Local commit | `4a2dad16d41b13f09a20e6ab90e91d288e838f37` |
| Pre-push sync | `PASS` — `git pull --rebase` không có commit mới (`0 1`) |
| Push status | `PUSHED` lúc 2026-11-07T16:21:56+07:00 — [commit](https://github.com/HiImNVH/ViSign/commit/4a2dad16d41b13f09a20e6ab90e91d288e838f37); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42359426590) |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP0/T086` | Independent CP0 verification | `CP0 T086(verify): record independent P2 verification` | `c77fd98264a6b22cff2a203de9380d5c3dd92f53` | [commit](https://github.com/HiImNVH/ViSign/commit/c77fd98264a6b22cff2a203de9380d5c3dd92f53) | 5/5 PASS | P1/Huy | `VERIFIED` |
| `CP1/T001-T007` | Assign setup toolchain | `CP1 T001-T007(spec): assign setup toolchain to P2 Tin` | `abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4` | [commit](https://github.com/HiImNVH/ViSign/commit/abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4) | Docs check | P1/Huy | `PUSHED` |
| `CP1/T001-T007` | Implement monorepo toolchain | `CP1 T001-T007(setup): scaffold monorepo toolchain` | `84958a34c44bc5e1d7e655cae6b6ed85e07d0c08` | [commit](https://github.com/HiImNVH/ViSign/commit/84958a34c44bc5e1d7e655cae6b6ed85e07d0c08) | Owner + P1 independent PASS | P3/Cường, P5/Hiển | `PARTIAL_VERIFIED` |
| `CP2/T019-T021` | API domain models | `CP2 T019-T021(api): add model metadata, prediction and error domain` | `9b888a182592a2739b665a287ec37a8a4aa9f8f3` | [commit](https://github.com/HiImNVH/ViSign/commit/9b888a182592a2739b665a287ec37a8a4aa9f8f3) | 44 passed, Ruff, mypy; P1 independent PASS | P3/Cường, P5/Hiển | `PARTIAL_VERIFIED` |
| `CP2/T022-T023` | Runtime settings và structured logging | `CP2 T022-T023(api): add runtime settings and privacy-safe logging` | `fb563545e33accbbf82bb83ad9373e5eb85e8add` | [commit](https://github.com/HiImNVH/ViSign/commit/fb563545e33accbbf82bb83ad9373e5eb85e8add) | 73 passed, Ruff, format, mypy; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42351545729) | P1/Huy, P5/Hiển | `PUSHED` |
| `CP2/T014-T016 review` | P2 API-boundary review cho pipeline của P3 | `CP2 T014-T016(api): record P2 serving boundary review` | `b248ec78b25f77973f48f1b7cda94290b3f5c1df` | [commit](https://github.com/HiImNVH/ViSign/commit/b248ec78b25f77973f48f1b7cda94290b3f5c1df) | 15 passed/5 skipped, probe 7 clip; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42351545729) | P3/Cường | `PUSHED` |
| `CP2/T099` | Đóng băng quy ước API v1 FE–BE | `CP2 T099(api): freeze FE-BE API v1 conventions with drift test` | `5add4005e572efcd17b921fb144b9feea1b7189c` | [commit](https://github.com/HiImNVH/ViSign/commit/5add4005e572efcd17b921fb144b9feea1b7189c) | drift 15 passed, API 88 passed, web PASS; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42353287941) | P5/Hiển, P1/Huy | `PUSHED` |
| `CP3/T037 mapping` | Ánh xạ mã lỗi pipeline sang API | `CP3 T037(api): map pipeline error codes to stable API codes` | `5b6a441e1e4d5a030ec5fdfde7479d3e252073b0` | [commit](https://github.com/HiImNVH/ViSign/commit/5b6a441e1e4d5a030ec5fdfde7479d3e252073b0) | 103 passed; CI [đỏ do test flaky T039](https://github.com/HiImNVH/ViSign/actions/runs/42352747056), xanh ở [run sau](https://github.com/HiImNVH/ViSign/actions/runs/42353287941) | P3/Cường, P1/Huy | `PUSHED` |
| `CP1/T004 fix` | Khai báo đúng mức Node tối thiểu | `CP1 T004(setup): align Node engines with dependency floor` | `84478b28b99dfd180fb09e09e187a5b813160894` | [commit](https://github.com/HiImNVH/ViSign/commit/84478b28b99dfd180fb09e09e187a5b813160894) | semver, `npm ci`, lint, typecheck; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42353287941) | P5/Hiển, P1/Huy | `PUSHED` |
| `CP3/T039 review` | Review camera UI của P5 | `CP3 T039(verify): request fix for flaky camera focus test` | `d81e5e3a4dc15f58294e4056af7c82020c4197be` | [commit](https://github.com/HiImNVH/ViSign/commit/d81e5e3a4dc15f58294e4056af7c82020c4197be) | Edge 21 passed; flaky 13/15 → 30/30 | P5/Hiển | `PUSHED` |
| `CP7/T091 review` | Review quality workflow của P1 | `CP7 T091(verify): record P2 quality workflow review` | `d3d33e1a42271788476b4c9786bf8ba9f12affab` | [commit](https://github.com/HiImNVH/ViSign/commit/d3d33e1a42271788476b4c9786bf8ba9f12affab) | `P2_VERIFIED` | P1/Huy | `PUSHED` |
| `CP1/T086 review` | Verify member frame của P1 | `CP1 T086(verify): record P2 member frame verification` | `c09853594adcebb580a6953ed376c3044fbe89c0` | [commit](https://github.com/HiImNVH/ViSign/commit/c09853594adcebb580a6953ed376c3044fbe89c0) | `VERIFIED`; P1 đề nghị chữ cuối `review`, commit đã push nên giữ nguyên | P1/Huy | `PUSHED` |
| `CP7/T091 follow-up` | Xác nhận 4 ghi chú T091 đã xử lý | `CP7 T091(verify): confirm P2 follow-up workflow review` | `45ea2148a7ffefcf81057282399612bdb9a94b53` | [commit](https://github.com/HiImNVH/ViSign/commit/45ea2148a7ffefcf81057282399612bdb9a94b53) | Tag action, 2 run success | P1/Huy | `PUSHED` |
| `CP2/T024-T025` | Clip tạm luôn bị xóa | `CP2 T024-T025(api): guarantee temporary clip deletion on every path` | `e3c5d8ae57e8ec33a956bb13a0bcb87c39845d30` | [commit](https://github.com/HiImNVH/ViSign/commit/e3c5d8ae57e8ec33a956bb13a0bcb87c39845d30) | 7 passed, API+contract 110 passed; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42357998638) | P1/Huy | `PUSHED` |
| `CP2/T026` | Nền FastAPI `/api/v1` | `CP2 T026(api): add FastAPI v1 foundation with request id and error mapping` | `4a2dad16d41b13f09a20e6ab90e91d288e838f37` | [commit](https://github.com/HiImNVH/ViSign/commit/4a2dad16d41b13f09a20e6ab90e91d288e838f37) | 129 passed, live smoke; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42359426590) | P1/Huy, P5/Hiển | `PUSHED` |

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
