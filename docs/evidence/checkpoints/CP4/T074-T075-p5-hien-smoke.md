# CP4 T074–T075 — Frontend HTTP compatibility

| Trường | Giá trị |
|---|---|
| Owner | P5 Hiển |
| Ngày | 2026-11-08 |
| Task | US2 T074–T075 |
| Reviewer | P1/Huy (spec/E2E), P2/Tín (API) — đang chờ review độc lập |
| Status | `TEST_PASS / READY_FOR_REVIEW` |
| Commit | `CP4 T074-T075(web): handle API compatibility errors` (tra `git log` để lấy full SHA) |

## Scope

- Typed `404/405` từ HTTP transport, giữ status/code/requestId, không render raw server body.
- Stable Vietnamese messages trong `content/vi.ts`/`RecognitionError.tsx`; `403` reserved, `304` chờ ETag contract.
- Khi POST nhận `404`, hủy clip hiện tại và giữ lời nhắc an toàn; không tự gửi lại request. Canonical API paths không có trailing slash.
- Transport/component tests tại `apps/web/tests/inferenceApi.test.ts` và `apps/web/tests/recognition/recognition-errors.test.tsx`.
- US6 T100–T104 (transcript, localStorage, history) có commit và evidence riêng.

## Gate đã chạy

Windows/PowerShell, `D:\Projects\ViSign\apps\web`, Edge Chromium fake camera và mock API, ngày 2026-11-08.

```powershell
$env:VISIGN_BROWSER_CHANNEL='msedge'
npm.cmd run check
```

Exit `0`: ESLint PASS, `tsc --noEmit` PASS, Vitest **159 PASS/4 SKIP**, Vite build PASS (25 modules), Playwright **48 PASS/3 SKIP** trên desktop/mobile/landscape. Ba browser live-backend cases skip theo cấu hình; chưa thử webcam thật hay predictor thật. `git diff --check` PASS.

## Handoff và provenance

- Reviewer kiểm tra 404/405 contract, không tự submit, không lộ thông báo framework, camera lifecycle khi 404.
- Commit gộp `231f8d249a0edc1f8fb98a3ced70da47c575aa4e` đã được hoàn tác bằng `git revert` trước khi tái lập từng task riêng. Lịch sử remote không được sửa/force push.
- Giữ task mở đến khi P1/P2 review; không đưa raw video, landmark hay secret lên Git.
