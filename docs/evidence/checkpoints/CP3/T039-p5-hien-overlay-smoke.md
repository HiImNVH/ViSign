# CP3 T039 — Áp dụng bố cục camera overlay đã duyệt

## Nhận dạng

- Owner: P5 Hiển; reviewer: P2/Tín, P1/Huy — PENDING.
- Ngày: 2026-11-07 (Asia/Saigon).
- Yêu cầu đã được duyệt qua demo: một màn hình không cuộn; bỏ “Một ký hiệu, một lần quay.”;
  camera chiếm phần lớn màn hình, nút và bản dịch ở trong camera; nền mờ nhẹ,
  chỉ hiện chữ khi có nhận dạng được chấp nhận.
- Pre-commit sync: fetch/rebase `origin/main` tại `38cc95519510954b3c45a61315620a20804a7a94`;
  local camera base `d1f9ea776189c648220ca8cbf2bc4082c7d4ec6f`. Conflict member log được giải quyết
  bằng cách giữ dòng T040 của lead và các dòng camera local; không sửa phần backend/AI.
- Full frontend gate đã chạy sau rebase 377ac98; các lần đồng bộ c902ea3/38cc955 sau đó chỉ thêm workflow CI/docs,
  không thay source/dependency frontend. Candidate frontend được khôi phục nguyên vẹn và diff-check sau sync.
- Commit/link GitHub: PENDING trước push; chưa có integration window, NOT_PUSHED.
- Môi trường: Windows 11, Node 26.7.0, npm 11.19.0, Playwright 1.64.1, Edge Chromium 157.0.4341.42.

## Phạm vi và kết quả

- App dùng `100dvh` và grid header + camera, không giấu nội dung bằng overflow của trang.
- Video luôn là cùng node/ref; giữ `object-fit: contain` và mirroring chỉ trên video.
- Nút trong camera ở cạnh dưới; status ở góc trên phải. Bỏ khung hướng dẫn trang trí không khớp ảnh.
- Nền controls: trắng alpha 0.72, nền chữ: trắng alpha 0.76; blur 6px, opacity chữ/nút bằng 1.
- Không có vùng chữ trống hoặc placeholder. `RecognitionOverlay` chỉ render khi accepted đúng true,
  chữ/class label không rỗng, confidence hữu hạn trong [0,1] và CameraRecorder xác nhận đúng clip.
- Quay lại, cancel/reset hoặc kết quả thuộc clip khác không hiển thị bản dịch cũ.
- Ứng dụng chưa có API client/result integration; App không truyền `recognitionResult`, không tạo chữ giả.
  T042 chỉ có ranh giới trình bày để nối sau; không đóng T040–T043/CP3.
- CameraSession/useCameraCapture, capture limits, dependency và lockfile không thay đổi.
- Giữ focus của native Help khi camera mất kết nối; Escape vẫn trở về nút Hướng dẫn.
- Privacy/disclaimer đầy đủ vẫn có trong Hướng dẫn. Overlay accepted có confidence/cảnh báo thử nghiệm.

## Gate tái lập

Từ `apps/web/`:

```powershell
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm.cmd run check
```

| Gate | Kết quả | Trạng thái |
|---|---|---|
| ESLint + TypeScript | Không lỗi; exit 0 | PASS |
| Vitest | 42 tests / 4 files; exit 0 | PASS |
| Vite build | 22 modules; exit 0 | PASS |
| Browser | 15 tests, desktop 1440×900, mobile 320×640, landscape 640×360; exit 0 | PASS |
| Git diff | `git diff --check`; exit 0 | PASS |

- Test overlay được viết trước; lần đầu fail vì module chưa tồn tại, sau implementation đạt.
- Test thiếu/rejected/blank text/class label/confidence sai đều không tạo panel.
- Test accepted có chữ/confidence/cảnh báo; đổi clip hoặc recapture ẩn chữ và giữ cùng video node.
- Browser xác nhận camera rộng >90% và cao >70% viewport, controls nằm trong camera,
  không cuộn ngang/dọc ở idle/preview/captured/error/reset. Local capture luôn không có vùng dịch.
- Fake Y4M/getUserMedia/MediaRecorder thật, cancel/release, denial, dialog/focus/reduced-motion
  và zero-upload checks vẫn đạt; không dùng webcam cá nhân.
- Kiểm tra bố cục positive riêng: render component overlay bằng React SSR với fixture accepted chỉ trong
  quá trình kiểm thử, chèn vào DOM test trên camera synthetic. Cả ba viewport đều thấy panel trong camera,
  nằm trên controls, opacity chữ bằng 1, background rgba(255,255,255,0.76), không scroll.
  Kiểm tra này không được tính là API/recognition E2E.
- Đã xem ảnh desktop/mobile/landscape từ browser tests: camera lớn, không có placeholder bản dịch.
- NOT_RUN: backend/model integration, webcam/điện thoại thật, CI/cloud; giữ các giới hạn browser ở evidence T039 chính.

## Spec Kit và thiết kế

- Prerequisites chạy với `SPECIFY_FEATURE_DIRECTORY=specs/001-vsl-recognition-mvp`; checklist requirements
  vẫn 18/18, không sửa checkbox. Không có `.specify/extensions.yml` để dispatch hooks.
- UI/UX Pro Max: focus không bị che, nền mờ vẫn giữ chữ rõ, không dùng opacity cho cả parent.
- Frontend Design: làm theo demo người dùng đã duyệt, không thêm hero/sidebar.
- Emil/mobile-native: dynamic viewport, safe area, hover theo capability, reduced motion;
  không thêm animation/thư viện mới.

| Before | After | Why |
|---|---|---|
| Hero và nội dung dưới camera làm trang dài | Header gọn + camera dùng phần chiều cao còn lại | Một màn hình không cuộn |
| Bản dịch rỗng luôn hiện | Chỉ render result accepted hợp lệ, đúng clip | Không trình bày trạng thái capture thành nhận dạng |
| Panel nền đặc | Background alpha + blur nhẹ, chữ/nút giữ opacity 1 | Nhìn được camera phía dưới mà vẫn đọc rõ |

Ảnh/fixture/report local được ignore; source/tests và evidence này là bằng chứng tái lập.
Rollback bằng revert riêng commit overlay; không reset/force-push main.

**Status**: PASS local / NOT_PUSHED. **Reviewer**: PENDING.
