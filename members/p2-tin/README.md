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
| `T019-T021 / CP2` | `DONE` | `services/inference-api/src/visign_api/domain/`, unit tests | T019 `[X]` sau khi P3 xác nhận metadata (Huy `219e10d`); T020, T021 `[X]`; T059 ghi `demoReady` theo gate full | P3/Cường, P5/Hiển |
| `T022-T023 / CP2` | `DONE` | `services/inference-api/src/visign_api/{config,observability}.py`, unit tests | T022, T023 `[X]`; `ALLOWED_MIME_TYPES` và `MIN/MAX_DURATION_MS` có hiệu lực từ T049 `b456206` | P1/Huy, P5/Hiển (CORS) |
| `T014-T016 / CP2 review` | `DONE` | review ranh giới API trong `docs/evidence/checkpoints/CP2/T014-T016-p3-cuong-smoke.md` | Đã ghi `P2_VERIFIED`; Cường chốt quy tắc `NO_PERSON_DETECTED` (bàn giao T037 21:02), đã áp ở T049 `3b47521` | P2/Tín là reviewer |
| `T026 / CP2` | `DONE` | `services/inference-api/src/visign_api/{main.py,api/,inference/coordinator.py}` | `[X]`; CORS credential khóa ở `Settings` (T022); ngoại lệ preflight ghi vào quy ước T099 | P1/Huy, P5/Hiển (CORS) |
| `T024-T025 / CP2` | `DONE` | `services/inference-api/src/visign_api/inference/temporary_clip.py`, unit tests | Huy verify `6cc3900`; đã đánh `[X]` trong `tasks.md`; ghi chú: kiểm 10 MiB trước khi đọc hết body (T049) | P1/Huy |
| `T099 / CP2` | `DONE` | `docs/contracts/api-conventions.md`, OpenAPI, `apps/web/src/types/inference-api.ts`, `tests/contract/` | P1 lead + P5 consumer; `[X]` (P1 đóng `4f0a32a`); quy ước `v1.0.1` ghi ngoại lệ preflight | P5/Hiển và P1/Huy |
| `T017 / CP2 review` | `DONE` | `docs/evidence/checkpoints/CP2/T017-p3-cuong-smoke.md` | Re-review `VERIFIED`: 13 test mới (28 passed AI); ghi chú merge commit `fc7d606` | P2/Tín là reviewer |
| `T040 / CP2 review` | `DONE` | `docs/evidence/checkpoints/CP2/T040-p5-hien-smoke.md` | `P2_VERIFIED` API contract; 1 MEDIUM (guard `meanings` rỗng), 3 LOW | P2/Tín là reviewer |
| `T030, T038 / CP3` | `DONE` | `services/inference-api/src/visign_api/api/predictions.py`, contract tests | `P1_VERIFIED`, `[X]` (Huy `7315314`) | P1/Huy, P5/Hiển, P3/Cường |
| `T055-T060 / CP5` | `DONE` | `services/inference-api/src/visign_api/{api/system.py,domain/health.py,main.py}` | `P1_VERIFIED`, `[X]` (Huy `7315314`) | P1/Huy, P5/Hiển |
| `T044-T048 / CP4` | `DONE` | `services/inference-api/src/visign_api/inference/prediction_decision.py` | `P1_VERIFIED`, `[X]` (Huy `7315314`) | P1/Huy, P3/Cường |
| `T037 / CP3` | `DONE` | `services/inference-api/src/visign_api/inference/` | `P1_VERIFIED`, `[X]` (Huy `181408e`); parity clip thật 32/32 và HTTP 32 × 200 (`0f3c557`); độ trễ p95 4,73 s trên CPU Windows chưa đạt SC-002 | P3/Cường, P1/Huy |
| `T049 / CP4` | `DONE` | `services/inference-api/src/visign_api/{inference/clip_validator.py,api/clip_upload_route.py}` | `P1_VERIFIED`, `[X]` (Huy `181408e`); quy tắc P3 qua HTTP và trên 32 clip thật | P3/Cường, P1/Huy, P5/Hiển |
| `T045, T050 / CP4` | `DONE` | `services/inference-api/tests/contract/test_predictions_contract.py`, `inference/worker_thread.py` | `P1_VERIFIED`, `[X]` (Huy `181408e`) | P1/Huy, P5/Hiển |
| `T072, T073 / CP4` | `DONE` | `services/inference-api/src/visign_api/{api/error_handlers.py,domain/errors.py}`, `contracts/openapi.yaml` | `P1_VERIFIED`, `[X]` (Huy `0242745`); câu chữ 404/405 trong `vi.ts` chuyển P5 | P1/Huy, P5/Hiển |
| `T066 / CP4` | `DONE` | `tests/integration/test_prediction_privacy.py`, `inference/temporary_clip.py` | `P1_VERIFIED`, `[X]` (Huy `0242745`) | P1/Huy, P3/Cường |
| `T064 / CP4` | `DONE` | `tests/integration/test_prediction_pipeline.py`, `t036_artifact_builder.py` | `P1_VERIFIED`, `[X]` (Huy `c875ae5`); phần cần clip đại diện chạy local qua `VISIGN_CP2_REFERENCE_WEBM` | P1/Huy, P3/Cường |
| `T065 / CP5 review` | `DONE` | review trong `docs/evidence/checkpoints/CP5/T065-p3-cuong-smoke.md` | `P2_VERIFIED` ứng viên `fd2656f`: A/B 76 cặp clip thật cùng đầu ra, p95 qua API 3.484 → 3.221 ms; đề nghị P3 thêm unit test nhánh song song | P2/Tín là reviewer |
| `T092 / CP4` | `DONE` | `tests/security/`, `scripts/security_audit.py`, `api/security_headers.py`, `docs/security-report.md` | `P1_VERIFIED`, `[X]` (Huy `b23c10f`); rate limit 429 chờ lead chọn WAF ở biên hay limiter trong API | P1/Huy |
| `T095 / CP7 benchmark` | `REVIEW` | `services/inference-api/scripts/benchmark_serving_memory.py`, `docs/evidence/checkpoints/CP7/T095-p2-tin-serving-ram-benchmark.md` | RAM đỉnh 480–600 MB/clip trên Windows: EC2 1 GB không an toàn, đề xuất ≥ 2 GB; chờ Huy quyết instance, đo lại trên Linux | P1/Huy, P3/Cường |
| `T095 / CP7 Docker` | `HANDOFF` → P1/Huy | `infra/aws/docker/`, `infra/aws/nginx/`, `infra/aws/compose.*.yml`, lock torch CPU | Build qua mọi bước, chưa smoke vì ổ C: máy build hết chỗ; Huy build/smoke rồi làm AWS khi chốt tài khoản và instance (`CP7/T095-p2-tin-docker-handoff.md`) | P1/Huy |
| `T065 / CP5 API` | `PLANNED` | `services/inference-api/src/visign_api/inference/` | Tích hợp `prepare_detectors` của P3 (`592db9c`): tạo bộ detector ở worker nền, đóng sau request, xử lý đổi artifact và shutdown; đo lại p95 HTTP kèm parity (SC-002) | P3/Cường, P1/Huy |
| `CP3-CP7` | `PLANNED` | predictor, errors/security, admin API, AWS (EC2/ECR/S3/CloudFront) | Chờ checkpoint tương ứng | P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T065` review (CP5), `T095` Docker bàn giao (CP7) |
| Proposed commit | `CP5-CP7 T065,T095(cloud): record detector review and hand off Docker` |
| Exact staged paths | 14 path: evidence T065 và T095, README này, `infra/aws/README.md`, `infra/aws/docker/` (4), `infra/aws/nginx/` (2), `infra/aws/compose.*.yml` (2), API `pyproject.toml`, `uv.lock` |
| Pre-commit sync | `PASS` — `0 0` trên `a255a7c` (sau khi pull review P1 T092/T065, P3 `592db9c`, P5 web và schema v0.3 `a255a7c`) |
| Gate commands | API + contract + integration + security 417 passed, 3 skipped (extra `serving`); như CI 355 passed, 2 skipped, Ruff, mypy 58 file; `docker compose config`; image web build OK, image API qua mọi bước tới unpack |
| Smoke evidence | `docs/evidence/checkpoints/CP7/T095-p2-tin-docker-handoff.md`; review trong `docs/evidence/checkpoints/CP5/T065-p3-cuong-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `PENDING` |

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
| `CP4/T044,T048` | Luật quyết định theo ngưỡng | `CP4 T044,T048(api): add pure confidence decision rule` | `9a64b41343c2de7787c96ccd18b864b100fd4104` | [commit](https://github.com/HiImNVH/ViSign/commit/9a64b41343c2de7787c96ccd18b864b100fd4104) | 7 test; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42375491322) | P1/Huy, P3/Cường | `PUSHED` |
| `CP5/T055,T060` | Health và model-info | `CP5 T055,T060(api): add health and model-info endpoints` | `fb94e467d3cb408b2eac3d003bf4d3e4f977f007` | [commit](https://github.com/HiImNVH/ViSign/commit/fb94e467d3cb408b2eac3d003bf4d3e4f977f007) | 9 contract + drift 16; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42375491322) | P1/Huy, P5/Hiển | `PUSHED` |
| `CP3/T030,T038` | Endpoint dự đoán | `CP3 T030,T038(api): add prediction endpoint with fixture contract tests` | `bfeee4d1213300f4cf20edc8af63b248e5dbcc45` | [commit](https://github.com/HiImNVH/ViSign/commit/bfeee4d1213300f4cf20edc8af63b248e5dbcc45) | 15 contract, live smoke; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42375491322) | P1/Huy, P5/Hiển, P3/Cường | `VERIFIED` |
| `CP3/T037 GRU` | Adapter GRU cho pilot/full | `CP3 T037(api): add GRU adapter for pilot and full artifacts` | `64ecf72f5d5049bf40e46b89c49c88c01d463359` | [commit](https://github.com/HiImNVH/ViSign/commit/64ecf72f5d5049bf40e46b89c49c88c01d463359) | 57 test (13 tích hợp CLI T036), 11 mutation; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42381710523) | P3/Cường, P1/Huy | `VERIFIED` |
| `CP4/T049` | Kiểm clip tại ranh giới API | `CP4 T049(api): validate clip type, signature, size and landmarks` | `b4562065a30d3b7deb773f23ef5fb19c49e125e6` | [commit](https://github.com/HiImNVH/ViSign/commit/b4562065a30d3b7deb773f23ef5fb19c49e125e6) | 19 mutation; live 413/415/422; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42381710523) | P3/Cường, P1/Huy, P5/Hiển | `VERIFIED` |
| `CP4/T045,T050` | Contract lỗi và dọn dẹp khi hủy | `CP4 T045,T050(api): extend error contract tests and harden cleanup` | `5056c284a49a7dc78750ec2e6b413a7fe3546a14` | [commit](https://github.com/HiImNVH/ViSign/commit/5056c284a49a7dc78750ec2e6b413a7fe3546a14) | 46 contract, 6 mutation; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42381710523) | P1/Huy, P5/Hiển | `VERIFIED` |
| `CP4/T049 P3 rule` | Quy tắc không có người theo P3 | `CP4 T049(api): use pre-normalization points for no-person rule` | `3b47521aa64c47f0bd9068078639626b3b4996c2` | [commit](https://github.com/HiImNVH/ViSign/commit/3b47521aa64c47f0bd9068078639626b3b4996c2) | 4 mutation; 345 passed; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42381710523) | P3/Cường | `VERIFIED` |
| `CP3/T037 HTTP test` | Dự đoán GRU và quy tắc P3 qua HTTP; artifact full | `CP3 T037(api): test GRU predictions over HTTP for pilot and full` | `396d3141729941eff454c0e88702f9cfd4936f75` | [commit](https://github.com/HiImNVH/ViSign/commit/396d3141729941eff454c0e88702f9cfd4936f75) | 5 test mới, 5 mutation; 350 passed; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42382956024) | P3/Cường, P1/Huy | `VERIFIED` |
| `CP3/T037 real clips` | Parity và HTTP trên clip có người thật | `CP3 T037(api): record real-clip parity and HTTP smoke` | `0f3c5578767717d9c4a4e7c94999b1de9005eb00` | [commit](https://github.com/HiImNVH/ViSign/commit/0f3c5578767717d9c4a4e7c94999b1de9005eb00) | Parity 32/32; HTTP 32 × 200, 6 × 422; p95 4,73 s; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42385392156) | P3/Cường, P1/Huy | `PUSHED` |
| `CP4/T072,T073` | 404/405/307 theo contract HTTP | `CP4 T072,T073(api): add 404/405 error envelopes and routing contract` | `d72ab3259547022decdebb1b1382f8ea7f0cce33` | [commit](https://github.com/HiImNVH/ViSign/commit/d72ab3259547022decdebb1b1382f8ea7f0cce33) | 28 test, 6 mutation; web 122/122; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42388018420) | P1/Huy, P5/Hiển | `VERIFIED` |
| `CP4/T066` | Audit quyền riêng tư, dọn clip sót | `CP4 T066(security): audit prediction privacy and sweep stale clips` | `961f59d7ef1465ac3146a8c5d481ffe2da496183` | [commit](https://github.com/HiImNVH/ViSign/commit/961f59d7ef1465ac3146a8c5d481ffe2da496183) | 21 test, 6 mutation; live smoke; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42388018420) | P1/Huy, P3/Cường | `VERIFIED` |
| `CP4/T064` | Clip đại diện, nạp/đổi artifact, rollback | `CP4 T064(api): add representative-clip pipeline and artifact swap tests` | `5cec97b5fd59b81fae86729f775f4c3cbedb01b7` | [commit](https://github.com/HiImNVH/ViSign/commit/5cec97b5fd59b81fae86729f775f4c3cbedb01b7) | 4 test, 4 mutation; clip thật 4/4; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42392276509) | P1/Huy, P3/Cường | `VERIFIED` |
| `CP4/T092` | Audit bảo mật, security header, tắt docs, lệnh audit cho BGK | `CP4 T092(security): add security audit, headers and docs lockdown` | `2561c7d4c5bace5c7c7db00e632382b15d752344` | [commit](https://github.com/HiImNVH/ViSign/commit/2561c7d4c5bace5c7c7db00e632382b15d752344) | 25 test, 14 mutation; audit 5/5; live uvicorn; CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42396068969) | P1/Huy | `PUSHED` |

## Handoff

- Current risks: setup chạm web và AI paths ngoài ownership thường kỳ của Tín; `.gitignore` chặn
  mọi `*.webm` nên golden clip T014/T064 cần ngoại lệ có review; vị trí E2E T032 (`tests/e2e/`) khác
  Playwright `testDir` (`apps/web/tests/`).
- Required input: Cường review `ai/pyproject.toml`; Hiển review web toolchain; T099 vẫn chờ lead.
- Next owner/action: Huy nhận phần Docker/Compose T095 (build, smoke local, rồi AWS sau khi chốt tài khoản và
  instance) theo `docs/evidence/checkpoints/CP7/T095-p2-tin-docker-handoff.md`; Huy chốt rate limit 429 (WAF ở biên
  hay limiter trong API, FE xử lý trước theo D3) và thêm `tests/integration`, `tests/security`, `ruff format --check`
  vào CI; Cường format `ai/src/visign_ai/evaluation/metrics.py` và thêm unit test nhánh `parallel-by-group`; Tín tích
  hợp `prepare_detectors` vào API (SC-002).
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P1/Huy | P2/Tín | Nhận T001–T007, CP1 integration window active |
| 2026-11-08 | P2/Tín | P1/Huy | T092 `2561c7d` chờ review; quyết định rate limit 429 và bổ sung CI theo mục 7–8 `docs/security-report.md` |
| 2026-11-08 | P2/Tín | P1/Huy | Bàn giao Docker/Compose T095: build qua mọi bước, chưa smoke; `docs/evidence/checkpoints/CP7/T095-p2-tin-docker-handoff.md` |
