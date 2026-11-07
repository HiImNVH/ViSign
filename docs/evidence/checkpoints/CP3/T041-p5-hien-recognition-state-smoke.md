# CP3 T041 — Recognition state machine (P5 Hiển)

Ngày: 2026-11-07. Phạm vi: `apps/web/src/features/recognition/useRecognition.ts` và unit tests cho hook.

## Kết quả triển khai

- Ghép trạng thái `idle`, `permission`, `preview`, `recording`, `stopping`, `captured` của một `CameraSession` với `submitting`, `result` và API `error`.
- Tải `GET /api/v1/model-info`, giữ `artifactKind`/`modelVersion`, chỉ gửi `POST /api/v1/predictions` sau thao tác `submit()` của người dùng khi metadata hợp lệ; không chọn endpoint theo artifact kind.
- Ngăn upload trùng clip sau kết quả, ngăn hai request đang chạy cùng lúc; retry sau lỗi chỉ khi người dùng chủ động gọi `submit()`.
- So khớp `modelVersion` giữa model-info và prediction, loại kết quả sai phiên bản, tải lại metadata, không tự upload lại.
- Abort request khi cancel/reset/unmount/pagehide hoặc camera đổi clip/trạng thái; chặn phản hồi cũ khi camera session thay đổi trước lúc React render lại. Khi quay về trang từ bfcache, metadata được tải lại.
- Không giữ `Blob` video trong trạng thái prediction. `WeakMap<Blob, id>` dùng định danh capture, giúp clip có thể được thu hồi sau khi camera giải phóng; Blob chỉ còn trong `CameraSession` lúc clip còn được giữ và trong request đang chạy.

## Kiểm thử

Chạy tại `apps/web` với PowerShell đặt `$env:VISIGN_BROWSER_CHANNEL='msedge'`, sau đó `npm.cmd run check`:

- ESLint: PASS.
- TypeScript: PASS.
- Vitest: **58/58 PASS** (6 test files), trong đó **11/11 PASS** cho `useRecognition.test.tsx`.
- Vite production build: PASS.
- Playwright Microsoft Edge: **21/21 PASS** (desktop/mobile/landscape); regression gate cho camera/App hiện hữu.

Hook tests dùng API/camera mô phỏng để kiểm tra chuyển trạng thái, metadata unavailable/refresh, xác nhận artifact pilot, rejected result, lỗi retry, duplicate submission, stale response, version mismatch, cancel/reset, pagehide/bfcache và unmount. Browser suite hiện tại chưa thực thi hook qua App vì nối UI là T043.

## Bàn giao

T041 **IMPLEMENTED_LOCAL / READY_FOR_REVIEW**. Chưa có review độc lập từ P2/P1; chưa push, chưa đánh dấu `[X]` trong task checklist chung. T042 (accepted result view) và T043 (App integration), kiểm thử với API/model thực tế và nghiệm thu trên thiết bị thật được theo dõi riêng; không lấy browser regression hiện tại làm bằng chứng tích hợp nhận diện.
