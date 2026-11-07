# T039 — Rà soát trước push

Ngày 2026-11-07; owner P5 Hiển. Người dùng yêu cầu kiểm tra kỹ rồi push các commit đã hoàn thiện.
Đồng bộ `origin/main` tại `ffb365ad27657c01a923f58824d96773ee5aaae0` trước commit/push.
Các cập nhật sau gate chỉ là evidence/member docs, không thay source đã kiểm tra.

- Web: clean `npm ci`, lint/typecheck/build và 42 unit/component tests PASS.
- Browser Edge: 21 tests PASS, gồm camera thật với Y4M tổng hợp, accepted-overlay fixture,
  viewport 320×180 tương đương vùng hiển thị nhỏ khi zoom, và giữ focus khi tự dừng quay.
- Node 24.22.2 giống major CI: lint/typecheck, 42 tests và build PASS trước bản sửa nhỏ cuối;
  bản sửa cuối được lint/typecheck/unit/build/browser gate kiểm tra lại trên Node 26.7.0.
- API sau đồng bộ runtime settings mới: Ruff/mypy PASS, 73 tests PASS.
- AI: Ruff/mypy PASS, 15 tests PASS, 5 SKIPPED vì chưa có browser/reference WebM riêng.
- Audit dependency runtime: 0 vulnerability. Không thay dependency/lockfile.
- Repository hygiene: không có raw video/model/secret bị track; không trúng mẫu private key/token đã kiểm tra.
- Spec checklist 18/18; prerequisites PASS. Không đóng task/checkpoint hoặc nhận định model đã sẵn sàng.

Review độc lập bằng subagent không thấy lỗi P0/P1; đã xử lý ba điểm P2:

1. Bố cục cực thấp không cắt nút: header/spacing gọn, target 44px, nhãn ngắn nhưng accessible name đầy đủ,
   giữ chấm trạng thái ghi hình; bản dịch/confidence/cảnh báo vẫn nằm trong camera, không scroll.
2. Chỉ phục hồi focus khi control cũ biến mất; không lấy focus khỏi control còn tồn tại hoặc dialog.
3. Positive accepted-overlay geometry được đưa vào browser suite bằng SSR fixture chỉ trong test.
   Acceptance/current-clip/stale clearing vẫn được component tests kiểm chứng; không tạo API/result giả trong App.

Các micro-commit đã sẵn sàng push; vẫn chưa có API upload/recognition integration, webcam/điện thoại thật
hoặc nghiệm thu của Tín/Huy. GitHub SHA/link/status được bổ sung vào member ledger sau push.
Push theo yêu cầu trực tiếp của owner trong phiên này; không tự ghi rằng Huy đã cấp integration window.
