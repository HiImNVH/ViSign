# CP4 T051 — Rejected result và quay lại ký hiệu (P5 Hiển)

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint / task | `CP4 / T051` (`US2`) |
| Owner | `P5 Hiển` |
| Reviewer | `P2 Tín`, `P1 Huy` — chờ review độc lập |
| Commit | `CP4 T051(web): show rejected result with explicit retry` — xem git log sau commit/push |
| Ngày/giờ | `2026-11-07T22:15:33+07:00` |
| Môi trường | Windows / PowerShell, Node `26.7.0`, npm `11.19.0`, Vitest `5.0.5`, Playwright `1.64.1`, Edge (`VISIGN_BROWSER_CHANNEL=msedge`) |
| Status | `LOCAL_PASS / READY_FOR_REVIEW`; chưa xác nhận independent reviewer/integration window |

## 2. Phạm vi

- `RecognitionResult.tsx`: hiển thị thông báo tiếng Việt và nút **Quay lại** khi `accepted=false` với metadata đúng version; tuyệt đối không render text, classLabel hoặc confidence như bản dịch.
- `CameraRecorder.tsx`: nối retry với `startRecording`, loại thông báo và nút trùng; giữ đường quay lại khi metadata không khớp; khôi phục focus sau thay đổi state.
- `styles.css`: panel rejected và nút tối thiểu 44px, phù hợp camera overlay và viewport thấp.
- Component, fake-camera và browser tests: bảo đảm chỉ một nút retry, focus bàn phím, không gửi lại clip cũ, phải bấm **Gửi nhận diện** cho clip mới, layout không tràn màn hình `320×180`.
- Không thay đổi API, model, schema hay cách lưu media. Contract inference `v1`.

## 3. Smoke test

Từ `apps/web` (PowerShell): `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check`.

| # | Mục tiêu | Command hoặc thao tác | Kết quả thực tế / exit code | Trạng thái |
|---|---|---|---|---|
| 1 | Component/integration | `npm.cmd test -- tests/recognition/recognition-errors.test.tsx tests/recognition/RecognitionResult.test.tsx` | **32/32** passed, exit `0` | `PASS` |
| 2 | Static gate | `npm.cmd run check` — ESLint + TypeScript | lint/typecheck thành công, exit `0` | `PASS` |
| 3 | Toàn bộ unit/component | `npm.cmd run check` — Vitest | **90/90**, 8 files, exit `0` | `PASS` |
| 4 | Build | `npm.cmd run check` — Vite | 24 modules transformed, exit `0` | `PASS` |
| 5 | Browser fake-camera | `npm.cmd run check` — Playwright Edge | **39/39** desktop/mobile/landscape, exit `0`; bao gồm keyboard retry và 320×180 | `PASS` |
| 6 | Real device/API/model | Chờ checkpoint tích hợp với webcam và backend thật | Chưa đo độ trễ/chất lượng trên model thực | `NOT_RUN` |

Browser tests mock API `v1` và camera; thông báo `ECONNREFUSED 127.0.0.1:8000` ở các case không mock metadata là fallback mong đợi, không làm hỏng gate.

## 4. Artifact / link

| Loại | Tham chiếu | Ghi chú |
|---|---|---|
| Commit diff | Xem `git log --oneline --grep='CP4 T051'` và remote commit sau push | Bổ sung full SHA khi publish |
| CI | `NOT_VERIFIED` — chưa xác nhận Actions trên candidate này | Không tự nhận CI PASS |
| Test source | `apps/web/tests/recognition/{RecognitionResult,recognition-errors}.test.tsx`, `apps/web/tests/browser/camera.spec.ts` | Component/negative/fake-camera |
| Báo cáo | `docs/evidence/checkpoints/CP4/T051-p5-hien-rejected-retry-smoke.md` | Kết quả gate và rủi ro |
| API/model | Mock API `v1` + metadata test | Không commit video/raw/model binary |

## 5. Rủi ro, rollback, handoff

- Chưa chạy camera thật, backend thật, model pilot/full; cần E2E tích hợp theo T047 và đánh giá nhóm.
- Rollback bằng `git revert <commit-sha-T051>` sau khi đã publish.
- Review độc lập P2/Tín và P1/Huy trước khi đánh dấu T051 `[X]`; tiếp theo P5 triển khai T052 và T053.

## 6. Xác nhận

- [x] Đã chạy full web gate sau chỉnh sửa (exit `0`).
- [x] Stage theo đúng 8 file T051; kiểm tra `git diff --cached --check`, không có secret/raw data/model binary.
- [ ] Điền full SHA/link sau push.
- [ ] Reviewer tái chạy gate và xác nhận.

**Reviewer result**: `PENDING`.
