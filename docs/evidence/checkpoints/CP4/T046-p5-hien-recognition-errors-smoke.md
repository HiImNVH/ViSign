# CP4 T046 — Negative recognition component tests (P5 Hiển)

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint / task | `CP4 / T046` (`US2`) |
| Owner | `P5 Hiển` |
| Reviewer | `P2 Tín`, `P1 Huy` — chờ kiểm thử độc lập |
| Commit | `CP4 T046(web): cover negative recognition flows`; full SHA được bổ sung sau commit |
| Ngày/giờ | `2026-11-07T21:31:45+07:00` |
| Môi trường | Windows / PowerShell, Node `26.7.0`, npm `11.19.0`, Vitest `5.0.5`, Playwright `1.64.1`, Edge (`VISIGN_BROWSER_CHANNEL=msedge`) |
| Status | `PASS` tại local; chờ reviewer xác nhận |

## 2. Phạm vi

- Thêm `apps/web/tests/recognition/recognition-errors.test.tsx`, sử dụng `useRecognition` và `CameraRecorder` thật với `getUserMedia`, `MediaRecorder` và inference API giả lập.
- Tám ca kiểm thử: từ chối quyền camera và thử lại; hủy khi quyền còn chờ và thu hồi stream đến muộn; hủy quay không gửi clip; dự đoán `accepted=false` không hiển thị bản dịch; `SERVICE_BUSY`/`MODEL_NOT_READY` 503 không rò mã lỗi và chỉ gửi lại khi bấm; mất metadata chặn upload và chỉ tải lại khi yêu cầu; hủy request đang tải lên abort và bỏ qua response đến muộn.
- Không thay đổi mã ứng dụng, API, model, schema hay dữ liệu. Contract web hiện dùng API `v1`.

## 3. Smoke test

Lệnh chạy từ `apps/web` (PowerShell): `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check`.

| # | Mục tiêu | Command hoặc thao tác | Kết quả thực tế / exit code | Trạng thái |
|---|---|---|---|---|
| 1 | Negative component cases | `npm.cmd test -- tests/recognition/recognition-errors.test.tsx` | **8/8** passed, exit `0` | `PASS` |
| 2 | Static gate | `npm.cmd run check` (ESLint + `tsc --noEmit`) | lint/typecheck thành công, exit `0` | `PASS` |
| 3 | Unit/component toàn web | `npm.cmd run check` (Vitest) | **88/88** passed, 8 test files, exit `0` | `PASS` |
| 4 | Build | `npm.cmd run check` (Vite production build) | 24 modules transformed, exit `0` | `PASS` |
| 5 | Browser fake-camera | `npm.cmd run check` (Playwright Edge) | **39/39** passed ở desktop/mobile/landscape, exit `0` | `PASS` |
| 6 | Real camera/API/model smoke | Chưa chạy vì không có môi trường tích hợp camera/backend/model thật trong checkpoint này | Chưa xác nhận phần cứng, API thực, latency/accuracy | `NOT_RUN` |

Test chỉ mock quyền/stream, recorder và API theo hợp đồng. Thông báo `ECONNREFUSED 127.0.0.1:8000` ở một số browser cases là fallback mong đợi khi backend không chạy; toàn bộ browser assertions đều PASS. T047 E2E negative paths thuộc P1/Huy và không được thay thế bằng T046.

**Pre-commit sync:** `git fetch origin main` thấy 6 commit mới (`44b1405` → `6b411aa`) thuộc API/spec/evidence P1/P2; stash đúng 3 file T046, `git pull --rebase origin main` fast-forward và khôi phục candidate không conflict. Sau đồng bộ, chạy lại `npm.cmd run check`: lint/typecheck/build PASS, 88/88 Vitest PASS, 39/39 Edge PASS, exit `0`. Fetch lần cuối thấy thêm commit CP7 cloud docs `a26aa5d`; thực hiện stash/pull/reapply lần nữa không conflict, frontend không đổi.

## 4. Artifact / link

| Loại | Tham chiếu | Ghi chú |
|---|---|---|
| Commit diff | Bổ sung full SHA/link sau commit/push | Review theo micro-commit |
| CI | `NOT_RUN` — chờ push/CI workflow | Chưa tự nhận CI pass |
| Test source | `apps/web/tests/recognition/recognition-errors.test.tsx` | 8 negative component cases |
| Báo cáo | `docs/evidence/checkpoints/CP4/T046-p5-hien-recognition-errors-smoke.md` | Commands và kết quả tái lập |
| API/model | Mock API `v1` + metadata pilot giả lập | Không có binary/video thật trong Git |

## 5. Rủi ro, rollback, handoff

- Chưa được kiểm chứng trên camera/device thật, backend đang chạy hoặc GRU pilot/full; để T047 và tích hợp nhóm xác minh các tầng đó.
- Có thể revert riêng commit T046 nếu test không còn phù hợp contract khi tích hợp.
- P2/Tín và P1/Huy cần review độc lập; việc tick `[X]` phụ thuộc verification theo `docs/team/git-checkpoints.md`.
- Push chờ integration window của P1/Huy: `members/p1-huy/README.md` hiện ghi `ACTIVE` cho P1, chưa có bàn giao window T046 cho P5.

## 6. Xác nhận

- [x] Owner đã chạy full web gate sau chỉnh sửa test.
- [ ] Kiểm tra staged diff không chứa secret/raw video/model binary.
- [ ] Full SHA và link public được điền sau push.
- [ ] Reviewer tái chạy gate và xác nhận.

**Reviewer result**: `PENDING`.
