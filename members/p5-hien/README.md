# P5 Hiển - Frontend/UX

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P5` |
| Current member | Hiển |
| Role | Frontend, UX và browser E2E |
| Canonical ownership | `apps/web/`, frontend tests và UX evidence |
| Allowed commit scopes | `web`, `ui`, `ux`, `e2e` |
| Current checkpoint | `CP2 T020/T022/T026` đã `P5_VERIFIED`; `T039 / CP3` đã push |
| Integration window | Push theo yêu cầu trực tiếp của owner trong phiên; chưa xác nhận window của Huy |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T004/T006 / CP1` | `P5_VERIFIED` | web Vite/lint/test config do Tín tạo | Evidence `docs/evidence/checkpoints/CP1/T004-T006-p5-hien-review.md` | P1/Huy |
| `T020/T022/T026 / CP2 review` | `P5_VERIFIED` | API prediction validation, CORS settings và FastAPI middleware của P2 | Fix đã kiểm lại; evidence `docs/evidence/checkpoints/CP2/T020-T021-T022-T026-p5-hien-review.md`; task đã `[X]` | P2/Tín, P1/Huy |
| `T040 / CP2` | `REVIEW` | typed API client và model-info | Client đã có transport test; chờ review P2 và tích hợp endpoint | P2/Tín |
| `T100-T104 / US6` | `TODO` | `apps/web/src/features/recognition/{translationHistory.ts,TranscriptPanel.tsx,HistoryPanel.tsx}`, tests | Lead duyệt 2026-11-07 (FR-034–FR-036): bản dịch trực tiếp + lịch sử trình duyệt ≥24 giờ; làm sau T040/T043 | P1/Huy, P2/Tín |
| `T039 / CP3` | `PUSHED` | `apps/web/src/features/recognition/`, camera UI/tests | Chờ review Tín/Huy; API/model chưa tích hợp | P2/Tín, P1/Huy |
| `T041 / CP3` | `IMPLEMENTED_LOCAL` | `apps/web/src/features/recognition/useRecognition.ts`, `apps/web/tests/recognition/useRecognition.test.tsx` | 11 hook tests, 58 unit và 21 Edge browser PASS; evidence `docs/evidence/checkpoints/CP3/T041-p5-hien-recognition-state-smoke.md`; chờ review và integration T043 | P2/Tín, P1/Huy |
| `T051-T053 / CP4` | `PLANNED` | error/retry/placeholders và integration | Chờ contract foundation | P2/Tín và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T039 / CP3` — chuẩn bị local theo yêu cầu; không đóng checkpoint |
| Proposed commit | `CP3 T039(ui): fix zoom controls and preserve keyboard focus` |
| Exact staged paths | `apps/web/src/features/recognition/CameraRecorder.tsx`, `apps/web/src/styles.css`, `apps/web/tests/browser/camera.spec.ts`, member README, `docs/evidence/checkpoints/CP3/T039-p5-hien-prepush-review.md` |
| Pre-commit sync | Fetch/rebase origin/main tại `ffb365ad27657c01a923f58824d96773ee5aaae0`; frontend unchanged qua cập nhật evidence, gate PASS |
| Gate commands | `npm.cmd run typecheck`; `VISIGN_BROWSER_CHANNEL=msedge npm.cmd run check` (PowerShell đặt env riêng) |
| Smoke evidence | `docs/evidence/checkpoints/CP3/T039-p5-hien-prepush-review.md` |
| Local commit | `e7ae3f797509bc8f6e0216bd8f00453ce7e986c7` |
| Pre-push sync | `git pull --rebase origin main` up to date tại `ffb365ad27657c01a923f58824d96773ee5aaae0`; push thường thành công tới e7ae3f7 |
| Push status | `PUSHED`; chưa tự đánh dấu VERIFIED, chờ Tín/Huy review |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP1/T004-T006` | Review web toolchain | `CP1 T004-T006(verify): record P5 web toolchain review` | `01eea59dc35eac388223498bee8836a8263e25db` | [commit](https://github.com/HiImNVH/ViSign/commit/01eea59dc35eac388223498bee8836a8263e25db) | Install/lint/typecheck/build, 42 unit và 21 browser PASS; xem evidence về worktree | P5/Hiển | `P5_VERIFIED` |
| `CP2/T020,T022,T026` | Kiểm lại fix response và CORS của Tín | `CP2 T020,T022,T026(verify): record P5 retest approval` | Xem git log | Xem git log | API + contract 179 passed, 1 skipped; Ruff/mypy và probe HTTP CORS độc lập PASS | P5/Hiển | `P5_VERIFIED` |
| `CP2/T040` | Versioned inference API client | `CP2 T040(web): add versioned inference API client` | Xem git log | Xem git log | lint/typecheck/build và 47 unit PASS; transport mock | P2/Tín, P1/Huy | `REVIEW` |
| `CP3/T039` | Explicit local camera capture và resource cleanup | `CP3 T039(web): add explicit camera capture and cleanup` | `e9badadf94ff6f0a086bac5dabddbc49c5cd1f46` | [commit](https://github.com/HiImNVH/ViSign/commit/e9badadf94ff6f0a086bac5dabddbc49c5cd1f46) | 32 unit/component + 8 browser Edge; lint/typecheck/build PASS | P2/Tín, P1/Huy | `PUSHED` |
| `CP3/T039 layout` | Camera lớn, văn bản dịch bên dưới theo yêu cầu | `CP3 T039(ui): restore large camera and text below` | `a074849599176e95abfbb3f606fbbf1df611c0ad` | [commit](https://github.com/HiImNVH/ViSign/commit/a074849599176e95abfbb3f606fbbf1df611c0ad) | 32 unit/component + 8 browser Edge; kiểm tra thứ tự dọc và chiều rộng camera PASS | P2/Tín, P1/Huy | `PUSHED` |
| `CP3/T039 overlay` | Áp dụng demo đã duyệt: nút/chữ trong camera, chữ chỉ khi accepted | `CP3 T039(ui): apply approved camera overlay layout` | `812b46a422dee62970d6165f33bad222fe3a57d0` | [commit](https://github.com/HiImNVH/ViSign/commit/812b46a422dee62970d6165f33bad222fe3a57d0) | 42 unit/component + 15 browser Edge; lint/typecheck/build, no-scroll và result guard PASS | P2/Tín, P1/Huy | `PUSHED` |
| `CP3/T039 review` | Sửa zoom/focus, thêm accepted browser fixture | `CP3 T039(ui): fix zoom controls and preserve keyboard focus` | `e7ae3f797509bc8f6e0216bd8f00453ce7e986c7` | [commit](https://github.com/HiImNVH/ViSign/commit/e7ae3f797509bc8f6e0216bd8f00453ce7e986c7) | 42 unit/component + 21 browser Edge PASS; API 73; AI 15 PASS/5 SKIPPED | P2/Tín, P1/Huy | `PUSHED` |

## Handoff

- Current risks: T039 local chưa có upload/recognition; overlay không tự tạo chữ từ capture. Chưa kiểm tra webcam/điện thoại thật; browser gate dùng Edge 157.
- Required input: Tín/lead chốt FE–BE API convention và OpenAPI v1.
- Next owner/action: Tín/Huy review camera local, chờ window trước push; xác nhận handoff `docs/team/fe-be-api-convention.md` và đóng băng T099 trước khi chốt API client.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P2/Tín | P5/Hiển | Review web toolchain T004/T006 |
| 2026-11-07 | P5/Hiển | P2/Tín, P1/Huy | Local T039; xem `docs/evidence/checkpoints/CP3/T039-p5-hien-smoke.md` |
| 2026-11-07 | P5/Hiển | P2/Tín, P1/Huy | Đã kiểm lại và xác nhận `P5_VERIFIED` T020/T022/T026 trên `bb40476`; evidence CP2 review, 179 passed/1 skipped |

## Nền toolchain

- Dùng CP1 của Tín tại `84958a3` và evidence `docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md`.
- Giữ dependency/package-lock của nhóm; candidate camera chỉ bổ sung test scripts và cấu hình browser cần thiết.
- Review tiếp với Tín: dependency dev thực tế có engine cao hơn mức Node 22.12 được khai báo;
  gate camera hiện được xác nhận trên Node 26.7.0.
- Task/checkpoint vẫn giữ mở cho đến khi được tích hợp và review độc lập.

## Kiểm tra trước push ngày 2026-11-07

- Web: clean install, lint/typecheck/build, 42 unit/component và 21 browser tests PASS.
- API: Ruff/mypy, 73 tests PASS. AI: Ruff/mypy, 15 PASS, 5 SKIPPED thiếu WebM fixtures riêng.
- Audit runtime 0 vulnerability; hygiene/secret-pattern scan không phát hiện artifact bị cấm.
- Node 24.22.2 static/unit/build PASS; CI quality được kích hoạt sau push, chưa tự xác nhận CI hoặc review nhóm.
- Evidence: `docs/evidence/checkpoints/CP3/T039-p5-hien-prepush-review.md`.
