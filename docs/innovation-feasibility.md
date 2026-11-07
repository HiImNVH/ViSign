# ViSign · Hồ sơ sáng tạo và tính khả thi (T087)

**Trạng thái**: bản đầu 2026-11-08, phụ trách P1/Huy. Không có kiểm thử người dùng (T071 đã bỏ); mọi số liệu dưới
đây lấy từ evidence trong repo, không suy diễn.

## 1. Bài toán và đối tượng sử dụng

| Nhóm | Bối cảnh | Nhu cầu |
|---|---|---|
| Người Điếc/khiếm thính dùng Ngôn ngữ Ký hiệu Việt Nam (VSL) | Quầy hành chính, phòng khám, giao tiếp thường ngày | Truyền đạt nhanh một ý thiết yếu khi người đối diện không biết VSL |
| Người nghe (nhân viên tiếp nhận, y tế, người thân) | Tiếp xúc ngắn, không có phiên dịch viên | Hiểu ý chính bằng tiếng Việt, biết khi nào hệ thống **không chắc chắn** |

**Pain point**: phiên dịch viên VSL ít và không luôn có mặt; viết tay/nhắn tin chậm và không phải ai cũng
thuận tiện; các ứng dụng hiện có thường cần cài đặt, gửi video lên server hoặc không cho biết khi kết quả
không đáng tin.

## 2. Giải pháp

Web chạy trên trình duyệt có camera: người dùng quay **một ký hiệu**, hệ thống trả nghĩa tiếng Việt kèm độ
tin cậy, hoặc trả **“Không nhận diện được”** khi dưới ngưỡng. Các kết quả được chấp nhận ghép thành dòng bản
dịch trực tiếp và lưu trên chính trình duyệt trong 24 giờ.

Phạm vi MVP: 10 nghĩa P0 thuộc ba nhóm giao tiếp, y tế, hành chính — Giấy tờ, Đau bụng, Sốt, Nhận, Bạn,
Cảm ơn, Giúp đỡ, Xin lỗi, Đau đầu, Không.

## 3. Điểm khác biệt

| # | Điểm khác biệt | Bằng chứng trong repo |
|---|---|---|
| 1 | **Từ chối có kiểm soát**: dưới ngưỡng thì nói rõ “Không nhận diện được” thay vì đoán; ngưỡng chọn chỉ trên tập validation và lưu trong artifact | T044/T048, T036, `docs/model-card.md` |
| 2 | **Không lưu video**: clip chỉ là file tạm, bị xoá trên mọi đường kể cả lỗi; log chỉ có field allowlist; lịch sử chỉ trên trình duyệt | T024–T025, T066, T092, FR-035 |
| 3 | **Train và phục vụ dùng cùng một pipeline** landmark → tensor 32×234; parity offline ↔ API được test (32/32 clip thật khớp tuyệt đối) | T014–T017, T037, T064 |
| 4 | **Nhẹ và chạy CPU**: GRU trên landmark, suy luận GRU < 5 ms; không cần GPU để demo | `docs/performance-report.md` (T065) |
| 5 | **Phát hành có cổng chất lượng**: chỉ model full đủ 10 nghĩa, Macro-F1 ≥ 0,80, recall từng nghĩa ≥ 0,65 trên split theo video gốc **và** lead duyệt mới được `demoReady` | T054, T057–T059 |
| 6 | **Không cần cài đặt**: web chuẩn, lỗi và hướng dẫn bằng tiếng Việt ổn định | T039–T043, T052, T074–T075 |

## 4. So sánh với giải pháp/tài nguyên công khai

Khảo sát GitHub/Hugging Face/Zenodo ngày 2026-11-07 (định tính, không so sánh độ chính xác vì khác bộ từ và
dữ liệu):

| Tiêu chí | ViSign | Model video RGB công khai (Multi-VSL I3D/MViT, VideoMAE PTIT) | Ứng dụng demo cá nhân trên GitHub |
|---|---|---|---|
| Đầu vào | Landmark từ camera trình duyệt | Clip RGB, model nặng hơn | Thường MediaPipe + LSTM |
| Từ chối khi không chắc | Có, ngưỡng từ validation | Không công bố | Hiếm khi có |
| Quyền riêng tư | Không lưu video, log allowlist | Không áp dụng (model nghiên cứu) | Thường không đề cập |
| Phủ 10 nghĩa P0 | Theo thiết kế | Không có bảng nhãn công khai (Multi-VSL) hoặc chỉ 3/10 (PTIT) | Tuỳ dự án |
| License dùng lại | Mã nguồn của nhóm | Một số không có license | Thường không có license |

Kết luận khảo sát: chưa có nguồn công khai nào phủ đủ 10 nghĩa P0 với license rõ ràng, nên nhóm tự xây dữ liệu
và model; đây vừa là rủi ro (dữ liệu ít) vừa là đóng góp.

## 5. Tính khả thi

| Khía cạnh | Hiện trạng | Đánh giá |
|---|---|---|
| Kỹ thuật | Luồng camera → API → kết quả chạy end-to-end với fixture; train/eval/gate/serving GRU đã có test | Khả thi |
| Dữ liệu | 27 clip cho 10 nghĩa, chưa có manifest audit; nhóm có kế hoạch tự quay | **Rủi ro chính** |
| Hiệu năng | Web p95 5,87 s, mục tiêu ≤ 3 s; nút thắt là trích landmark | Cần tối ưu |
| Chi phí | Chạy CPU; kế hoạch một EC2 + CloudFront trên AWS Free Plan (`docs/cost-report.md`) | Khả thi nếu giữ phạm vi nhỏ |
| Triển khai | OIDC bị chặn trên Free Plan; chưa có URL production | Cần quyết định của lead |

## 6. Phạm vi áp dụng

- Phù hợp: tương tác ngắn, một ý thiết yếu, nơi có người nghe hỗ trợ (quầy tiếp nhận, phòng khám ban đầu).
- Không phù hợp: hội thoại dài, nội dung pháp lý/y khoa quan trọng cần chính xác tuyệt đối — khi đó cần
  phiên dịch viên chuyên nghiệp (disclaimer FR-010).

## 7. Bằng chứng người dùng

**Không có.** Lead bỏ T071 (2026-11-08) vì đây là bản trình chiếu chấm điểm, chưa có người dùng thật. Bằng chứng
trải nghiệm hiện có: audit accessibility T063, audit FE/UX T088 và nhóm tự kiểm webcam thật qua HTTPS trên AWS.
Khi trình bày không nêu số liệu usability; nếu được hỏi, nói rõ đây là bước tiếp theo sau MVP.
