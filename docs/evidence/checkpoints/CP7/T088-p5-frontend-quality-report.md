# T088 — Frontend UI/UX quality audit (P5 Hiển)

**Ngày:** 2026-11-08 (Asia/Ho_Chi_Minh)
**Checkpoint:** CP7 / US5 / T088
**Phạm vi:** `apps/web/` (giao diện camera, kết quả, lịch sử, trạng thái và API client); API v1 và video giả lập.
**Kết luận ở phạm vi frontend:** `TEST_PASS / READY_FOR_REVIEW`; P1 Huy/P2 Tín chưa review độc lập các thay đổi P5. P1 đã có audit song song, xem báo cáo tổng hợp.

## Phương pháp và môi trường

Kiểm thử bản build Vite (`npm run build` rồi Playwright chạy `vite preview` ở
`http://127.0.0.1:4173`), trên Windows, Chromium qua Microsoft Edge `msedge`.
Playwright dùng video giả lập qua `MediaRecorder`, intercept `GET /api/v1/model-info`
và `POST /api/v1/predictions`; không gửi clip tới backend thật.

Tập trung vào trạng thái đã nhận diện thành công (danh sách 10 nghĩa), từ chối quyền
camera, lịch sử có dữ liệu, request đang xử lý, lỗi API `SERVICE_BUSY`, điều hướng
phím và vị trí các thành phần khi khung nhìn đổi kích thước. Test được lưu tại
[`apps/web/tests/browser/frontend-quality.spec.ts`](../apps/web/tests/browser/frontend-quality.spec.ts).

| Hạng mục | Kết quả có thể tái lập | Đánh giá |
|---|---|---|
| Responsive | Test trên desktop `1440×900`, mobile `320×640`, landscape `640×360`; với accepted flow còn đổi động sang `768×1024` và `320×180`. Không tràn ngang/dọc, nút thao tác trong camera, panel kết quả không đè nhóm nút. | PASS trong 5 kích thước đã kiểm thử |
| Camera usability | Quy trình `Bật camera → Quay ký hiệu → Kết thúc → Gửi nhận diện` có ý định rõ ràng; xác nhận chưa upload trước khi bấm gửi và chỉ upload một lần. Trạng thái camera không bị transcript che trên mobile. | PASS với video giả và response mock |
| Chạm/điều khiển | Các nút trong nhóm điều khiển camera đang hiển thị đạt chiều cao tối thiểu `44px` trên các viewport đã thử. | PASS |
| Accessibility | Axe WCAG 2 A/AA + 2.1 A/AA không báo vi phạm trên màn hình bị từ chối quyền, lịch sử mở, đang gửi và lỗi API phục hồi; kiểm tra focus `Thử lại`, `Escape` đóng dialog và trả focus về `Lịch sử`. | PASS trong các trạng thái đã kiểm thử; không tương đương chứng nhận WCAG |
| Visual consistency | Camera là khối nội dung chủ đạo, trạng thái/nút/feedback cùng kiểu chữ và nút hiện hữu; các panel transcript, kết quả và lỗi được đặt trong vùng camera. | Đã rà soát mã/CSS và ảnh chụp ba viewport |
| Module boundaries | `App.tsx` phối hợp màn hình; `useRecognition.ts` quản lý trạng thái/side effects; `CameraRecorder.tsx` hiển thị video/controls; `RecognitionResult.tsx`, `TranscriptPanel.tsx`, `HistoryPanel.tsx` đảm nhiệm phần hiển thị; `services/inferenceApi.ts` giữ HTTP contract. | Ranh giới trách nhiệm hợp lý; chưa phát hiện logic HTTP trong UI component |

## Lỗi phát hiện và sửa trong T088

| ID | Bằng chứng tái lập ban đầu | Sửa | Kiểm tra lại |
|---|---|---|---|
| FE-088-01 | Ở trạng thái đang gửi, nút hiển thị `Đang nhận diện…` nhưng `aria-label` vẫn là `Gửi nhận diện`; axe báo lỗi nhãn truy cập không chứa chữ hiển thị. | `CameraRecorder.tsx`: gắn nhãn động theo `pending` và `vi.recognition.sending`. | Playwright/axe ở trạng thái pending trên cả ba viewport. |
| FE-088-02 | Mobile `320×640`: transcript ở trên cùng che huy hiệu trạng thái camera. | `styles.css`: dưới `480px`, đặt `.transcript-panel` `top: 48px`. | Kiểm tra bounding box để hai vùng không giao nhau và chụp màn hình accepted mobile. |

## Screenshot evidence

Ảnh JPEG lưu trong repo, được chụp tự động từ các case đã xác nhận thành công;
không có webcam thật, khuôn mặt hay video người dùng.

| Trạng thái | Desktop 1440×900 | Mobile 320×640 | Landscape 640×360 |
|---|---|---|---|
| Accepted + transcript 10 nghĩa | [ảnh](evidence/checkpoints/CP7/T088-screenshots/accepted-desktop.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/accepted-mobile.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/accepted-landscape.jpg) |
| Camera permission denied | [ảnh](evidence/checkpoints/CP7/T088-screenshots/permission-desktop.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/permission-mobile.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/permission-landscape.jpg) |
| Lịch sử được mở | [ảnh](evidence/checkpoints/CP7/T088-screenshots/history-desktop.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/history-mobile.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/history-landscape.jpg) |
| API báo busy | [ảnh](evidence/checkpoints/CP7/T088-screenshots/api-error-desktop.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/api-error-mobile.jpg) | [ảnh](evidence/checkpoints/CP7/T088-screenshots/api-error-landscape.jpg) |

## Kiểm tra tái lập

```powershell
cd apps/web
$env:VISIGN_BROWSER_CHANNEL='msedge'
$env:VISIGN_CAPTURE_T088='1' # Tùy chọn: ghi đè 12 ảnh snapshot
npm.cmd run check
```

Case riêng của T088: **9/9 PASS** (`3 cases × 3 projects`, exit 0), sau khi
build lại bản preview; gồm accepted flow, permission/history/axe và pending/error/axe.
Full web gate sau khi đồng bộ `origin/main`: lint, typecheck, build PASS;
**165 unit PASS / 4 SKIP**, **84 Edge browser PASS / 12 SKIP**, exit 0.
Các screenshot test của P1 chỉ chạy khi bật cờ chụp ảnh, và live API test
được skip trong gate không bật backend. Kết quả chi tiết trong
[`T088-p5-hien-smoke.md`](evidence/checkpoints/CP7/T088-p5-hien-smoke.md).

## Giới hạn và đề xuất review

- Ở landscape/điện thoại nhỏ, panel kết quả dài che phần lớn live video; các nút
  vẫn hiện đủ. Cần thử trên máy thật với nội dung sản phẩm trước khi điều chỉnh bố cục.
- Test mô phỏng không đo thành công không trợ giúp của người dùng (SC-001), độ trễ
  mô hình thực tế (SC-002), quyền camera/zoom 200% trên phần cứng, TalkBack/NVDA,
  latency của thiết bị chậm hoặc model suy luận thật. Axe tự động không thay thế
  kiểm tra thủ công bằng screen reader.
- `quality.yml` hiện chưa chạy bộ Playwright T088; đề nghị P1 xem xét đưa browser
  smoke vào T091 và P1/P2 tái lập gate Edge trên commit đã push.
- Lịch sử và transcript là phần UI liên quan riêng US6; audit này chỉ xác nhận
  trình bày/trạng thái, không thay thế kiểm thử lưu trữ TTL và quyền riêng tư.

**Handoff:** P1 Huy đánh giá tính dễ dùng, visual consistency và thiết bị thật;
P2 Tín xác nhận flow API thật; cả hai review bằng chứng CP7 trước khi đổi trạng thái
T088 từ `[ ]` sang `[X]` hoặc `VERIFIED`.
