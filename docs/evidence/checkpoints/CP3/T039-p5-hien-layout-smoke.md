# CP3 T039 — Camera lớn và văn bản dịch bên dưới

- Owner: P5 Hiển; reviewer P2/Tín, P1/Huy — PENDING.
- Ngày: 2026-11-07, Asia/Saigon.
- Yêu cầu: camera lớn, chữ dịch bên dưới; bỏ bố cục hai cột.
- Đồng bộ: fetch `origin/main` tại `18a07aef641b424ddf4772249623b1bc04a4b926`;
  remote-only count 0, local base `edd328de4e1cdf9de31fdf808369a44e30bb2c7a`.
- Local commit/link GitHub: PENDING trước push; không có integration window nên chưa push.

## Thay đổi

Camera rộng toàn khung, height theo viewport có giới hạn; nút điều khiển đặt ngay dưới.
Vùng Văn bản dịch luôn nằm dưới nút điều khiển. Trạng thái quay và riêng tư nằm tiếp bên dưới,
không dùng sidebar. Tắt camera được gom cùng nhóm thao tác; không đổi lifecycle/quyền/capture.
Vùng dịch hiển thị “Chưa có bản dịch.” vì chưa có API; không tạo bản dịch giả.
Giữ `object-fit: contain`, nên hình xem trước không bị cắt mất tay khi tỷ lệ camera khác vùng hiển thị.

## Kiểm tra

Từ `apps/web/`:

```powershell
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm.cmd run check
```

- PASS: lint, strict typecheck, 32 unit/component tests, build, 8 browser tests; exit 0.
- Browser xác nhận camera rộng hơn 75% viewport và thứ tự camera → actions → vùng dịch
  ở idle, preview, captured cho desktop 1440×900 và mobile 320×640; không tràn ngang.
- Các test quyền camera, capture/cancel/reset/cleanup, focus, Escape, reduced motion và no-upload vẫn đạt.
- Đã xem ảnh desktop/mobile sinh bởi browser test. Màn hình nhỏ cho phép cuộn tự nhiên.
- Source/config nền không đổi dependency hoặc lockfile. Không sửa camera session/limits.
- NOT_RUN: API/model, webcam/điện thoại thật; giới hạn browser/Node như evidence T039 chính.

Ảnh tái lập bằng test tại
`apps/web/test-results/browser-camera-explicitly--62798-M-clip-then-releases-camera-{desktop,mobile}/camera-captured.png`;
chỉ chứa frame tổng hợp, không có video cá nhân; output/fixture được ignore.

Rollback: revert riêng commit layout; không reset/force-push `main`.
Spec Kit: T039 local; task/checkpoint vẫn mở đến khi có review/tích hợp. Không có extension hook.

**Status**: PASS local / NOT_PUSHED. **Reviewer**: PENDING.
