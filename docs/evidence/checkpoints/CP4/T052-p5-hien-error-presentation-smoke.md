# CP4 T052 — Thông báo lỗi camera/API ổn định (P5 Hiển)

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint / task | `CP4 / T052` (`US2`) |
| Owner | `P5 Hiển` |
| Reviewer | `P2 Tín`, `P1 Huy` — chờ review độc lập |
| Commit | `CP4 T052(web): present stable Vietnamese camera and API errors` — SHA/link sau push |
| Ngày/giờ | `2026-11-07T22:31:14+07:00` |
| Môi trường | Windows / PowerShell, Node `26.7.0`, npm `11.19.0`, Vitest `5.0.5`, Playwright `1.64.1`, Edge (`VISIGN_BROWSER_CHANNEL=msedge`) |
| Status | `LOCAL_PASS / READY_FOR_REVIEW`; chờ reviewer và integration với thiết bị/backend thật |

## 2. Phạm vi

- `RecognitionError.tsx`: hiển thị lỗi camera bằng thông báo tiếng Việt hiện có, lỗi metadata bằng hướng dẫn kết nối lại, lỗi nhận diện theo loại `network`/`timeout`/`invalid-response` và mã HTTP được cho phép.
- `content/vi.ts`: cố định copy tiếng Việt cho 11 mã lỗi API `v1`; mã không nhận biết dùng thông báo dự phòng.
- `CameraRecorder.tsx`: gắn thông báo lỗi vào giao diện camera, tránh thông báo lặp và tránh hiển thị lỗi prediction khi metadata không sẵn sàng; giữ thao tác thử lại do người dùng chủ động.
- Tests: bao phủ lỗi camera, từng mã HTTP, mã lạ/XSS, thông tin nhạy cảm từ backend không được render, cancel im lặng, tải lại metadata, explicit retry, keyboard và khung hình `320×180` trên ba cấu hình Edge.
- Không thay đổi API, timeout/cancel/reset lifecycle của T053, model hay schema. Sử dụng inference API `v1`.

## 3. Smoke test

Từ `apps/web` (PowerShell): `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check`.

| # | Mục tiêu | Command hoặc thao tác | Kết quả thực tế / exit code | Trạng thái |
|---|---|---|---|---|
| 1 | Component/error negative | `npm.cmd test -- tests/recognition/RecognitionError.test.tsx tests/recognition/recognition-errors.test.tsx` | **40/40** passed, exit `0` | `PASS` |
| 2 | Static gate | `npm.cmd run check` — ESLint + TypeScript | lint/typecheck thành công, exit `0` | `PASS` |
| 3 | Toàn bộ unit/component | `npm.cmd run check` — Vitest | **122/122**, 9 files, exit `0` | `PASS` |
| 4 | Production build | `npm.cmd run check` — Vite | 25 modules transformed, exit `0` | `PASS` |
| 5 | Browser fake-camera | `npm.cmd run check` — Playwright Edge | **42/42** desktop/mobile/landscape, exit `0`; kiểm tra lỗi, retry chủ động và không tràn khung `320×180` | `PASS` |
| 6 | Real webcam/API/model | E2E live với backend và thiết bị thật | Chưa chạy trong gate này; cần integration sau | `NOT_RUN` |

Browser tests sử dụng API `v1` và camera mock; các log `ECONNREFUSED 127.0.0.1:8000` của trường hợp cố ý không mock metadata là đường fallback, không làm gate thất bại. Lần chạy đầu có 3 failure vì test T043 còn kỳ vọng copy lỗi cũ; đã cập nhật assertion theo thông báo mới và chạy lại **toàn bộ** gate thành công.

## 4. Artifact / link

| Loại | Tham chiếu | Ghi chú |
|---|---|---|
| Commit diff | Xem `git log --oneline --grep='CP4 T052'`; cập nhật SHA/link sau push | Commit T052 |
| CI | `NOT_VERIFIED` — chưa xác nhận GitHub Actions của candidate | Không tự nhận CI PASS |
| Component tests | `apps/web/tests/recognition/RecognitionError.test.tsx`, `apps/web/tests/recognition/recognition-errors.test.tsx` | Safe copy/negative flows |
| Browser tests | `apps/web/tests/browser/camera.spec.ts` | 3 cấu hình viewport |
| Báo cáo | `docs/evidence/checkpoints/CP4/T052-p5-hien-error-presentation-smoke.md` | Gate và rủi ro |
| API/model | Mock API `v1` + metadata test | Không lưu raw media/model |

## 5. Rủi ro, rollback, handoff

- Chưa kiểm tra thông báo với thiết bị thật/backend thật; test dùng fake-camera và mock API.
- Nếu cần rollback sau publish: `git revert <commit-sha-T052>`.
- T052 chờ reviewer độc lập trước khi đánh dấu `[X]`. P5 tiếp tục T053 timeout/cancel/reset.

## 6. Xác nhận

- [x] Đã chạy full web gate sau sửa (exit `0`).
- [ ] Xác nhận exact-path staging, diff check và hygiene ở bước commit.
- [ ] Điền full SHA/link sau push.
- [ ] Reviewer chạy lại gate và xác nhận.

**Reviewer result**: `PENDING`.
