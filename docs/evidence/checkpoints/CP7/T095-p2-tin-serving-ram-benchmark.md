# CP7 T095 — benchmark RAM và độ trễ đường phục vụ để chọn instance AWS

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP7 / T095` (chuẩn bị chọn instance; theo yêu cầu P1 trong `implementation-status.md`) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy` (quyết định instance); `P3 Cường` (bộ nhớ decoder T015) |
| Candidate commit | `CP7 T095(cloud): add serving RAM and latency benchmark for AWS sizing` |
| Commit | `PENDING` — bổ sung full SHA/link sau push |
| Ngày/giờ | `2026-11-07T17:10+07:00` |
| Môi trường đo | Windows 11 (máy P2), CPython 3.12.15, extra `serving`: visign-ai 0.0.1, MediaPipe 1.1.1, OpenCV 5.0.0.93, PyAV 19.0.2, torch 2.11.0+cpu |
| Status | `PASS` (số đo Windows); số đo Linux/EC2 `NOT_RUN` |

## 2. Cách đo

Script `services/inference-api/scripts/benchmark_serving_memory.py`:

- Sinh clip WebM tổng hợp gần mức tối đa contract (5,9 s ≤ 6000 ms) vào thư mục tạm và xóa sau khi đo;
  nội dung là gradient chuyển động nén được nên dung lượng clip nhỏ — RAM chủ yếu do **frame đã giải mã**,
  không phụ thuộc dung lượng nén.
- Mỗi clip đo trong **một tiến trình mới**, ghi RAM đỉnh (Windows `PeakWorkingSetSize`, Linux `ru_maxrss`)
  theo thứ tự giống tiến trình phục vụ: import `visign_api.main` → nạp pipeline `visign_ai` → import `torch`
  (GRU sẽ cần) → hai lần `extract` theo đúng đường API (bytes → clip tạm → adapter T037).
- Kiểm tra đầu dò: cấp phát thêm 300 MB làm RAM đỉnh tăng đúng 300 MB.

Tái lập (kể cả trên EC2 Linux):

```bash
uv sync --project services/inference-api --extra serving
uv run --project services/inference-api python ai/setup_models.py   # nếu chưa có detector
uv run --project services/inference-api --extra serving \
  python services/inference-api/scripts/benchmark_serving_memory.py --runs 2
```

## 3. Kết quả (Windows, RAM đỉnh của tiến trình, MB)

| Clip | Frame giải mã | Sau import API | + pipeline | + torch | Lần 1: thời gian / RAM đỉnh | Lần 2: thời gian / RAM đỉnh |
|---|---|---|---|---|---|---|
| VP8 640×480 30 fps 5,9 s | 178 | 42 | 108 | 257 | 3025 ms / 483 | 2891 ms / 490 |
| VP9 640×480 30 fps 5,9 s | 178 | 42 | 108 | 256 | 2900 ms / 484 | 2432 ms / 490 |
| VP8 1280×720 30 fps 5,9 s | 178 | 42 | 108 | 257 | 3368 ms / 467 | 3046 ms / 475 |
| VP8 640×480 60 fps 5,9 s | 355 | 42 | 108 | 256 | 3219 ms / 575 | 2780 ms / 604 |

Decode chiếm 93–450 ms; phần còn lại là MediaPipe trên tối đa 64 frame đã lấy mẫu (kèm khởi tạo 3 detector mỗi clip).
Clip 1280×720 được decoder thu về cạnh dài 640 px nên tốn RAM ít hơn 640×480.

## 4. Đánh giá cho EC2

| Thành phần trên một host | Ước lượng |
|---|---|
| Hệ điều hành + Docker daemon (Amazon Linux 2023) | ~200–350 MB |
| Container web tĩnh | ~10–30 MB |
| Container API khi xử lý một clip (một lượt suy luận nhờ coordinator T026) | ~480–600 MB (Windows; Linux cần đo lại) |
| Model GRU + bộ nhớ suy luận | Chưa đo (T033/T036 của P3); dự kiến vài chục MB |
| **Tổng** | **~0,7–1,0 GB** |

Kết luận:

1. **Instance 1 GB RAM (ví dụ `t3.micro`) không đủ an toàn**: gần như không còn dư, clip 60 fps hoặc tiến trình
   phụ có thể gây OOM. Đề xuất tối thiểu **2 GB** (ví dụ `t3.small`); nếu buộc dùng 1 GB thì phải có swap và
   chấp nhận chậm.
2. **CPU**: chỉ phần đặc trưng đã 2,4–3,4 s/clip trên máy P2, sát gate p95 ≤ 3 s (SC-002) trước khi tính GRU/HTTP.
   Instance burstable (`t3.*`) chạy MediaPipe liên tục có thể cạn CPU credit và chậm hơn nhiều; cần đo trên
   instance đích (T094/T065 của P3) trước khi chốt.
3. **Giảm RAM**: decoder T015 giữ toàn bộ frame RGB trước khi lấy mẫu 64 frame (ghi chú review T014–T016 của P1).
   Lấy mẫu theo PTS trước khi chuyển RGB có thể bớt ~150–300 MB cho clip 30–60 fps — đề xuất cho P3.

## 5. Giới hạn

- Đo trên Windows; Linux/Docker có thể khác. Cần chạy lại script trên instance đích trước khi chốt (T095).
- Clip tổng hợp không có người; MediaPipe chạy cùng số frame nên thời gian/RAM tương đương bậc độ lớn, nhưng
  cần xác nhận với clip đại diện.
- Chưa có model GRU thật nên chưa đo bộ nhớ/thời gian suy luận.

**Reviewer result**: `PENDING`
