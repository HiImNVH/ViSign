# P5 Hiển — T074/T075 HTTP compatibility + T100–T104 transcript/history

| Trường | Giá trị |
|---|---|
| Owner | P5 Hiển |
| Ngày | 2026-11-08 |
| Phạm vi | US2 T074–T075; US6 T100–T104, frontend `apps/web` |
| Reviewer | P1/Huy (spec, E2E), P2/Tín (API, privacy); **chưa review độc lập** |
| Trạng thái | `TEST_PASS / READY_FOR_REVIEW (LOCAL)`; **chưa commit/push/merge** |

## Hành vi đã triển khai

- API `404`/`405` có typed error, giữ status/code/requestId, hiển thị thông báo tiếng Việt ổn định, không lộ raw `message`/`detail`. URL health/model-info/predictions canonical; không tự submit lại khi endpoint lỗi. Catalog `403` để dành cho backend tương lai, chưa trình bày như trạng thái MVP; `304` chờ ETag contract.
- Mỗi kết quả nhận diện `accepted=true` hợp lệ nối một ý nghĩa vào bản dịch trực tiếp theo thứ tự trong phiên. `rejected`, lỗi, clip hủy và response cũ không nối. Đây là các ý nghĩa nối nhau, chưa phải câu có ngữ pháp.
- Chỉ metadata của bản dịch được chấp nhận nằm trong `localStorage` `visign.translation-history.v1`, version 1, đúng 5 field: `requestId`, `text`, `confidence`, `modelVersion`, `createdAt`. Có loại dữ liệu sai, chống trùng `requestId`, TTL **24 giờ**, xoá toàn bộ có xác nhận; không lưu hay gửi video/frame/landmark/lịch sử lên API.
- Khi bộ nhớ trình duyệt bị chặn/đầy, dòng bản dịch trong phiên vẫn hoạt động và lịch sử hiển thị cảnh báo. Reload chỉ khôi phục lịch sử metadata, không khôi phục transcript của phiên trước.
- Giao diện một màn hình, khung camera lớn; kiểm tra chiều ngang/dọc không cuộn ở viewport `320×180`.

## Local smoke evidence

Chạy từ `D:\Projects\ViSign\apps\web` (PowerShell):

```powershell
$env:VISIGN_BROWSER_CHANNEL='msedge'
npm.cmd run check
```

Kết quả `npm.cmd run check` (exit `0`):

| Gate | Kết quả |
|---|---|
| ESLint | **PASS** |
| TypeScript `tsc --noEmit` | **PASS** |
| Vitest unit/component | **165 PASS, 4 SKIP**, 11 files pass, 1 file skip |
| Vite production build | **PASS**, 28 modules transformed |
| Playwright Edge browser đầy đủ | **54 PASS, 3 SKIP** (3 live backend tests skip theo cấu hình) |
| T104 Playwright tập trung | **6/6 PASS**, desktop/mobile/landscape |
| `git diff --check` | **PASS** (chỉ cảnh báo Git sẽ chuẩn hóa LF/CRLF) |

Smoke dùng API mock và video fake-camera; chưa kiểm tra bằng webcam thật và predictor/backend triển khai thực tế. Dữ liệu cá nhân, video hay model weights không đưa vào bằng chứng này.

## Handoff

- T074/T075: `src/services/inferenceApi.ts`, `src/content/vi.ts`, `src/features/recognition/RecognitionError.tsx`; `tests/inferenceApi.test.ts`, `tests/recognition/recognition-errors.test.tsx`.
- T100–T104: `src/features/recognition/{translationHistory.ts,TranscriptPanel.tsx,HistoryPanel.tsx,useRecognition.ts}`, `src/App.tsx`, `src/styles.css`; unit/component `tests/recognition/{translationHistory,transcript-history}.test.ts(x)`, browser `tests/browser/transcript-history.spec.ts`.
- P1/P2 review lại API contract, storage/privacy và transcript E2E. Không đánh dấu `specs/001-vsl-recognition-mvp/tasks.md` `[X]` hoặc `P1_VERIFIED` trước review; commit/push theo integration window.
