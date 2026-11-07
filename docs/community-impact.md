# ViSign · Báo cáo tác động cộng đồng (T093)

**Trạng thái**: bản đầu 2026-11-08, phụ trách P1/Huy. Kết quả accessibility (T063) và usability (T071) chưa
có; các mục đó để `PENDING` và chỉ cập nhật bằng kết quả đo thật.

## 1. Nhóm hưởng lợi

| Nhóm | Lợi ích kỳ vọng | Điều kiện |
|---|---|---|
| Người Điếc/khiếm thính dùng VSL | Truyền đạt nhanh ý thiết yếu với người không biết VSL, không cần cài app | Ký hiệu thuộc 10 nghĩa P0; camera và ánh sáng đủ |
| Nhân viên tiếp nhận, y tế, hành chính | Hiểu ý chính, biết khi hệ thống không chắc chắn | Có người hỗ trợ khi kết quả bị từ chối |
| Người thân, cộng đồng | Công cụ học và giao tiếp ban đầu | Không thay thế học VSL hay phiên dịch viên |
| Cộng đồng nghiên cứu VSL | Pipeline, contract và quy ước dữ liệu mở trong repo | Dữ liệu người thật không công bố khi chưa có quyền |

## 2. Accessibility và usability

| Hạng mục | Hiện có | Trạng thái |
|---|---|---|
| Thông báo lỗi/hướng dẫn tiếng Việt ổn định, không hiển thị text thô từ server | T052, T074–T075 | Đã có |
| Kết quả và trạng thái đọc được bằng trình đọc màn hình (`role="alert"`, `aria-live`) | T042, T052, T103 | Đã có trong code |
| Giao diện không tràn trên khung 320 px, mobile, landscape | Browser test của P5 | Đã có |
| Audit accessibility (bàn phím, focus, nhãn camera) | T063 | `PENDING` |
| Usability với ≥ 10 người thuộc nhóm mục tiêu | T071 | `PENDING` |

## 3. Rủi ro gây hiểu nhầm và biện pháp

| Rủi ro | Biện pháp hiện có | Còn thiếu |
|---|---|---|
| Dịch sai trong tình huống quan trọng (y tế, giấy tờ) | Disclaimer FR-010; từ chối dưới ngưỡng; chỉ nhận một ký hiệu mỗi lần | Kiểm chứng với người dùng thật |
| Người dùng tin độ tin cậy như xác suất đúng | Model card ghi rõ confidence chưa hiệu chuẩn | Hiển thị diễn giải dễ hiểu (T088) |
| Biến thể vùng miền, người ký lạ, ánh sáng/góc máy | Class map giữ biến thể vùng; split theo video gốc; báo cáo không tuyên bố nhận diện người ký mới | Đo OOD/bias trên model thật (T089) |
| Bản dịch trực tiếp bị hiểu là dịch câu | Chỉ ghép các kết quả được chấp nhận, không suy ngữ pháp (FR-034) | Câu chữ giải thích trên UI cần review UX |
| Lịch sử trên máy dùng chung | Lưu cục bộ 24 giờ, tự xoá, có nút xoá và thông báo (FR-035–FR-036) | Hướng dẫn xoá trước khi bàn giao máy |
| Lộ video/dữ liệu cá nhân | Không lưu video, log allowlist, audit privacy và security | — |
| Pilot/fixture bị trình bày như model hoàn chỉnh | `demoReady=false` và cảnh báo phạm vi trên UI | — |

## 4. Roadmap mở rộng có điều kiện

| Bước | Điều kiện mở |
|---|---|
| 1. Model full 10 nghĩa `demoReady` | Manifest audit + đủ dữ liệu tự quay; Macro-F1 ≥ 0,80, recall ≥ 0,65; lead duyệt |
| 2. Đạt latency p95 ≤ 3 s và có URL production | Tối ưu trích landmark; hạ tầng được duyệt phạm vi/chi phí |
| 3. Mở rộng thêm ~20 nghĩa | Bước 1 ổn định; quy trình dữ liệu và quyền sử dụng lặp lại được |
| 4. Biến thể vùng miền và nhiều người ký | Có `signerId` để đánh giá người ký mới |
| 5. Ký hiệu liên tục, chuyển văn bản thành ký hiệu/giọng nói | Ngoài MVP (FR-017); cần đặc tả mới được duyệt |

Mỗi bước chỉ mở khi có evidence; không quảng bá năng lực chưa đo.
