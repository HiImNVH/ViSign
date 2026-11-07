# CP3/CP4 T032, T047 — E2E camera giả + FastAPI thật (P1)

| Trường | Giá trị |
|---|---|
| Task | `T032` (happy path), `T047` (luồng lỗi) |
| Implementer | `P1 Huy` (trợ lý soạn theo uỷ quyền) |
| Reviewer | `P5 Hiển` (UX/test web), `P2 Tín` (backend) — **P1 không tự xác nhận** |
| Thời điểm | `2026-11-08T01:03:32+07:00` |
| Môi trường | Windows 11, Edge (`VISIGN_BROWSER_CHANNEL=msedge`), Playwright 1.64.1, uv + FastAPI fixture |

## Thiết kế

- `apps/web/playwright.e2e.config.ts` khởi động **3 backend FastAPI thật**: `fixture` (8100),
  `fixture-low-confidence` (8101), không có artifact → `degraded` (8102); và bản build web thật (preview 4180).
- Camera giả Y4M (`tests/browser/cameraFixture.ts`) → MediaRecorder thật → multipart WebM thật.
- Mỗi test chọn backend bằng `route.continue({ url })`: chỉ đổi đích request, **response là của FastAPI thật**
  (không phải HTTP-only mock theo yêu cầu T032).
- Ngoại lệ có ghi rõ: `SERVICE_BUSY` dùng một phản hồi điều khiển 503 theo contract vì fixture xử lý quá nhanh
  để tạo tranh chấp thật; lần gửi lại đi tới backend thật.

## Vị trí file (lệch `tasks.md` cũ)

`tasks.md` ghi `tests/e2e/` ở gốc repo, nhưng Playwright và dependency chỉ có trong `apps/web`; test đặt tại
`apps/web/tests/e2e/` và `tasks.md` đã sửa đường dẫn T032/T047 (điểm lệch P2 nêu từ CP1).

## Kết quả

`cd apps/web; $env:VISIGN_BROWSER_CHANNEL='msedge'; npm run test:e2e` → **6 passed (40 s)**:

| Test | Kiểm |
|---|---|
| T032 happy path | Quay xong chưa gửi; một POST multipart chứa chữ ký EBML WebM; 200 `accepted`, `X-Request-ID` = `requestId`, không có landmark; UI hiện "Cảm ơn", cảnh báo chưa sẵn sàng demo, dòng bản dịch |
| T047 từ chối quyền camera | Thông báo khôi phục được, không có upload |
| T047 low-confidence | Backend thật trả `accepted=false`, `classLabel=null`; UI hiện câu từ chối; không nối vào bản dịch |
| T047 clip hỏng + gửi lại | Backend thật trả 415/422; UI không render `message`/`code` của server; gửi lại chủ động → 200 |
| T047 dịch vụ bận | Câu tiếng Việt ổn định, không lộ text server; gửi lại chủ động tới backend thật → 200 |
| T047 backend degraded | `model-info` 503; UI hướng dẫn, không upload |

Lint, typecheck PASS. CI chưa chạy E2E (cần browser + backend); chạy local bằng lệnh trên.

**Reviewer result**: `PENDING` (P5/P2).
