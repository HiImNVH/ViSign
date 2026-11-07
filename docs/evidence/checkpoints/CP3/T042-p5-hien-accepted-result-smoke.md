# CP3 T042 — Accepted result view (P5 Hiển)

Ngày: 2026-11-07. Phạm vi: component kết quả được chấp nhận của P5; chưa ghép API vào `App.tsx` (T043).

## Triển khai

- Tạo `apps/web/src/features/recognition/RecognitionResult.tsx`, nhận prediction và metadata model-info khớp `modelVersion`; chỉ hiển thị khi server trả `accepted=true`, có nội dung/nhãn hợp lệ và confidence thuộc `[0, 1]`.
- Render văn bản tiếng Việt từ API bằng React text, confidence phần trăm, disclaimer `vi.disclaimer`. Không tự suy diễn accepted bằng ngưỡng confidence.
- Với `demoReady=false`, phân biệt `fixture` (tích hợp nội bộ), `pilot` (thí điểm giới hạn) và `full` chưa đạt gate; liệt kê đúng `meanings` từ model-info. Nếu metadata không hợp lệ, thiếu hoặc lệch phiên bản thì không hiển thị kết quả cũ. Pilot/fixture vẫn cảnh báo nếu metadata không nhất quán báo `demoReady=true`.
- Giữ bố cục camera/điều khiển một khung hình, không cuộn trang. Với viewport siêu thấp (cao ≤260px), dùng disclaimer ngắn vẫn nói rõ tính thử nghiệm; bản đầy đủ được hiển thị ở viewport thông thường và trong mục Hướng dẫn.
- Không đổi `CameraRecorder` và `App.tsx`; T043 sẽ truyền prediction và model-info thật vào component mới. Không cài rejected/retry UI của T051.

## Kiểm thử

- Viết test trước implementation và xác nhận thất bại do component chưa tồn tại. Sau triển khai, 22/22 test mới PASS: accepted/validation, confidence bounds/rounding, disclaimer, phiên bản mismatch, cả ba artifact, readiness không nhất quán, empty meanings, rerender và nội dung HTML nguy hiểm được escape.
- `cd apps/web`; `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check`: **ESLint PASS**, **TypeScript PASS**, **80/80 Vitest PASS** (7 files), **Vite production build PASS**, **24/24 Playwright Edge PASS**.
- Browser bổ sung 3 test hiển thị pilot tại desktop/mobile/landscape, có kiểm tra riêng viewport `320×180`: translation và controls nằm trong camera, không chồng nhau, không sinh scroll.

## Handoff

T042 **IMPLEMENTED / READY_FOR_REVIEW**. Chờ P2/Tín, P1/Huy review và integration T043 trước khi đánh dấu `[X]` trong `specs/001-vsl-recognition-mvp/tasks.md`. Browser hiện kiểm tra presentational component bằng markup mô phỏng; không được xem là bằng chứng request API thật hoặc chất lượng model.
