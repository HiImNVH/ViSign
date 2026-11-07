# T039 — sửa focus không ổn định

- Review P2 ghi nhận unit test đôi lúc thấy trạng thái mới trước khi `useEffect` chuyển focus; xem `T039-p5-hien-smoke.md`, mục independent review.
- Chuyển quản lý focus sang `useLayoutEffect`, giữ nguyên điều kiện bảo vệ dialog và control còn tồn tại. Browser test chờ trạng thái tương ứng trước khi kiểm tra focus.
- Windows / Node 26.7.0: test `recognition-flow.test.tsx` chạy 30 lần độc lập: 30/30 PASS; lint, typecheck, 47 unit tests và build PASS; Playwright với Edge: 21/21 PASS trên desktop, mobile và landscape.
- Browser test dùng camera giả; CI trên commit mới và review độc lập của P2/P1 còn chờ. Cập nhật README theo Node engines đã sửa tại CP1.
