# P2 Tín - Backend/Cloud/Security

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P2` |
| Current member | Tín |
| Role | Backend/API, cloud và security; CP1 setup coordinator |
| Canonical ownership | `services/inference-api/`, `infra/aws/`, `tests/security/`; T001–T007 setup paths |
| Allowed commit scopes | `setup` (chỉ T001–T007), `api`, `backend`, `security`, `cloud` |
| Current checkpoint | `CP1` |
| Integration window | `CLOSED` sau push; P1 đang review |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T001-T007 / CP1` | `DONE` | monorepo dirs, root/API/AI pyproject + `uv.lock`, web Vite/lint/test config, `.gitignore` | CP1 `VERIFIED` (P1 đóng `4b21e71`), đã `[X]`; follow-up `.gitignore` chặn file nén theo ghi chú P1 | P1/Huy, P3/Cường, P5/Hiển |
| `T086 / CP1 review` | `DONE` | `docs/evidence/checkpoints/CP1/T086-p1-huy-member-frame-smoke.md` | `VERIFIED`; ghi chú P3 lệch khung sau `a8ea4c6` | P2/Tín là reviewer |
| `T091 / CP7 review` | `DONE` | `docs/evidence/checkpoints/CP7/T091-p1-huy-quality-ci-smoke.md` | `P2_VERIFIED`; 4 ghi chú không chặn | P2/Tín là reviewer |
| `T039 / CP3 review` | `DONE` | `docs/evidence/checkpoints/CP3/T039-p5-hien-focus-fix.md` | Re-review `VERIFIED`: `useLayoutEffect`, 30/30 pass, 47 unit + 21 Edge PASS trên Node 24 | P2/Tín là reviewer |
| `T004 / CP1 fix` | `P1_VERIFIED` | `apps/web/package.json`, lockfile | Huy verify `d3afdff`; `plan.md`/`quickstart.md` đã cập nhật; chờ Hiển (kèm `apps/web/README.md`) | P5/Hiển, P1/Huy |
| `T019-T021 / CP2` | `REVIEW` | `services/inference-api/src/visign_api/domain/`, unit tests | T021 `DONE` `[X]` (P1 đóng `4f0a32a`); T020 đã sửa chữ bị từ chối và `classLabel` khoảng trắng, chờ P5 kiểm lại; T019 chờ Cường (metadata, T059 `demoReady`) | P3/Cường, P5/Hiển |
| `T022-T023 / CP2` | `REVIEW` | `services/inference-api/src/visign_api/{config,observability}.py`, unit tests | T023 `DONE` `[X]` (P1 đóng `4f0a32a`); T022 đã khóa CORS credential `Literal[False]`, chờ P5 kiểm lại | P1/Huy, P5/Hiển (CORS) |
| `T014-T016 / CP2 review` | `DONE` | review ranh giới API trong `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` | Đã ghi `P2_VERIFIED`; chờ Cường xác nhận quy tắc `NO_PERSON_DETECTED` | P2/Tín là reviewer |
| `T026 / CP2` | `REVIEW` | `services/inference-api/src/visign_api/{main.py,api/,inference/coordinator.py}` | P1_VERIFIED; CORS credential đã khóa ở `Settings` (T022); ngoại lệ preflight ghi vào quy ước T099; chờ P5 kiểm lại | P1/Huy, P5/Hiển (CORS) |
| `T024-T025 / CP2` | `DONE` | `services/inference-api/src/visign_api/inference/temporary_clip.py`, unit tests | Huy verify `6cc3900`; đã đánh `[X]` trong `tasks.md`; ghi chú: kiểm 10 MiB trước khi đọc hết body (T049) | P1/Huy |
| `T099 / CP2` | `DONE` | `docs/contracts/api-conventions.md`, OpenAPI, `apps/web/src/types/inference-api.ts`, `tests/contract/` | P1 lead + P5 consumer; `[X]` (P1 đóng `4f0a32a`); quy ước `v1.0.1` ghi ngoại lệ preflight | P5/Hiển và P1/Huy |
| `T017 / CP2 review` | `DONE` | `docs/evidence/checkpoints/CP2/T017-p3-cuong-smoke.md` | Re-review `VERIFIED`: 13 test mới (28 passed AI); ghi chú merge commit `fc7d606` | P2/Tín là reviewer |
| `T040 / CP2 review` | `DONE` | `docs/evidence/checkpoints/CP2/T040-p5-hien-smoke.md` | `P2_VERIFIED` API contract; 1 MEDIUM (guard `meanings` rỗng), 3 LOW | P2/Tín là reviewer |
| `T037 / CP3` | `REVIEW` | `services/inference-api/src/visign_api/inference/` | Ánh xạ lỗi `P1_VERIFIED`; adapter + parity `7d5c16a`; loader/fixture/registry `7adc7e5` (CI success); GRU predictor chờ T033/T036 của P3 | P3/Cường, P1/Huy |
| `T095 / CP7 benchmark` | `REVIEW` | `services/inference-api/scripts/benchmark_serving_memory.py`, `docs/evidence/checkpoints/CP7/T095-p2-tin-serving-ram-benchmark.md` | RAM đỉnh 480–600 MB/clip trên Windows: EC2 1 GB không an toàn, đề xuất ≥ 2 GB; chờ Huy quyết instance, đo lại trên Linux | P1/Huy, P3/Cường |
| `CP3-CP7` | `PLANNED` | predictor, errors/security, admin API, AWS (EC2/ECR/S3/CloudFront) | Chờ checkpoint tương ứng | P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T030/T037 / CP3` (loader, fixture predictor, registry) |
| Proposed commit | `CP3 T030,T037(api): add artifact loader, fixture predictor and registry` |
| Exact staged paths | `services/inference-api/src/visign_api/inference/{artifact_loader,predictor,predictor_registry}.py`, `services/inference-api/tests/unit/{test_artifact_loader,test_predictor_registry}.py`, `services/inference-api/tests/fixtures/model-artifacts/{fixture,fixture-low-confidence}/model_info.json`, `members/p2-tin/README.md`, `docs/evidence/checkpoints/CP3/T037-p2-tin-artifact-registry-smoke.md` |
| Pre-commit sync | `PASS` — stash/pull/apply qua `bc642c1` (T017 của P3); gate chạy lại; `origin/main...HEAD` = `0 0` |
| Gate commands | RED→GREEN 28 passed, 3 mutation fail, API+contract 173 passed + 1 skipped ×3 `-W error`, Ruff/format/mypy |
| Smoke evidence | `docs/evidence/checkpoints/CP3/T037-p2-tin-artifact-registry-smoke.md` |
| Local commit | `7adc7e5503ef4bf7cd86497247791aea2046db96` |
| Pre-push sync | `PASS` — `git pull --rebase` không có commit mới (`0 1`) |
| Push status | `PUSHED` lúc 2026-11-07T17:38:34+07:00 theo xác nhận của owner — [commit](https://github.com/HiImNVH/ViSign/commit/7adc7e5503ef4bf7cd86497247791aea2046db96); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42364814495) |

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
| `CP3/T037 serving` | Adapter đặc trưng + parity offline ↔ API | `CP3 T037(api): add serving feature extraction adapter with parity test` | `7d5c16ac3db817764d042853b8b6276cd825b870` | [commit](https://github.com/HiImNVH/ViSign/commit/7d5c16ac3db817764d042853b8b6276cd825b870) | 145 passed + parity VP8/VP9; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42361742686) | P3/Cường, P1/Huy | `PUSHED` |
| `CP2/T024-T025 done` | Đánh `[X]` T024–T025 sau P1 verify | `CP2 T024-T025(api): mark temporary clip tasks done after P1 verify` | `1c4539f3dd244de569dbb6e2ee38e8fa1cd3c010` | [commit](https://github.com/HiImNVH/ViSign/commit/1c4539f3dd244de569dbb6e2ee38e8fa1cd3c010) | Task format 99/0 | P1/Huy | `PUSHED` |
| `CP7/T095 benchmark` | Benchmark RAM/độ trễ cho AWS | `CP7 T095(cloud): add serving RAM and latency benchmark for AWS sizing` | `89f5443d82a8292e5fb8a0f0c9b637e0dda7445d` | [commit](https://github.com/HiImNVH/ViSign/commit/89f5443d82a8292e5fb8a0f0c9b637e0dda7445d) | 4 clip × 2 lần; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42362596296) | P1/Huy, P3/Cường | `PUSHED` |
| `CP3/T030,T037 registry` | Loader, fixture predictor, registry fail closed | `CP3 T030,T037(api): add artifact loader, fixture predictor and registry` | `7adc7e5503ef4bf7cd86497247791aea2046db96` | [commit](https://github.com/HiImNVH/ViSign/commit/7adc7e5503ef4bf7cd86497247791aea2046db96) | 173 passed + 1 skipped; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42364814495) | P3/Cường, P1/Huy | `PUSHED` |
| `CP2/T017 review` | Review CLI trích landmark của P3 | `CP2 T017(verify): request tests for batch extraction CLI` | `a6d936163968d46a9b61f4cd0bd6f712670c52fe` | [commit](https://github.com/HiImNVH/ViSign/commit/a6d936163968d46a9b61f4cd0bd6f712670c52fe) | Smoke 4 mã từ chối; `CHANGES_REQUESTED` thiếu test | P3/Cường | `PUSHED` |
| `CP2/T020 fix` | Chữ cố định cho kết quả bị từ chối | `CP2 T020(api): require fixed text on rejected predictions` | `6ee9e613e5fcafa5ed2fdcbc83aaf863d110d00d` | [commit](https://github.com/HiImNVH/ViSign/commit/6ee9e613e5fcafa5ed2fdcbc83aaf863d110d00d) | 18 test, 176 passed; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42370782722) | P5/Hiển | `PUSHED` |
| `CP2/T022,T026 fix` | Khóa CORS credential `Literal[False]` | `CP2 T022,T026(api): forbid credentialed CORS configuration` | `b1390074e57aafa57c8ad3e8f5c928dae2d6d932` | [commit](https://github.com/HiImNVH/ViSign/commit/b1390074e57aafa57c8ad3e8f5c928dae2d6d932) | 16 test, 178 passed, app từ chối khởi động; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42370782722) | P5/Hiển | `PUSHED` |
| `CP2/T099 wording` | Quy ước `v1.0.1`: ngoại lệ preflight | `CP2 T099(api): document CORS preflight exception in API conventions` | `8cadadc83919aa4a003eaf2014a255848d2d6265` | [commit](https://github.com/HiImNVH/ViSign/commit/8cadadc83919aa4a003eaf2014a255848d2d6265) | drift 15 passed; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42370782722) | P5/Hiển, P1/Huy | `PUSHED` |
| `CP1/T007 follow-up` | `.gitignore` chặn file nén | `CP1 T007(setup): ignore archive files to match CI hygiene` | `9abd2f35c34cbe859444e2a52f2a7859dc20e0ab` | [commit](https://github.com/HiImNVH/ViSign/commit/9abd2f35c34cbe859444e2a52f2a7859dc20e0ab) | `git check-ignore`; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42370782722) | P1/Huy | `PUSHED` |
| `CP3/T039 re-review` | Xác nhận sửa focus của P5 | `CP3 T039(verify): confirm camera focus fix after P2 review` | `e07720d1a1530ae89b9f17d3a0d76c0d753f3eeb` | [commit](https://github.com/HiImNVH/ViSign/commit/e07720d1a1530ae89b9f17d3a0d76c0d753f3eeb) | 30/30, 47 unit, 21 Edge; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42371289103) | P5/Hiển | `PUSHED` |
| `CP2/T017 re-review` | Xác nhận test CLI của P3 | `CP2 T017(verify): confirm batch CLI regression tests` | `69495d4d560dd826a9cd3fd9512b8ab2c171fad2` | [commit](https://github.com/HiImNVH/ViSign/commit/69495d4d560dd826a9cd3fd9512b8ab2c171fad2) | 28 passed AI; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42371289103) | P3/Cường | `PUSHED` |
| `CP2/T040 review` | Review API client của P5 | `CP2 T040(verify): record P2 API client contract review` | `37a8817f0902e9008b033c1365e1b2476886df56` | [commit](https://github.com/HiImNVH/ViSign/commit/37a8817f0902e9008b033c1365e1b2476886df56) | 47 unit; `P2_VERIFIED`; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42371289103) | P5/Hiển | `PUSHED` |
| `CP2/T020 fix 2` | `classLabel` khoảng trắng bị từ chối | `CP2 T020(api): reject blank class labels on accepted predictions` | `542e33f9061a9b9a8374b8c4cabf378805f7a320` | [commit](https://github.com/HiImNVH/ViSign/commit/542e33f9061a9b9a8374b8c4cabf378805f7a320) | 19 test, 179 passed; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42371289103) | P5/Hiển | `PUSHED` |

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
