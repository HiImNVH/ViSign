# ViSign web

Frontend React/TypeScript/Vite, phiên bản `0.0.1`. Bản local hiện có phần camera T039:
xem trước, quay/dừng/hủy một ký hiệu và tắt camera. Chưa tích hợp API nhận diện.

## Chạy local

Yêu cầu Node.js 22.22.2+ (nhánh 22), 24.15.0+ (nhánh 24) hoặc 26+ và npm, đúng `package.json#engines`. Từ thư mục repository:

```powershell
npm.cmd ci --prefix apps/web
npm.cmd --prefix apps/web run dev
```

Mở URL Vite in ra. Dev server chỉ lắng nghe trên loopback.

## Kiểm tra

Tại `apps/web/`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:browser
```

`npm.cmd run check` chạy lint, toàn bộ unit/component tests, typecheck/build và browser tests.
`test:browser` và `test:smoke` yêu cầu chạy build trước. Playwright khởi động
preview server riêng tại `127.0.0.1:4173`, kiểm tra desktop, viewport 320px và landscape 640×360;
không tái sử dụng server có sẵn. Cổng bận sẽ làm kiểm tra thất bại rõ ràng.
Vitest chỉ thu thập `*.test.ts`/`*.test.tsx`, tách khỏi Playwright `*.spec.ts`.

Trên Windows có Edge, chạy camera E2E bằng Chromium của Edge:

```powershell
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm.cmd run check
```

Camera tests dùng `getUserMedia`/`MediaRecorder` thật với fixture Y4M tổng hợp do
`tests/browser/cameraFixture.ts` tạo trong `.local/` (được ignore). Không dùng webcam
thật hoặc video cá nhân. Kiểm tra quyền bị từ chối bằng CDP của Chromium.
Gate cuối dùng Playwright 1.64.1 của toolchain CP1 và Edge 157, đã chạy đạt.
Lần kiểm tra ban đầu với Playwright 1.65.0 / Headless Shell 158 trả `NotSupportedError`
với fake media. Chưa xác nhận camera E2E trên bundled Chromium của 1.64.1;
bỏ biến channel để thử browser Playwright mặc định khi môi trường hỗ trợ.

## Luồng camera

- Bật camera chỉ xin quyền và mở preview, không quay hoặc tải dữ liệu lên.
- Quay ký hiệu → Kết thúc tạo một Blob WebM trong bộ nhớ. Có thể hủy/quay lại.
- Tự dừng sau 5 giây; bỏ đoạn dưới 300 ms, vượt 6 giây hoặc 10 MiB.
- Các giới hạn phía client là kiểm tra sơ bộ; decoder backend vẫn phải đo duration
  và xác thực nội dung khi tích hợp. Timer trình duyệt không chứng minh duration giải mã.
- Không ghi âm, lưu file/localStorage hoặc tạo object URL. Hủy bỏ Blob;
  Tắt camera/pagehide/unmount dừng tracks và xóa preview, timers, listeners.
- Có hướng dẫn native dialog hỗ trợ Escape/focus, lỗi quyền/thiết bị và thử lại.

## Phạm vi và thiết kế

- Bố cục đã được người dùng duyệt: một màn hình không cuộn, camera chiếm phần lớn viewport,
  bỏ tiêu đề lớn. Nút điều khiển nằm trong khung camera, sát cạnh dưới, trên nền trong mờ.
- Vùng chữ chỉ xuất hiện khi có kết quả `accepted=true`, chữ/class label không rỗng,
  confidence hợp lệ và đúng Blob của lần quay hiện tại. Không hiển thị ô rỗng,
  “Chưa có bản dịch” hoặc chữ mẫu trong ứng dụng.
- `CameraRecorder.recognitionResult` là ranh giới trình bày cho lần tích hợp sau;
  ứng dụng hiện chưa truyền kết quả vì chưa nối API. Ghi xong clip không tự trở thành bản dịch.
- Vùng chữ nằm trên hàng nút trong camera; nền có alpha và blur nhẹ, không giảm opacity của chữ/nút.
- Riêng tư và disclaimer đầy đủ nằm trong Hướng dẫn; kết quả được chấp nhận có confidence/cảnh báo thử nghiệm.
- T004: package, lockfile, entrypoint React và trang khởi đầu.
- T006: ESLint, strict TypeScript, Vitest và Playwright.
- T039: camera và capture local; T031/T028 chỉ triển khai phần test/copy phục vụ camera.
- API client/types, kết quả tích hợp và Admin thuộc các phần sau; T042 mới chuẩn bị phần overlay, chưa hoàn tất.
- Nền sáng `#f4f5f6`, chữ chính `#173f35`, chữ phụ `#52666b`;
  font hệ thống hỗ trợ tiếng Việt; nội dung căn trái, chiều dài dòng tối đa 65ch.
- Giữ zoom trình duyệt, safe area và viewport nhỏ; hover chỉ cho thiết bị hỗ trợ,
  phản hồi nhấn nhẹ và tắt chuyển động khi bật reduced motion.
- Browser smoke dùng Chromium với viewport mô phỏng; chưa kiểm tra điện thoại thật.

Không đánh dấu hoàn thành checkpoint trước khi có push theo integration window
và review độc lập. Xem `members/p5-hien/README.md` và smoke evidence của CP1.
