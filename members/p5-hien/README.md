# P5 Hiển - Frontend/UX

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P5` |
| Current member | Hiển |
| Role | Frontend, UX và browser E2E |
| Canonical ownership | `apps/web/`, frontend tests và UX evidence |
| Allowed commit scopes | `web`, `ui`, `ux`, `e2e` |
| Current checkpoint | `CP2 T020/T022/T026` đã `P5_VERIFIED`; CP3 và T046 đã push; `T051 / CP4` đã đạt local gate, chờ review |
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
| `T041 / CP3` | `PUSHED / READY_FOR_REVIEW` | `apps/web/src/features/recognition/useRecognition.ts`, `apps/web/tests/recognition/useRecognition.test.tsx` | Commit `943065594421facf6c659ccb0e0f6e36495704d4`; evidence `docs/evidence/checkpoints/CP3/T041-p5-hien-recognition-state-smoke.md`; chờ review và integration T043 | P2/Tín, P1/Huy |
| `T042 / CP3` | `PUSHED / READY_FOR_REVIEW` | `apps/web/src/features/recognition/RecognitionResult.tsx`, component/browser tests | SHA `3f3eb369fb18df5a85f399b59de8e18159bffdbb`, 80 unit và 24 Edge browser PASS; evidence `docs/evidence/checkpoints/CP3/T042-p5-hien-accepted-result-smoke.md` | P2/Tín, P1/Huy |
| `T043 / CP3` | `PUSHED / READY_FOR_REVIEW` | `apps/web/src/App.tsx`, `features/recognition/CameraRecorder.tsx`, nội dung/UI và test | SHA `44b14059097534f17463c847ce15e8f0ccb99f5b`; một session camera + metadata + POST thủ công; 80 unit / 39 Edge browser PASS; evidence `docs/evidence/checkpoints/CP3/T043-p5-hien-integration-smoke.md` | P2/Tín, P1/Huy |
| `T046 / CP4` | `PUSHED / READY_FOR_REVIEW` | `apps/web/tests/recognition/recognition-errors.test.tsx` | Commit [`18a7f60b8e8c6af1ba908082eeaf6e0268a55a9a`](https://github.com/HiImNVH/ViSign/commit/18a7f60b8e8c6af1ba908082eeaf6e0268a55a9a); 8 negative component tests; full web gate 88 unit / 39 browser PASS; evidence `docs/evidence/checkpoints/CP4/T046-p5-hien-recognition-errors-smoke.md` | P2/Tín, P1/Huy |
| `T051 / CP4` | `LOCAL_PASS / READY_FOR_REVIEW` | `RecognitionResult.tsx`, `CameraRecorder.tsx`, style và tests | Panel rejected + retry thủ công; 90 unit, 39 browser PASS; evidence `docs/evidence/checkpoints/CP4/T051-p5-hien-rejected-retry-smoke.md` | P2/Tín và P1/Huy |
| `T052-T053 / CP4` | `PLANNED` | `RecognitionError.tsx`, `useRecognition.ts` và integration tests | Làm sau T051; ưu tiên error copy ổn định, timeout/abort/reset | P2/Tín và P1/Huy |

## Checkpoint T046 đã push

| Field | Value |
|---|---|
| Task/checkpoint | `T046 / CP4` — web negative recognition component cases |
| Proposed commit | `CP4 T046(web): cover negative recognition flows` |
| Exact staged paths | `apps/web/tests/recognition/recognition-errors.test.tsx`, `members/p5-hien/README.md`, `docs/evidence/checkpoints/CP4/T046-p5-hien-recognition-errors-smoke.md` |
| Pre-commit sync | Remote cập nhật 7 commit tới `a26aa5d`; stash/rebase/apply thành công, full web gate sau 6 commit đầu 88 unit + 39 browser PASS; commit cuối chỉ có cloud docs |
| Gate commands | `cd apps/web`; `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check` |
| Smoke evidence | `docs/evidence/checkpoints/CP4/T046-p5-hien-recognition-errors-smoke.md` |
| Published commit | [`18a7f60b8e8c6af1ba908082eeaf6e0268a55a9a`](https://github.com/HiImNVH/ViSign/commit/18a7f60b8e8c6af1ba908082eeaf6e0268a55a9a) |
| Push status | `PUSHED / READY_FOR_REVIEW`; owner cho phép push sau gate PASS; không tự đánh dấu VERIFIED trước P1/P2 review |

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
| `CP3/T041` | Recognition state machine và metadata handling | `CP3 T041(web): add recognition state machine` | `943065594421facf6c659ccb0e0f6e36495704d4` | [commit](https://github.com/HiImNVH/ViSign/commit/943065594421facf6c659ccb0e0f6e36495704d4) | 58 unit và 21 browser Edge PASS | P2/Tín, P1/Huy | `PUSHED / READY_FOR_REVIEW` |
| `CP3/T042` | Accepted result view và thông báo demoReady | `CP3 T042(ui): add accepted result and model scope notices` | `3f3eb369fb18df5a85f399b59de8e18159bffdbb` | [commit](https://github.com/HiImNVH/ViSign/commit/3f3eb369fb18df5a85f399b59de8e18159bffdbb) | 80 unit và 24 browser Edge PASS; lint/typecheck/build PASS | P2/Tín, P1/Huy | `PUSHED / READY_FOR_REVIEW` |
| `CP3/T043` | Ghép camera, model-info, prediction API v1 vào trang chính | `CP3 T043(web): integrate camera with recognition results` | `44b14059097534f17463c847ce15e8f0ccb99f5b` | [commit](https://github.com/HiImNVH/ViSign/commit/44b14059097534f17463c847ce15e8f0ccb99f5b) | 80 unit + 39 browser Edge PASS; lint/typecheck/build PASS | P2/Tín, P1/Huy | `PUSHED / READY_FOR_REVIEW` |
| `CP4/T046` | Negative web recognition error, cancel và retry tests | `CP4 T046(web): cover negative recognition flows` | `18a7f60b8e8c6af1ba908082eeaf6e0268a55a9a` | [commit](https://github.com/HiImNVH/ViSign/commit/18a7f60b8e8c6af1ba908082eeaf6e0268a55a9a) | 88 unit + 39 browser Edge PASS; lint/typecheck/build PASS | P2/Tín, P1/Huy | `PUSHED / READY_FOR_REVIEW` |
| `CP4/T051` | Rejected-result panel, explicit fresh recording và focus | `CP4 T051(web): show rejected result with explicit retry` | Xem git log | Chờ push | 90 unit + 39 browser Edge PASS; lint/typecheck/build PASS | P2/Tín, P1/Huy | `LOCAL_PASS / READY_FOR_REVIEW` |

## Handoff

- Current risks: T043 đã ghép request và T046 đã có negative component cases, nhưng browser mới xác nhận fake-camera + API mock; chưa kiểm tra webcam/điện thoại thật, backend thực tế hoặc chất lượng model.
- Required input: Tín/Huy review T042/T043/T046 và kiểm thử lại với API v1 đang chạy.
- Next owner/action: P1/Huy và P2/Tín review độc lập commit T046; rebase và web gate trước push đã PASS.
- T051 đã hoàn thiện local: rejected không dịch, một nút retry, không auto-upload clip mới; 90 unit/39 Edge browser PASS. Chờ review độc lập trước khi đánh dấu `[X]`, P5 tiếp tục T052–T053.
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
