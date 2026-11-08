# ViSign · Bộ câu hỏi phản biện và chiến thuật trả lời (T097)

**Dùng cho**: 5 thành viên khi trình bày trước BGK · **Cập nhật**: 2026-11-08 · **Phụ trách**: P1/Huy

Mọi con số dưới đây đều có trong repo; cột "Bằng chứng" chỉ file để mở ngay khi bị hỏi vặn. Không nêu số nào không có
ở đây. Cái gì chưa đo thì nói "chưa đo" và nói cách sẽ đo.

---

## 0. Chiến thuật chung

### 0.1. Công thức trả lời mỗi câu (≤ 45 giây)

1. **Kết luận một câu**: trả lời thẳng, có số.
2. **Bằng chứng**: tên file/số đo/test; mở được nếu BGK muốn xem.
3. **Giới hạn**: tự nói trước điểm yếu, kèm nguyên nhân.
4. **Bước tiếp theo**: một hướng cụ thể, có ước lượng.
5. **Cầu nối**: một câu dẫn sang điểm mạnh kế tiếp trong flow (mục 0.3).

> Ví dụ cầu nối: "…và chính vì giới hạn đó nên nhóm làm cổng chất lượng; em xin chỉ nhanh cổng này hoạt động thế nào."

### 0.2. Quy tắc

- **Không tranh luận, không phòng thủ.** Đồng ý phần đúng, rồi đưa số.
- **Phân biệt rõ ba loại câu**: "đã đo", "ước lượng", "chưa làm". BGK audit sẽ bắt lỗi khi trộn ba loại này.
- **Người trả lời theo phần**: AI/model → Cường; dữ liệu → Quang; backend/bảo mật/cloud → Tín; giao diện/a11y → Hiển;
  tổng thể, quy trình, capacity, chi phí → Huy. Người khác bổ sung tối đa một câu.
- **Không nói "AI viết hết"**, cũng không giấu việc dùng trợ lý AI: nhóm dùng trợ lý để viết/review, mọi thay đổi đi qua
  test, CI và review chéo có ghi lại trong evidence.

### 0.3. Flow muốn dẫn BGK đi qua (gài "mồi" trong slide)

| Bước | Thông điệp | Mồi để BGK hỏi đúng chỗ mạnh |
|---|---|---|
| 1 | Bài toán thật: người Điếc cần truyền một ý thiết yếu khi không có phiên dịch | Slide có câu "hệ thống biết nói *không chắc*" → mời hỏi về từ chối |
| 2 | Demo dịch trực tiếp: bật camera, ký, chữ hiện ra | Để chip **Người/Mặt/Tay** và 11 trạng thái hiện rõ → mời hỏi cách phát hiện |
| 3 | Kiến trúc: trình duyệt lọc người/tay, server nhận diện, không lưu video | Sơ đồ có ô "1 slot suy luận" → mời hỏi capacity (đã chuẩn bị số) |
| 4 | Chất lượng: cổng Macro-F1/recall, split theo video gốc | Ghi thẳng "pilot Macro-F1 0,33 – chưa demoReady" → BGK hỏi, ta trả lời bằng cổng |
| 5 | Vận hành: CI 5 job, Docker, AWS, chi phí | Hiện bảng kiểm tải → mời hỏi scale |
| 6 | Lộ trình: gửi landmark thay video, thêm dữ liệu, mở rộng từ vựng | Kết bằng con số cụ thể của bước tiếp theo |

**Backup slides** (để sẵn, chỉ mở khi bị hỏi): bảng kiểm tải, sơ đồ luồng dữ liệu riêng tư, bảng cổng chất lượng,
confusion matrix pilot, bảng chi phí AWS, ảnh CI xanh, bảng so sánh với Multi-VSL/PTIT.

---

## 1. Hai câu chắc chắn bị hỏi

### 1.1. "Hệ thống của bạn đáp ứng được bao nhiêu user?" (trả lời như dev, có bằng chứng)

**Trả lời 30 giây:**
"Một instance hiện phục vụ ổn định **1–2 người đang ký liên tục**, tương đương khoảng **4–6 người dùng thưa**, vì
nhóm cố ý thiết kế **một slot suy luận**: quá tải thì trả 503 kèm Retry-After chứ không treo. Nhóm đã đo: local bão hoà
khoảng **30–36 ký hiệu/phút**, AWS c7i-flex.large khoảng **19 ký hiệu/phút**. Nút thắt là trích landmark MediaPipe
trên CPU; model GRU chỉ dưới 5 ms. Hướng scale là đưa trích landmark sang trình duyệt và scale ngang API vì API không
có trạng thái."

**Bằng chứng (mở `docs/performance-report.md` → "Kiểm tải đồng thời"):**

| Môi trường | 1 client | 2 client | 4 client | 8 client |
|---|---|---|---|---|
| Local i7-12700H | 36 ký hiệu/phút, p95 1,95 s | 32/phút, p95 5,7 s, 1 lần 503 | 28/phút, 19/35 lần 503 | 28/phút, 59/74 lần 503 |
| AWS c7i-flex.large | 14/phút, p95 5,4 s | 19,5/phút, 0 lần 503 | 19/phút, 14/25 lần 503 | lỗi ở tầng Quick Tunnel |

Tái lập: `python services/inference-api/scripts/load_test_predictions.py <url> <thư-mục-webm> 30 1,2,4,8`.

**Cách quy ra số người dùng** (nói rõ đây là ước lượng từ số đo):
- Một người ký liên tục tạo khoảng 1 ký hiệu mỗi 4–6 giây → 10–15 ký hiệu/phút.
- Hội thoại thực tế thưa hơn, khoảng 3–6 ký hiệu/phút mỗi người.
- 30–36 ký hiệu/phút ÷ 10–15 ≈ **2–3 người ký liên tục**; ÷ 6 ≈ **5–6 người dùng thưa** (local).
- Nếu tính đúng mục tiêu độ trễ SC-002 (≤ 3 s) thì chỉ đạt khi **1 người** dùng tại một thời điểm, trên máy local.

**Vì sao thiết kế một slot** (nếu bị hỏi "sao không cho nhiều request cùng lúc"):
MediaPipe ăn CPU; cho chạy song song trên 2 vCPU thì mọi request cùng chậm và RAM tăng (đã đo container API lên 1,35 GiB
ở tải cao, giới hạn 1,5 GiB). Từ chối sớm bằng 503 giữ độ trễ dự đoán được và không làm sập dịch vụ: kiểm tải không có
lần khởi động lại hay OOM (`RestartCount=0`, `OOMKilled=false`).

**Lộ trình scale** (phân biệt rõ đã làm / ước lượng):

| Bước | Thay đổi | Hiệu quả kỳ vọng | Trạng thái |
|---|---|---|---|
| 1 | Trình duyệt trích landmark (đã chạy MediaPipe hand + pose để lọc người), gửi tensor 32×234 thay video | Server chỉ chạy GRU (< 5 ms) → thông lượng mỗi instance tăng nhiều bậc; mất upload video | Ước lượng; cần chứng minh landmark trình duyệt khớp Python (cùng MediaPipe 1.1.1) |
| 2 | Scale ngang: API không trạng thái, không DB → N instance sau ALB | Tuyến tính theo số instance (~19–36 ký hiệu/phút mỗi instance với kiến trúc hiện tại) | Template CloudFormation có sẵn, chưa chạy nhiều instance |
| 3 | Nhiều worker/slot trên máy nhiều nhân | Tăng theo số nhân, đổi lại RAM | Chưa đo |

**Câu hỏi nối tiếp có thể gặp:**
- *"Nghìn người thì sao?"* → Kiến trúc hiện tại cần khoảng 40–60 instance (ước lượng tuyến tính), không kinh tế; nên
  phải làm bước 1 trước. Đây là MVP để chứng minh pipeline đúng, không phải hệ thống cho nghìn người.
- *"Đã test tải bằng công cụ chuẩn chưa (k6, Locust)?"* → Dùng script Python tự viết, gửi multipart thật, đo p50/p95;
  đủ cho một instance. Lên nhiều instance sẽ dùng k6.

### 1.2. "Đề tài có gì mới so với đề tài/sản phẩm hiện có?"

**Trả lời 30 giây:**
"Cái mới không nằm ở việc nhóm có model chính xác hơn (nhóm không tuyên bố điều đó). Cái mới là một **sản phẩm dịch
trực tiếp chạy được end-to-end và trung thực**: trình duyệt tự phát hiện người, mặt, tay rồi tự cắt từng ký hiệu; hệ
thống **biết nói 'không nhận diện được'** thay vì đoán; **không lưu video**; **train và phục vụ dùng chung một
pipeline** đã test khớp; và **chỉ được gắn nhãn sẵn sàng demo khi qua cổng chất lượng**."

**Năm điểm khác biệt, mỗi điểm một bằng chứng:**

| # | Điểm khác | Đề tài/demo thường gặp | Bằng chứng |
|---|---|---|---|
| 1 | Dịch trực tiếp không bấm nút: MediaPipe trong trình duyệt lọc người/mặt/tay và tự cắt ký hiệu; server chỉ nhận đoạn có người | Bấm quay/gửi từng lần, hoặc chạy model nặng liên tục | `apps/web/src/features/live/`, T105–T107 |
| 2 | Từ chối có kiểm soát: dưới ngưỡng (chọn trên validation) trả "Không nhận diện được" | Luôn trả nhãn có xác suất cao nhất | `docs/model-card.md`, T044/T048 |
| 3 | Riêng tư: clip là file tạm, xoá ở mọi nhánh kể cả lỗi; lịch sử chỉ trên trình duyệt 24 giờ | Thường không đề cập | `docs/admin-acceptance.md` (kiểm trên EC2: 0 clip còn lại) |
| 4 | Train và phục vụ dùng chung pipeline landmark → tensor 32×234, có test parity offline ↔ API | Tiền xử lý train và chạy thật viết riêng, dễ lệch | T014–T017, T037, T064 |
| 5 | Cổng phát hành: chỉ model full đủ 10 nghĩa, Macro-F1 ≥ 0,80, recall mỗi nghĩa ≥ 0,65 trên split theo video gốc và lead duyệt mới được `demoReady` | Báo accuracy trên tập ngẫu nhiên, dễ rò rỉ | T054, T057–T059, FR-015/016 |

**So với tài nguyên công khai cụ thể** (`docs/innovation-feasibility.md` mục 4):
- **Multi-VSL (WACV 2025)**: model video RGB nặng (I3D/MViT), không công bố bảng ánh xạ nhãn; nhóm đã thử và không
  dùng được cho 10 nghĩa P0.
- **VideoMAE của PTIT trên Hugging Face**: chỉ phủ 3/10 nghĩa P0.
- **Các demo MediaPipe + LSTM trên GitHub**: thường không có từ chối, không có chính sách dữ liệu, không có license.

**Câu bẫy nối tiếp:** *"Vậy model của bạn kém hơn họ?"* → "Đúng, ở thời điểm này model pilot còn yếu vì chỉ có 15 clip.
Nhóm chọn đầu tư vào pipeline và cổng chất lượng trước, vì đây là phần quyết định có dám đưa cho người dùng thật hay
không; thêm dữ liệu thì model cải thiện mà không phải viết lại hệ thống."

### 1.3. "Mô hình được train như thế nào?" (Cường trả lời, Quang bổ sung phần dữ liệu)

**Trả lời 30 giây:**
"Nhóm **không train trên pixel**. Mỗi clip đi qua MediaPipe để lấy toạ độ tay, vai/tay trên và một phần khuôn mặt, chuẩn
hoá theo vai, lấy lại mẫu thành **32 khung × 234 đặc trưng**, rồi đưa vào một **GRU một lớp, 64 nút ẩn, khoảng 58 nghìn
tham số**, train trên CPU. Chọn checkpoint theo loss validation, chọn ngưỡng từ chối cũng trên validation, test chỉ
chạy một lần ở cuối. Toàn bộ pipeline này cũng là pipeline API dùng khi chạy thật."

**Giải thích 2 phút, theo 6 bước (mở `ai/configs/feature_schema.json`, `ai/configs/pilot-gru.yaml`):**

| Bước | Làm gì | Chi tiết để trả lời vặn | File |
|---|---|---|---|
| 1. Dữ liệu và chia tập | Manifest đã kiểm, chia **theo video gốc** (`recordingSessionId`) để clip cắt từ cùng một video không rơi vào hai tập | Pilot: 15 clip, 4 lớp (Giấy tờ/Nhận × HCM/HN), train/val/test **7/4/4**, 13 video gốc; ghi `video-held-out` | `create_splits.py`, T018 |
| 2. Trích landmark | MediaPipe Tasks 1.1.1: hand (2 tay), pose, face; lấy tối đa 64 khung đều theo thời gian | **78 điểm**: 42 điểm tay + 6 điểm vai/khuỷu/cổ tay + 30 điểm mặt; chỉ lấy x, y | `feature_schema.json` |
| 3. Chuẩn hoá | Gốc toạ độ ở giữa hai vai, chia cho khoảng cách hai vai | Không phụ thuộc người đứng gần/xa, lệch trái/phải; điểm không thấy đặt 0 và đánh dấu | `sequence_transform.py` |
| 4. Lấy lại mẫu 32 khung | Nội suy tuyến tính theo thời gian thật (PTS) | **Không nội suy qua đoạn bị mất** để không bịa chuyển động; mỗi khung = 156 toạ độ + 78 cờ hợp lệ = **234** | schema v0.3 (APPROVED) |
| 5. Train | Nhân đặc trưng theo **trọng số nhóm tay 0,7 / mặt 0,2 / vai 0,1** (tay và vai ×1,30, mặt ×0,52 để tổng đóng góp đúng 70:20:10), rồi GRU 1 lớp, 64 nút ẩn → lớp tuyến tính; `pack_padded_sequence` cho chuỗi | Adam lr 0,001, batch 16, 30 epoch, cross-entropy, seed 42, CPU; **chọn checkpoint có loss validation thấp nhất** (pilot: epoch 24) | `train.py`, `gru_classifier.py` |
| 6. Chọn ngưỡng và đánh giá | Quét ngưỡng 0,5–0,9 **trên validation**: tối đa (đúng được chấp nhận − sai được chấp nhận), rồi độ phủ | Pilot chọn 0,5; test 4 clip chạy **một lần**: accuracy 25%, Macro-F1 0,33 → `demoReady=false` | `train.py`, `pilot-report.md` |

**Tái lập và truy vết:** mỗi artifact lưu SHA-256 manifest, digest schema, phiên bản extractor, lịch sử loss từng epoch,
bảng quét ngưỡng; W&B chạy offline (run `kbj3bpvu`); weights 234 KB, SHA-256 `0c9a991b…`. Cùng manifest + seed → cùng
kết quả.

**Câu hỏi nối tiếp có thể gặp:**

| Hỏi | Trả lời |
|---|---|
| Sao lại trọng số 70/20/10? | Tay quyết định từ; mặt chỉ biểu cảm; vai làm neo vị trí. Nếu để nguyên, mặt chiếm 38% đầu vào chỉ vì có 30 điểm. Với 15 clip pilot chưa đo được khác biệt (cùng 25% / 0,33); sẽ so trên bộ 10 nghĩa |
| Sao chọn GRU mà không phải Transformer/3D-CNN? | Dữ liệu rất ít (15 clip pilot, 101 clip toàn bộ); model nhỏ ít overfit hơn, chạy CPU < 5 ms, dễ giải thích. Transformer cần nhiều dữ liệu hơn nhiều |
| Sao dùng landmark mà không dùng ảnh? | Bỏ được nền, ánh sáng, màu da, quần áo; dữ liệu nhỏ hơn hàng nghìn lần; không phải lưu hình người; đổi lại mất thông tin khẩu hình chi tiết |
| Có augmentation không? | **Chưa.** Pilot train trên dữ liệu gốc. Bước tiếp: lật trái/phải có đổi tay, co giãn thời gian, nhiễu nhẹ toạ độ — phải tách theo video gốc trước khi tăng cường để không rò rỉ |
| 7 clip train thì overfit chắc chắn? | Đúng, đó là lý do kết quả test thấp và hệ thống tự gắn `demoReady=false`. Pilot dùng để chứng minh pipeline train → artifact → API chạy đúng, không phải để chứng minh độ chính xác |
| Sao 32 khung? | Ký hiệu dài 0,3–6 giây; 32 khung đủ giữ hình dạng chuyển động mà model vẫn nhỏ; cố định trong schema đã duyệt |
| Phân biệt vùng HCM/HN thế nào? | Train theo **lớp** (nghĩa × vùng × biến thể), hiển thị theo **nghĩa**: 4 lớp gộp về 2 nghĩa khi trả kết quả |
| Train ở đâu, bao lâu? | CPU laptop, vài giây cho pilot; không cần GPU |
| Làm sao chắc train và chạy thật dùng cùng tiền xử lý? | Cùng code `visign_ai`; test parity offline ↔ API khớp tuyệt đối tensor/mask (T037, T064) |
| Có train lại được khi có dữ liệu mới? | Có, bằng CLI hoặc công cụ admin (`/admin/train-model`, T078–T082); artifact mới phải qua cổng chất lượng mới được `demoReady` |

---

## 2. Bộ câu hỏi theo chủ đề

Cột "Ai" là người trả lời chính.

### 2.1. Bài toán và người dùng

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Ai dùng, dùng khi nào? | Người Điếc cần truyền một ý thiết yếu (y tế, hành chính, giao tiếp cơ bản) khi người đối diện không biết VSL | `docs/innovation-feasibility.md` §1 | Huy |
| Sao chỉ 10 từ? Ai chọn? | 10 nghĩa P0 thiết yếu, nhóm chốt 2026-11-07; MVP chứng minh pipeline với phạm vi kiểm soát được | `spec.md` FR-002, `data/manifests/p0-meanings.csv` | Huy |
| Đã thử với người Điếc thật chưa? | **Chưa.** Lead quyết định bỏ kiểm thử 10 người vì đây là bản trình chiếu chấm điểm. Có audit accessibility (axe WCAG A/AA 0 vi phạm) và nhóm tự thử webcam. Đây là bước đầu tiên sau MVP | `spec.md` Session 2026-11-08, T063 | Huy |
| Dịch được câu không? | Không. Mỗi ký hiệu là một nghĩa; bản dịch trực tiếp chỉ nối các nghĩa theo thứ tự, giao diện ghi rõ "chưa phải câu có ngữ pháp" | FR-001, FR-034 | Hiển |
| Có thay phiên dịch viên được không? | Không, và giao diện luôn hiện cảnh báo này | FR-010 | Huy |

### 2.2. Dữ liệu

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Có bao nhiêu dữ liệu? | Manifest v5: **101 clip, 10 nghĩa, 19 lớp** (76 clip tự quay, 25 từ website giáo dục). Mục tiêu 200 clip | `data/manifests/p0-source-v5.DRAFT.csv`, validator T012 | Quang |
| Dữ liệu lấy ở đâu, có bản quyền không? | Video giáo dục công khai và video nhóm tự quay; nguồn ghi theo từng clip; quyền khai ở mức bộ dữ liệu theo quyết định của lead; **không có bằng chứng cấp phép của bên thứ ba** | `docs/dataset-card.md` (T061 đang sửa) | Quang |
| Chia train/test thế nào để không rò rỉ? | Theo video gốc (`recordingSessionId`), gom bắc cầu cả xuyên nghĩa; ghi rõ là `video-held-out`, **không** tuyên bố người ký chưa thấy | FR-015, `create_splits.py`, T018/T056 | Quang |
| Người ký đa dạng chưa? | Chưa; phần lớn clip thiếu `signerId`; đây là rủi ro thiên lệch đã ghi trong dataset card | dataset card §9 | Quang |
| Nhãn đúng chưa, ai duyệt? | Nhãn `unverified` (chưa chuyên gia VSL xác nhận); hệ thống cho train nhưng ghi rõ trạng thái | manifest, data conventions | Quang |

### 2.3. Model và AI

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Model là gì, vì sao chọn? | MediaPipe trích 234 đặc trưng/khung (tay, pose, mặt) × 32 khung → GRU nhỏ; chạy CPU, GRU < 5 ms | `feature_schema.json` v0.3, `gru_classifier.py` | Cường |
| Độ chính xác bao nhiêu? | Pilot Giấy tờ/Nhận: **accuracy 25%, Macro-F1 0,33** trên 4 clip test; `demoReady=false`. Không tuyên bố model đạt | `docs/pilot-report.md`, `docs/model-card.md` | Cường |
| Sao kết quả thấp vẫn đem đi demo? | Demo chứng minh hệ thống: pipeline, từ chối, riêng tư, cổng chất lượng. Giao diện tự hiện "Thí điểm giới hạn (pilot), chưa sẵn sàng demo" | UI, FR-016 | Cường/Huy |
| Ngưỡng từ chối chọn thế nào? | Chọn trên tập validation, lưu vào artifact; **không** chỉnh theo kết quả test | T044, `pilot-report.md` | Cường |
| Có overfit không? | Có rủi ro rõ (15 clip, 11/19 lớp chỉ 1 clip trong bộ cũ). Vì thế split theo video gốc và cổng chất lượng là bắt buộc trước khi gắn demoReady | dataset card §6, §9 | Cường |
| Sao không dùng model lớn sẵn có? | Đã khảo sát Multi-VSL, PTIT: không phủ 10 nghĩa hoặc thiếu license/nhãn; nặng, cần GPU | `innovation-feasibility.md` §4 | Cường |

### 2.4. Kiến trúc và kỹ thuật

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Kiến trúc tổng thể? | React/Vite (trình duyệt) → nginx → FastAPI `/api/v1` → `visign_ai` (MediaPipe + GRU); 2 container Docker trên 1 EC2 | `docs/architecture-quality-report.md` | Tín |
| Trình duyệt làm gì, server làm gì? | Trình duyệt: phát hiện người/mặt/tay (MediaPipe WASM) để cắt đoạn; server: trích đủ đặc trưng + nhận diện | T105–T106 | Huy/Hiển |
| Sao không nhận diện luôn trên trình duyệt? | Đó là bước scale 1; cần chứng minh đặc trưng trình duyệt khớp Python trước, nếu không model sẽ sai lặng lẽ | mục 1.1 | Cường |
| API contract quản lý thế nào? | OpenAPI trong `specs/.../contracts/openapi.yaml`; mã lỗi ổn định có test contract | T019–T026 | Tín |
| Làm sao biết train và chạy thật không lệch? | Test parity offline ↔ API trên clip thật (khớp tuyệt đối tensor/mask) | T037, T064 | Cường |

### 2.5. Hiệu năng

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Từ lúc ký xong tới lúc hiện chữ bao lâu? | Local **1,2–2,0 s**; AWS c7i-flex.large **3,9–5,4 s** (gồm upload VN → Sydney); t3.small 5,5–6,3 s | `docs/deployment-report.md` | Huy |
| Đạt mục tiêu ≤ 3 s chưa? | Local đạt; cloud **chưa** — nút thắt là trích landmark (2,5–3,4 s) và upload | `performance-report.md` | Cường |
| Đã tối ưu gì? | Tạo sẵn detector ở luồng nền (−194 ms/request khi có khoảng nghỉ), chạy 3 nhóm detector song song, lấy tối đa 64 khung, đổi lên c7i-flex.large (−35% thời gian xử lý) | T065 evidence | Cường/Tín |
| Tốn bao nhiêu RAM? | API nghỉ ~450 MiB (giữ detector sẵn), đỉnh ~1 GiB khi xử lý, 1,35 GiB ở tải cao | `deployment-report.md`, kiểm tải | Tín |

### 2.6. Bảo mật và quyền riêng tư

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Video có bị lưu không? | Không: file tạm trên tmpfs, xoá ở mọi nhánh; đã kiểm trên EC2 sau nhiều request: 0 clip còn lại | `admin-acceptance.md` §3 | Tín |
| Tự ghi liên tục có xâm phạm riêng tư? | Chỉ ghi khi thấy người, mặt và tay đang chuyển động; có Tạm dừng/Tắt; chuyển tab tự tạm dừng; giao diện nói rõ tự gửi và tự xoá | FR-004 (sửa) | Hiển |
| Bảo mật web? | CSP chặt (`default-src 'self'`, chỉ thêm `'wasm-unsafe-eval'` cho WASM cùng origin), không lộ phiên bản server, không bật tài liệu API ở production | `infra/aws/nginx/security-headers.conf`, T092 | Tín |
| Container an toàn chưa? | Chạy user không root (uid 10001), root filesystem chỉ đọc, bỏ hết capability, giới hạn RAM | `compose.production.yml`, CI job docker | Tín |
| Admin có bị lộ không? | Tắt mặc định (404); bật thì cần token ≥ 16 ký tự, so sánh hằng thời gian, không log token | T078–T080 | Tín |
| Có secret trong repo không? | CI chặn file secret/model/video; EC2 dùng IAM role, không access key | job `hygiene`, T092 | Tín |

### 2.7. Cloud và chi phí

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Deploy thế nào? | CloudFormation: ECR + S3 private + EC2 (IAM role, không SSH, quản trị qua SSM) + Elastic IP; image theo commit SHA | `infra/aws/cloudformation/` | Huy/Tín |
| Chi phí bao nhiêu? | Free Plan, credit 100 USD; t3.small ~0,9 USD/ngày; c7i-flex.large chỉ bật trong ngày demo; Budget cảnh báo 5/20/50 USD | `deployment-report.md`, `cost-report.md` | Huy |
| Sao HTTPS qua Cloudflare Tunnel, không CloudFront? | Tài khoản mới bị AWS chặn tạo CloudFront tới khi xác minh; tunnel là giải pháp tạm, đã ghi rõ giới hạn | `deployment-report.md` | Huy |
| CI/CD? | GitHub Actions 5 job (API, AI, web, Docker build + MediaPipe + smoke 14/14, hygiene); deploy hiện thủ công vì OIDC bị SCP Free Plan chặn | `.github/workflows/quality.yml` | Huy |

### 2.8. Chất lượng phần mềm và quy trình nhóm

| Câu hỏi | Trả lời ngắn | Bằng chứng | Ai |
|---|---|---|---|
| Test bao nhiêu? | API + contract ~400 test; AI 175; web 191 unit + 75 Playwright (3 viewport, axe) + 6 E2E với backend thật | CI, evidence | Huy |
| Chia việc thế nào? | 5 vai (P1–P5) theo `tasks.md` 107 task; mỗi task có evidence, review chéo, không tự xác nhận việc mình làm | `specs/.../tasks.md`, `docs/evidence/` | Huy |
| Tiến độ? | 79/107 task đã nghiệm thu; phần còn lại chủ yếu chờ dữ liệu full và CloudFront | `docs/team/implementation-status.md` | Huy |
| Có dùng AI để code? | Có, như công cụ; mọi thay đổi qua test/CI/review chéo có ghi lại; ví dụ lỗi thiếu `libEGL` trong Docker được phát hiện bằng smoke thật và có job CI chặn tái diễn | T091, T095 | Huy |

### 2.9. Giới hạn và rủi ro (tự nói trước khi bị hỏi)

1. Model pilot chỉ 2 nghĩa, Macro-F1 0,33 → chưa dùng được thật.
2. Dữ liệu 101/200 clip, thiếu đa dạng người ký, nhãn chưa chuyên gia duyệt.
3. Độ trễ cloud 3,9–5,4 s, chưa đạt ≤ 3 s.
4. Một instance phục vụ 1–2 người ký liên tục.
5. Chưa kiểm thử với người Điếc thật.
6. HTTPS tạm qua Quick Tunnel; CloudFront chờ AWS xác minh.

Cách nói: "Nhóm liệt kê công khai 6 giới hạn này trong repo; mỗi giới hạn có số đo và hướng xử lý."

### 2.10. Mở rộng và tính bền vững

| Câu hỏi | Trả lời ngắn | Ai |
|---|---|---|
| Thêm từ mới có phải sửa code? | Không, trong giới hạn ≤ 10 nghĩa của contract MVP: thêm dữ liệu, train lại, artifact mới tự công bố danh sách nghĩa. Quá 10 cần đổi contract | Cường |
| Mở rộng câu/hội thoại? | Ngoài MVP; cần nhận diện chuỗi và mô hình ngôn ngữ | Cường |
| Sau cuộc thi có tiếp tục không? | Cần đối tác cộng đồng người Điếc để có dữ liệu và kiểm thử thật; chi phí vận hành nhỏ nếu chuyển landmark sang trình duyệt | Huy |

---

## 3. Câu hỏi bẫy và cách xử lý

| Câu bẫy | Đừng nói | Nên nói |
|---|---|---|
| "Accuracy 25% thì làm được gì?" | "Do ít dữ liệu thôi ạ" (đổ lỗi) | "Đúng, nên hệ thống tự gắn `demoReady=false` và giao diện cảnh báo. Thứ nhóm chứng minh là pipeline và cổng chất lượng; đây là cổng đó (mở bảng)." |
| "Bạn có dùng video người khác không xin phép?" | Lảng tránh | "25/101 clip từ website giáo dục công khai, ghi nguồn từng clip; quyền khai ở mức bộ dữ liệu, không có văn bản cấp phép bên thứ ba — đã ghi rõ trong dataset card là rủi ro." |
| "1 slot thì sao gọi là hệ thống?" | "Do máy yếu" | "Thiết kế có chủ đích để fail-fast; đây là số đo; đây là đường scale có ước lượng." |
| "Demo này có phải dựng sẵn?" | — | "Mời BGK tự mở link trên điện thoại" (chuẩn bị QR) hoặc chạy local trước mặt BGK. |
| "Sao không làm app mobile?" | — | "Web chạy trên mọi máy có camera, không cài đặt; camera chỉ cần HTTPS." |
| "Nếu nhận sai ý quan trọng (ví dụ 'Không' thành 'Nhận')?" | — | "Đó là lý do có từ chối dưới ngưỡng và cảnh báo không thay phiên dịch viên; với từ đối nghĩa nên đặt ngưỡng riêng — hướng tiếp theo." |

---

## 4. Số cần thuộc

| Chủ đề | Số |
|---|---|
| Phạm vi | 10 nghĩa P0; pilot 2 nghĩa (Giấy tờ, Nhận) |
| Dữ liệu | 101 clip / 19 lớp / mục tiêu 200; pilot 15 clip, split 7/4/4 theo video gốc |
| Model pilot | accuracy 25%, Macro-F1 0,33, `demoReady=false`; GRU < 5 ms |
| Cổng chất lượng | Macro-F1 ≥ 0,80, recall mỗi nghĩa ≥ 0,65, split `video-held-out`, lead duyệt |
| Độ trễ | local 1,2–2,0 s; AWS c7i 3,9–5,4 s; t3.small 5,5–6,3 s |
| Capacity | 1 slot; local ~30–36 ký hiệu/phút; AWS ~19/phút; 1–2 người ký liên tục/instance |
| Đặc trưng | 32 khung × 234 đặc trưng; schema v0.3 APPROVED |
| Kiểm thử | API ~400, AI 175, web 191 + 75 Playwright + 6 E2E; CI 5 job |
| Cloud | ap-southeast-2; EC2 + ECR + S3 + SSM; credit 100 USD; Budget 5/20/50 USD |
| Tiến độ | 79/107 task |

## 5. Chuẩn bị trước buổi chấm

- [ ] Stack local chạy sẵn (`http://127.0.0.1:8080`) làm demo chính; link AWS + mã QR làm bằng chứng cloud.
- [ ] Mở sẵn các tab: `performance-report.md` (kiểm tải), `model-card.md`, `admin-acceptance.md`, CI xanh, `tasks.md`.
- [ ] Mỗi thành viên tập trả lời 3 câu của phần mình theo công thức 0.1, mỗi câu ≤ 45 giây.
- [ ] Diễn tập một vòng hỏi vặn: một người đóng vai BGK hỏi lần lượt mục 1 và mục 3.
