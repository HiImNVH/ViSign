# P5 Hiển - Frontend/UX

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P5` |
| Current member | Hiển |
| Role | Frontend, UX và browser E2E |
| Canonical ownership | `apps/web/`, frontend tests và UX evidence |
| Allowed commit scopes | `web`, `ui`, `ux`, `e2e` |
| Current checkpoint | `CP1 review`; `T039 / CP3` camera local |
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T004/T006 / CP1` | `REVIEW` | web Vite/lint/test config do Tín tạo | Review web toolchain | P1/Huy |
| `T040 / CP2` | `PLANNED` | typed API client và model-info | Quy ước lead tại `docs/team/fe-be-api-convention.md`; chờ Tín đóng băng T099 | P2/Tín |
| `T039 / CP3` | `LOCAL-DRAFT` | `apps/web/src/features/recognition/`, camera UI/tests | Local capture đã chạy gate; chờ tích hợp foundation/window | P2/Tín, P1/Huy |
| `T051-T053 / CP4` | `PLANNED` | error/retry/placeholders và integration | Chờ contract foundation | P2/Tín và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T039 / CP3` — chuẩn bị local theo yêu cầu; không đóng checkpoint |
| Proposed commit | `CP3 T039(ui): apply approved camera overlay layout` |
| Exact staged paths | `apps/web/src/App.tsx`, `src/features/recognition/{CameraRecorder.tsx,RecognitionOverlay.tsx}`, `src/styles.css`, `tests/browser/camera.spec.ts`, `tests/recognition/recognition-overlay.test.tsx`, `playwright.config.ts`, `apps/web/README.md`, member README và `docs/evidence/checkpoints/CP3/T039-p5-hien-overlay-smoke.md` |
| Pre-commit sync | Fetch/rebase `origin/main` tại `38cc95519510954b3c45a61315620a20804a7a94`; giữ dòng T040 theo handoff mới của lead, khôi phục candidate. Gate frontend sau rebase 377ac98 PASS; các cập nhật c902ea3/38cc955 chỉ có CI/docs, không đổi source frontend |
| Gate commands | `npm.cmd run typecheck`; `VISIGN_BROWSER_CHANNEL=msedge npm.cmd run check` (PowerShell đặt env riêng) |
| Smoke evidence | `docs/evidence/checkpoints/CP3/T039-p5-hien-overlay-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `NOT_PUSHED` — chờ foundation của Tín, Huy mở window và review độc lập |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T040` | Versioned inference API client | `CP2 T040(web): add versioned inference API client` | `PENDING` | `PENDING` | `NOT_RUN` | P2/Tín, P1/Huy | `BLOCKED` |
| `CP3/T039` | Explicit local camera capture và resource cleanup | `CP3 T039(web): add explicit camera capture and cleanup` | `PENDING` trước push | `PENDING` | 32 unit/component + 8 browser Edge; lint/typecheck/build PASS | P2/Tín, P1/Huy | `NOT_PUSHED` |
| `CP3/T039 layout` | Camera lớn, văn bản dịch bên dưới theo yêu cầu | `CP3 T039(ui): restore large camera and text below` | `PENDING` trước push | `PENDING` | 32 unit/component + 8 browser Edge; kiểm tra thứ tự dọc và chiều rộng camera PASS | P2/Tín, P1/Huy | `NOT_PUSHED` |
| `CP3/T039 overlay` | Áp dụng demo đã duyệt: nút/chữ trong camera, chữ chỉ khi accepted | `CP3 T039(ui): apply approved camera overlay layout` | `PENDING` trước push | `PENDING` | 42 unit/component + 15 browser Edge; lint/typecheck/build, no-scroll và result guard PASS | P2/Tín, P1/Huy | `NOT_PUSHED` |

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

## Nền toolchain

- Dùng CP1 của Tín tại `84958a3` và evidence `docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md`.
- Giữ dependency/package-lock của nhóm; candidate camera chỉ bổ sung test scripts và cấu hình browser cần thiết.
- Review tiếp với Tín: dependency dev thực tế có engine cao hơn mức Node 22.12 được khai báo;
  gate camera hiện được xác nhận trên Node 26.7.0.
- Task/checkpoint vẫn giữ mở cho đến khi được tích hợp và review độc lập.
