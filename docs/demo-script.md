# ViSign · Kịch bản demo (T068)

**Trạng thái**: bản đầu 2026-11-08, phụ trách P1/Huy. Thời lượng mục tiêu 7 phút + Q&A. Mọi con số lấy từ evidence
trong repo; trước buổi demo phải cập nhật lại theo artifact thật (xem mục 6).

## 0. Chuẩn bị (trước giờ trình bày)

- Chạy `/api/v1/health` và `/api/v1/model-info`; ghi lại `artifactKind`, `modelVersion`, `demoReady` lên slide.
- Laptop demo: Chrome/Edge, webcam, ánh sáng phía trước; xoá lịch sử bản dịch trên máy dùng chung.
- Phương án dự phòng: bản local (README "Chạy local") + artifact đã smoke-test; video quay màn hình luồng chuẩn.

## 1. Bài toán (45 giây) — người trình bày: Huy

- Người Điếc/khiếm thính dùng VSL gặp khó khi giao tiếp ngắn ở quầy hành chính, phòng khám; phiên dịch viên
  không luôn có mặt.
- ViSign: quay **một ký hiệu** bằng camera trình duyệt → nghĩa tiếng Việt, hoặc nói rõ **“Không nhận diện được”**.

## 2. Demo trực tiếp (3 phút) — người trình bày: Hiển

| Bước | Thao tác | Điểm cần nói |
|---|---|---|
| 1 | Bật camera | Chỉ xin quyền và mở preview; chưa quay, chưa gửi gì |
| 2 | Quay ký hiệu → Kết thúc → **Gửi nhận diện** | Chỉ gửi khi người dùng chủ động bấm |
| 3 | Kết quả + độ tin cậy | Hiển thị phạm vi model (fixture/pilot/full) và cảnh báo nếu `demoReady=false` |
| 4 | Ký thêm một nghĩa | Dòng **bản dịch trực tiếp** ghép các kết quả được chấp nhận |
| 5 | Ký động tác ngoài phạm vi | Hệ thống trả “Không nhận diện được” thay vì đoán |
| 6 | Tải lại trang | Lịch sử còn trên **chính trình duyệt** trong 24 giờ; nút xoá |

## 3. Điểm khác biệt (1 phút) — Huy

Từ chối có kiểm soát · không lưu video · train và API dùng cùng pipeline (parity 32/32 clip thật) · chạy CPU ·
cổng phát hành Macro-F1 ≥ 0,80, recall từng nghĩa ≥ 0,65 + lead duyệt. Chi tiết: `docs/innovation-feasibility.md`.

## 4. Dữ liệu và mô hình (1 phút) — Cường, Quang

- 10 nghĩa P0 thuộc giao tiếp/y tế/hành chính; video giáo dục công khai + dữ liệu nhóm tự quay; nguồn khai ở
  dataset card.
- MediaPipe → tensor 32×234 → GRU một tầng; split theo video gốc, **không** tuyên bố nhận diện người ký mới.
- **Công khai trạng thái artifact**: nếu chạy fixture/pilot thì nói rõ đây là bản tích hợp, `demoReady=false`.

## 5. Kỹ thuật, cloud, chi phí (1 phút) — Tín

- REST `/api/v1` đóng băng, lỗi tiếng Việt ổn định, `X-Request-ID`, 404/405/307 theo contract.
- Bảo mật: không lưu video, log allowlist, header bảo mật, quét secret/dependency (`docs/security-report.md`).
- CI kiểm mọi push; kế hoạch AWS (EC2 + CloudFront + ECR + S3) và chi phí (`docs/cost-report.md`).

## 6. Giới hạn — nói thẳng (30 giây) — Huy

| Giới hạn | Số liệu hiện tại (cập nhật trước demo) |
|---|---|
| Latency | Web p95 5,87 s, mục tiêu ≤ 3 s (`docs/performance-report.md`) |
| Model | Chưa có model VSL thật đạt gate (`docs/model-card.md`) |
| Production | Chưa có URL công khai; OIDC bị chặn trên AWS Free Plan |
| Phạm vi | Một ký hiệu mỗi lần, 10 nghĩa; không thay phiên dịch viên |

## 7. Q&A chuẩn bị

| Câu hỏi có thể gặp | Trả lời ngắn | Evidence |
|---|---|---|
| Độ chính xác bao nhiêu? | Chỉ công bố số trên tập test tách theo video gốc khi artifact qua gate; hiện chưa có | `docs/model-card.md` |
| Sao không dùng model công khai? | Không nguồn nào phủ đủ 10 nghĩa với license rõ (đã khảo sát) | `docs/innovation-feasibility.md` |
| Có lưu video người dùng? | Không; file tạm bị xoá trên mọi đường, đã audit | T066, `docs/security-report.md` |
| Model sai trong tình huống y tế? | Từ chối khi không chắc, disclaimer, không thay phiên dịch viên | FR-010, `docs/community-impact.md` |
| Vì sao GRU? | Gọn, chạy CPU, giữ thứ tự động tác; GRU < 5 ms/clip | `docs/model-card.md`, T065 |
| Chi phí vận hành? | Một host CPU; chi tiết theo số đo | `docs/cost-report.md` |
| Mở rộng thế nào? | Theo roadmap có điều kiện; thêm nghĩa qua class map + train lại | `docs/community-impact.md` |
| Nhóm phân công ra sao? | Theo checkpoint, mỗi task có owner và reviewer khác owner | `members/`, `docs/team/` |

## 8. Phân vai

| Người | Phần |
|---|---|
| Huy | Mở đầu, điểm khác biệt, giới hạn, điều phối Q&A |
| Hiển | Demo giao diện |
| Cường | Mô hình, đánh giá |
| Quang | Dữ liệu, quyền sử dụng |
| Tín | Backend, bảo mật, cloud, chi phí |
