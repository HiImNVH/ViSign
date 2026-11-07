# CP7 T090 — P5 Hiển: frontend architecture review evidence

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint / task | CP7 / T090 — review chất lượng kiến trúc FE/BE/AI; phần P5 đóng góp FE |
| Owner / reviewer | P5 Hiển / P1 Huy, P2 Tín (độc lập, đang chờ) |
| Commit | [`a4eb02cc45a1d6723c6e55d0ede2254f1e3c560b`](https://github.com/HiImNVH/ViSign/commit/a4eb02cc45a1d6723c6e55d0ede2254f1e3c560b) |
| Ngày / múi giờ | 2026-11-08T02:31:00+07:00, Asia/Ho_Chi_Minh |
| Base khi review | `main` / `a214a3c`, đã `git pull --rebase origin main` sạch trước khi sửa |
| Môi trường | Windows PowerShell, Node `v26.7.0`, npm `11.19.0`, Playwright Microsoft Edge `msedge` |
| Status | `PUSHED / READY_FOR_REVIEW`; reviewer `PENDING` |

## 2. Phạm vi

- Bổ sung `docs/architecture-quality-report.md` §7: sơ đồ chiều phụ thuộc FE, cách tổ chức
  component/state, phân tách API/camera/storage, tái sử dụng UI, CSS và các rủi ro mở rộng.
- Ghi 6 phát hiện có file/dòng liên quan cùng thứ tự xử lý tại FE-T090-01..06; phân biệt
  lỗi suy ra từ luồng mã với rủi ro chưa tái hiện.
- Đối chiếu 20 FE test files và guard metadata hiện tại `meanings.length <= 10` để P1 xác nhận
  hai nhận định của bản báo cáo đầu.
- Không thay đổi TS/JSX, CSS, backend, AI, hành vi storage, API contract hoặc test trong T090.

## 3. Smoke và evidence

| # | Mục tiêu / cách tái lập | Kết quả thực tế | Trạng thái |
|---|---|---|---|
| 1 | `cd apps/web; $env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check` — lint/typecheck/build | ESLint và TypeScript sạch; Vite build 28 modules, exit 0; tổng gate exit 0 | PASS |
| 2 | Vitest trong `npm.cmd run check` | 11 test files passed, 1 skipped; 168 tests passed, 4 skipped, exit 0 | PASS |
| 3 | Playwright Edge trong `npm.cmd run check` | 84 passed, 12 skipped, 3 projects (desktop/mobile/landscape), exit 0 | PASS |
| 4 | `rg --files apps/web/tests` lọc `\.(spec\|test)\.[tj]sx?$` | 20 test files; quan sát trong repo, không thay đổi file | PASS |
| 5 | Review `translationHistory.ts`, `useRecognition.ts`, `CameraRecorder.tsx`, `HistoryPanel.tsx`, `RecognitionResult.tsx`, `RecognitionOverlay.tsx`, `inferenceApi.ts`, `styles.css` | Các vấn đề và hành động ghi tại §7 báo cáo; có dòng nguồn, phân mức và chủ sở hữu | PASS |
| 6 | Benchmark session dài, test tab đồng thời, camera/screen reader thật | Ngoài phạm vi review tĩnh, cần bài kiểm thử thực nghiệm theo FE-T090-02/05 và T063/T071 | NOT_RUN |

**Giới hạn kiểm chứng**: Gate Playwright dùng camera/response tổng hợp, không thay cho thiết bị
thật hoặc phép đo độ trễ model. Không xem vấn đề nhiều tab hoặc hiệu năng phiên dài là lỗi đã tái hiện.
Các skip là screenshot capture opt-in và live backend, không được coi là pass.

## 4. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit | [T090 frontend architecture review](https://github.com/HiImNVH/ViSign/commit/a4eb02cc45a1d6723c6e55d0ede2254f1e3c560b) | Chỉ có thay đổi report, member log và evidence |
| Report | `docs/architecture-quality-report.md` §7 | Phát hiện FE-T090-01..06 và hành động P5 |
| Test evidence | `apps/web/tests/` | Unit và Playwright Edge gate; số liệu mục 3 |
| GitHub Actions | NOT_RUN tại máy local; sau push kiểm tra workflow T091 riêng | T090 không đổi CI |
| API/cloud/model | NOT_RUN: review FE tĩnh, không cần deploy hoặc model artifact | Không thay đổi pipeline |

## 5. Rủi ro, rollback, handoff

- Ưu tiên P5 tiếp theo: FE-T090-01 (history cleanup write failure) kèm regression; tiếp theo
  multi-tab semantics, interface view/actions và gỡ duplicate overlay theo micro-commit riêng.
- P1/P2 kiểm tra các phát hiện §7, xác nhận điểm count test và giới hạn 10 meanings trong báo cáo
  hiện có trước khi nghiệm thu T090.
- Rollback nếu báo cáo sai: revert riêng micro-commit T090; không ảnh hưởng mã chạy.
- Blocker đóng task: reviewer độc lập chưa xác nhận; `tasks.md` vẫn `[ ]`.

## 6. Xác nhận

- [x] Owner đã chạy full web gate trên nguồn hiện hành sau sync `origin/main`.
- [x] Không stage video/landmark/model, secret hoặc artifact runtime.
- [x] Full SHA và link được cập nhật sau push (follow-up evidence).
- [ ] Reviewer tái lập kết quả và ghi đánh giá.

**Reviewer result:** `PENDING`. **Reviewer note:** Chờ P1/P2 đọc §7 và xác nhận gate/action.

## Independent review — P1/Huy (2026-11-08)

- Phần §1–§6 do P1 viết, đã được P5 review chéo; P1 review §7 của P5.
- Kiểm chứng trong mã: đếm `apps/web/tests` = **20 file** test (P1 sửa §1 từ 17 → 20); `isModelInfo` chặn
  `meanings.length <= 10` (P1 bổ sung giới hạn này vào §5); FE-T090-01 đúng: trong `translationHistory.ts`
  `load()`, `setItem`/`removeItem` của bước dọn dẹp nằm chung `try` ngoài nên khi ném lỗi trả `entries: []`,
  mất cả các entry đã đọc hợp lệ; FE-T090-04 đúng: `RecognitionOverlay` chỉ còn được import trong test
  (`camera.spec.ts:338`, `recognition-overlay.test.tsx`), app thật dùng `RecognitionResult`.
- Gate web đã chạy cùng lượt review T063/T088 trên cùng mã nguồn (T090 không đổi code): unit 165 passed/4 skipped,
  Playwright T063 + T088 lặp 3 lần 90/90; CI `f9232cd` xanh.

**Reviewer result**: `P1_VERIFIED`, tick `[X]` T090 (báo cáo kiến trúc review chéo P1 ↔ P5). Các fix FE-T090-01..06
là việc tiếp theo của P5, ưu tiên FE-T090-01 kèm regression test.

## Independent review FE-T090-01..06 — P1/Huy (2026-11-08, `6f2dfd4`…`3b9a65a`)

- `npm run check` trên Edge: lint/typecheck/build sạch, Vitest **175 passed / 4 skipped**, Playwright **93 passed**, exit 0; CI xanh.
- Sáu micro-commit khớp sáu hành động trong §7.2 (giữ lịch sử khi cleanup lỗi, đồng bộ đa tab, tách contract
  controller, bỏ fixture overlay cũ, giới hạn hiển thị transcript/history, focus dialog bằng ref).

**Reviewer result**: `P1_VERIFIED` cho FE-T090-01..06 (T090 đã `[X]`).
