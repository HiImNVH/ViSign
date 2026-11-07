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
| Proposed commit | `CP3 T039(ui): restore large camera and text below` |
| Exact staged paths | `apps/web/src/features/recognition/CameraRecorder.tsx`, `apps/web/src/styles.css`, `apps/web/tests/browser/camera.spec.ts`, `apps/web/README.md`, member README và `docs/evidence/checkpoints/CP3/T039-p5-hien-layout-smoke.md` |
| Pre-commit sync | Fetch `origin/main` tại `18a07aef641b424ddf4772249623b1bc04a4b926`; remote-only count 0, local camera commit `edd328d` đã có; chạy lại toàn bộ gate |
| Gate commands | `npm.cmd run typecheck`; `VISIGN_BROWSER_CHANNEL=msedge npm.cmd run check` (PowerShell đặt env riêng) |
| Smoke evidence | `docs/evidence/checkpoints/CP3/T039-p5-hien-layout-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `NOT_PUSHED` — chờ foundation của Tín, Huy mở window và review độc lập |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T040` | Versioned inference API client | `CP2 T040(web): add versioned inference API client` | `PENDING` | `PENDING` | `NOT_RUN` | P2/Tín, P1/Huy | `BLOCKED` |
| `CP3/T039` | Explicit local camera capture và resource cleanup | `CP3 T039(web): add explicit camera capture and cleanup` | `PENDING` trước push | `PENDING` | 32 unit/component + 8 browser Edge; lint/typecheck/build PASS | P2/Tín, P1/Huy | `NOT_PUSHED` |
| `CP3/T039 layout` | Camera lớn, văn bản dịch bên dưới theo yêu cầu | `CP3 T039(ui): restore large camera and text below` | `PENDING` trước push | `PENDING` | 32 unit/component + 8 browser Edge; kiểm tra thứ tự dọc và chiều rộng camera PASS | P2/Tín, P1/Huy | `NOT_PUSHED` |

## Handoff

- Current risks: T039 local chưa có upload/recognition; chưa kiểm tra webcam/điện thoại thật. Camera E2E trên Headless Shell 158 chưa đạt; đã chạy Edge 157.
- Required input: Tín/lead chốt FE–BE API convention và OpenAPI v1.
- Next owner/action: review toolchain của Tín; Tín/Huy review camera local, chờ window trước push. T099 vẫn chặn việc chốt API client.
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
