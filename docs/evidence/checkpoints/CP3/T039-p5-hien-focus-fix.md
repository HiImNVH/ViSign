# T039 — sửa focus không ổn định

- Review P2 ghi nhận unit test đôi lúc thấy trạng thái mới trước khi `useEffect` chuyển focus; xem `T039-p5-hien-smoke.md`, mục independent review.
- Chuyển quản lý focus sang `useLayoutEffect`, giữ nguyên điều kiện bảo vệ dialog và control còn tồn tại. Browser test chờ trạng thái tương ứng trước khi kiểm tra focus.
- Windows / Node 26.7.0: test `recognition-flow.test.tsx` chạy 30 lần độc lập: 30/30 PASS; lint, typecheck, 47 unit tests và build PASS; Playwright với Edge: 21/21 PASS trên desktop, mobile và landscape.
- Browser test dùng camera giả; CI trên commit mới và review độc lập của P2/P1 còn chờ. Cập nhật README theo Node engines đã sửa tại CP1.

## Independent re-review — P2/Tín

Review time `2026-11-07T19:20+07:00` trên `origin/main` `9abd2f3` (chứa `39209c7`); Windows, **Node 24.18.0** (khác Node 26.7.0 của P5), Edge.

| Gate | Kết quả |
|---|---|
| Thay đổi | `CameraRecorder.tsx` dùng `useLayoutEffect` cho quản lý focus, giữ điều kiện bảo vệ dialog/control; browser test chờ trạng thái trước khi kiểm focus — đúng đề xuất trong review P2 trước |
| Test từng flaky | `npx vitest run tests/recognition/recognition-flow.test.tsx` × 30: **30/30 pass** (trước sửa 13/15) |
| Web | `npm ci`, lint, typecheck, build: PASS; Vitest 5 file / 47 test PASS |
| Browser | `VISIGN_BROWSER_CHANNEL=msedge npx playwright test`: 21/21 PASS |
| CI | Run trên `fc7d606` (trước sửa) đỏ ở đúng assertion này; các run sau `39209c7` (`5d09f50`, `e1ecec3`, `9abd2f3`) success |

**Reviewer result**: `VERIFIED` (P2) — đóng mục `CHANGES_REQUESTED` trong review P2 tại `T039-p5-hien-smoke.md`.
