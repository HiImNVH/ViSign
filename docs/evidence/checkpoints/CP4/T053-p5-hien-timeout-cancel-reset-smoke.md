# CP4 T053 — Timeout, cancel request và reset trạng thái (P5 Hiển)

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T053` (`US2`) |
| Owner | P5 Hiển |
| Reviewer | P2 Tín, P1 Huy — chưa review độc lập |
| Commit | `CP4 T053(web): harden timeout cancel and state reset`; tra SHA bằng `git log --grep='CP4 T053'` |
| Ngày | 2026-11-07 |
| Môi trường | Windows / PowerShell, Node `26.7.0`, npm `11.19.0`, Vitest `5.0.5`, Playwright `1.64.1`, Microsoft Edge (`VISIGN_BROWSER_CHANNEL=msedge`) |
| Tình trạng | `TEST_PASS / READY_FOR_REVIEW`; chưa tự nhận VERIFIED |

## 2. Phạm vi và điều kiện nghiệm thu

- `useRecognition.ts`: chỉ request đang hoạt động và clip đang giữ trong session camera mới có quyền ghi kết quả **hoặc lỗi**; cancel/reset/recapture/pagehide/unmount hủy request và vô hiệu hóa kết quả đến muộn.
- `inferenceApi.ts`: dùng một deadline tại transport (5s metadata, 15s prediction), lưu nguyên nhân hủy đầu tiên; kiểm tra abort sau khi đọc body để response đến muộn không thành công giả; dọn timer và listener.
- Retry timeout là thao tác `Gửi nhận diện` chủ động; không auto-upload/auto-retry. Hủy đoạn quay đưa camera về preview; tắt camera đưa về idle, giải phóng track.
- Unit tests kiểm tra deadline 15s, hủy trước deadline, body resolve sau cancel, timer cleanup, A cũ không ghi đè/giải phóng guard B, session đổi trước React rerender, metadata refresh cũ, retry timeout.
- Browser fake-camera chứng minh timeout → thông báo tiếng Việt → nút gửi lại, cancel/reset khi upload pending → không hiện kết quả cũ, track ended; chạy trên desktop/mobile/landscape.

## 3. Smoke

Chạy từ `apps/web` trong PowerShell:

```powershell
$env:VISIGN_BROWSER_CHANNEL='msedge'
npm.cmd run check
```

| Gate | Kết quả | Trạng thái |
|---|---|---|
| Unit tập trung | `npm.cmd test -- tests/inferenceApi.test.ts tests/recognition/useRecognition.test.tsx`: **23/23**, exit `0` | `PASS` |
| Browser T053 desktop | `npm.cmd run test:browser -- tests/browser/camera.spec.ts --project=desktop -g T053`: **2/2**, exit `0` | `PASS` |
| ESLint + TypeScript | `npm.cmd run check`: lint và typecheck thành công | `PASS` |
| Toàn bộ Vitest | `npm.cmd run check`: **129/129**, 9 files | `PASS` |
| Production build | `npm.cmd run check`: Vite 25 modules transformed | `PASS` |
| Browser Edge toàn bộ | `npm.cmd run check`: **48/48** desktop/mobile/landscape | `PASS` |
| Backend/model và webcam thật | Chưa chạy; phụ thuộc giai đoạn tích hợp thật | `NOT_RUN` |

Các log proxy `ECONNREFUSED 127.0.0.1:8000` trong kịch bản không mock metadata là fallback dự kiến, không làm test fail. Không đưa clip WebM thật, token, backend traceback hay model weights vào Git.

## 4. Artifact / handoff

| Loại | Tham chiếu |
|---|---|
| Source | `apps/web/src/features/recognition/useRecognition.ts`, `apps/web/src/services/inferenceApi.ts` |
| Unit | `apps/web/tests/inferenceApi.test.ts`, `apps/web/tests/recognition/useRecognition.test.tsx` |
| Browser | `apps/web/tests/browser/camera.spec.ts` |
| Member log | `members/p5-hien/README.md` |
| CI | `NOT_VERIFIED`; kiểm tra riêng sau khi xuất hiện run trên remote |
| Reviewer | `PENDING` — chưa đánh dấu task `[X]` |

Nếu phải rollback: `git revert <sha-commit-T053>`. Huy/Tín kiểm thử độc lập trên backend/API thật khi integration window cho phép.
