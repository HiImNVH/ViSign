# CP7 / T090 — P5: follow-up FE-T090-01..06

Ngày: 2026-11-08, Asia/Ho_Chi_Minh. Phạm vi: `apps/web` trên repo ViSign; đây là
follow-up sửa code cho review đã ghi tại `docs/architecture-quality-report.md` §7.

## Phạm vi và bằng chứng

| ID | File / xác minh |
|---|---|
| 01 — storage cleanup | `translationHistory.ts`, `HistoryPanel.tsx`, `translationHistory.test.ts`, `transcript-history.test.tsx`: giữ dữ liệu hợp lệ và cho phép xoá/thử lại khi ghi lỗi. |
| 02 — multi-tab | `useRecognition.ts`, `useRecognition.test.tsx`, `browser/transcript-history.spec.ts`: storage event append/clear, huỷ prediction khi clear từ tab khác, bỏ response đến muộn. |
| 03 — contract | `recognitionController.ts`, `useRecognition.ts`, `CameraRecorder.tsx`, `HistoryPanel.tsx`: tách interface hook và component; camera session private. |
| 04 — production fidelity | Xoá `RecognitionOverlay.tsx`; `browser/camera.spec.ts` dùng API fixture/capture UI thật; test unit chuyển sang `CameraRecorder`. |
| 05 — session dài | `TranscriptPanel.tsx`, `HistoryPanel.tsx`: 30 mục transcript cuối và 50 mục lịch sử/trang; Vitest 100/1.200 transcript; Playwright 1.200 mục history, 50→100 row và toàn bộ 1.200 được lưu. Raw payload fixture dưới 500 KB, không đặt giới hạn lưu tuỳ tiện trong TTL. |
| 06 — focus/copy | `CameraRecorder.tsx`, `RecognitionResult.tsx`, `CameraHelp.tsx`, `styles.css`: button refs, class `app-dialog`, giới hạn camera từ source constant. |

## Gate local

- `npm.cmd run lint`: PASS.
- `npm.cmd run typecheck`: PASS.
- `npm.cmd run build`: PASS, Vite 33 modules transformed.
- `npm.cmd test`: **175 PASS, 4 SKIP**, 12 test files passed, 1 file skipped.
- `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run test:browser`: **93 PASS, 12 SKIP**,
  3 projects desktop/mobile/landscape, 105 cases. Skips gồm screenshot opt-in và live backend.
- `git diff --check`: PASS ở lượt trước cập nhật evidence.

## Giới hạn và bàn giao

Các bài camera/browser dùng camera giả và response fixture. Chưa thử webcam thật, screen reader
thật, stress profile trên thiết bị yếu, quota gần đầy với dữ liệu thật hoặc đo latency model.
Hai tab ghi đồng thời qua localStorage vẫn có race last-writer-wins; hiện bảo đảm refresh theo
event của snapshot mới nhất và huỷ request khi clear, chưa có giao dịch append nguyên tử.
Các kiểm tra này không thay thế review và nghiệm thu độc lập của P1/P2.

Trạng thái: sửa 6 hạng mục tại local, chưa push trong lượt follow-up này.
