# US6 T100–T104 — Live transcript and local history

| Trường | Giá trị |
|---|---|
| Owner | P5 Hiển |
| Ngày | 2026-11-08 |
| Task | US6 T100–T104 |
| Reviewer | P1/Huy (spec/E2E), P2/Tín (privacy/API) — chờ review độc lập |
| Status | `TEST_PASS / READY_FOR_REVIEW` |
| Commit | `CP6 T100-T104(web): add local transcript and history` (tra `git log` lấy full SHA) |

## Phạm vi

- Transcript chỉ thêm các kết quả `accepted=true` hợp lệ theo thứ tự trong phiên; rejected/error/cancel/stale không thêm vào.
- `localStorage` chỉ chứa năm trường `requestId`, `text`, `confidence`, `modelVersion`, `createdAt`, schema version 1, khoá `visign.translation-history.v1`; TTL 24 giờ, chống trùng `requestId`, kiểm tra schema. Không lưu clip, frame, landmark hay gửi history tới API.
- History panel có thời gian, confidence, modelVersion, xoá lịch sử có xác nhận. Dịch trực tiếp vẫn hoạt động khi storage không khả dụng.
- Browser E2E dùng camera giả lập + mock API, reload giữ lịch sử và đồng hồ mô phỏng 24 giờ.
- US2 T074–T075 HTTP compatibility nằm ở commit `49448f8` và evidence `docs/evidence/checkpoints/CP4/T074-T075-p5-hien-smoke.md`.

## Gate

Windows/PowerShell, `D:\Projects\ViSign\apps\web`, Chromium Edge `msedge`, mock API + synthetic fake-camera fixture.

```powershell
$env:VISIGN_BROWSER_CHANNEL='msedge'
npm.cmd run check
```

**Kết quả thực tế (2026-11-08, exit code `0`)**:

| Gate | Kết quả |
|---|---|
| ESLint | **PASS** |
| TypeScript `tsc --noEmit` | **PASS** |
| Vitest unit/component | **165 PASS, 4 SKIP** (11 files pass, 1 file skip) |
| Vite production build | **PASS**, 28 modules transformed |
| Playwright Edge browser | **54 PASS, 3 SKIP** (3 bài live backend bị skip trong môi trường mock) |
| Browser T104 desktop/mobile/landscape | **6 PASS** |
| `git diff --check` | **PASS** |

Sử dụng mock API và fake-camera, không sử dụng webcam thật hoặc predictor thật.

## Rủi ro và handoff

- Cần P1/Huy review UI/E2E và P2/Tín kiểm tra không gửi lịch sử lên backend.
- Commit gộp lịch sử `231f8d249a0edc1f8fb98a3ced70da47c575aa4e` đã được revert trước khi khôi phục hai task thành các commit riêng, giữ lịch sử public. Không force push.
- Giữ task mở cho đến khi review độc lập; không tự đánh dấu `VERIFIED`.
