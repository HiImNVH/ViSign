# CP3 T037/T049 smoke evidence — clip có người thật qua đường API

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP3 / T037` (parity offline ↔ API, dự đoán GRU qua HTTP); `CP4 / T049` (quy tắc người/landmark, thời lượng) |
| Owner | `P2 Tín` |
| Reviewer | `P3 Cường` (parity, quy tắc T049); `P1 Huy` |
| Baseline | `origin/main` `181408e` (đã pull T046 của P5, T058/T059 của P3 và review P1 đánh dấu T037/T045/T049/T050 `[X]`); evidence bổ sung cho T037 đã đóng |
| Commit | `0f3c5578767717d9c4a4e7c94999b1de9005eb00` — [0f3c557](https://github.com/HiImNVH/ViSign/commit/0f3c5578767717d9c4a4e7c94999b1de9005eb00); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42385392156) |
| Ngày/giờ | `2026-11-07T22:09+07:00` |
| Môi trường | Windows 11, CPython 3.12.15, extra `serving` (torch 2.11.0+cpu, MediaPipe 1.1.1), uvicorn local |
| Status | `PASS` cho cơ chế; độ trễ chưa đạt SC-002 trên máy này |

## Dữ liệu và quyền riêng tư

- 38 clip quay bằng iPhone trong thư mục local của owner: HEVC 1920×1080, 30 fps, metadata xoay −90°;
  32 clip dài 3,3–5,1 s, 6 clip dài 8,8–11,6 s. Không chép vào repo, không commit, không ghi tên file;
  evidence chỉ dùng chỉ số `clip01`–`clip38` và số liệu tổng hợp, không có ảnh, frame hay landmark.
- Mỗi clip được chuyển sang WebM VP8 đứng thẳng 360×640, 30 fps, 1,5 Mbps, không âm thanh (mô phỏng clip
  MediaRecorder dọc). Chiều xoay (90° theo chiều kim đồng hồ) được xác định bằng MediaPipe Pose (mũi nằm trên
  hai vai), không xem ảnh. Bản chuyển đổi được xóa ngay sau khi kiểm.

## Kết quả

| Gate | Kết quả |
|---|---|
| Parity offline ↔ API | **32/32 PASS**: `process_video` offline và bytes → clip tạm → `FeatureExtractor` cho tensor `32×234` trùng tuyệt đối (sai khác lớn nhất `0,0`), tensor mask và group mask khớp, `inputStatus` khớp, clip tạm bị xóa |
| Thời lượng | 6 clip > 6 s: cả hai đường trả `CLIP_TOO_LONG` |
| Quy tắc T049 (P3) | 32/32 `HAS_USABLE_FRAMES` → được phân lớp; tỉ lệ bước tensor dùng được 0,84–1,0 (trung vị 0,98); tỉ lệ frame có tay 0,92–1,0 |
| HTTP thật | uvicorn + artifact pilot do CLI T036 train trên tensor tổng hợp: 32 × 200, 6 × 422 `CLIP_TOO_LONG`; `X-Request-ID` khớp body ở mọi response; 0 file `visign_clip_*` còn lại |
| Log | JSON chỉ có field allowlist (`requestId`, `modelVersion`, timings, `accepted`, `errorCode`, method/path/status); các dòng chứa chữ "landmark" là log C++ của MediaPipe (tên file nguồn), không có dữ liệu |
| Độ trễ (CPU Windows) | `processingTimeMs` p50 3,72 s, p95 4,73 s, max 5,25 s; trích đặc trưng p50 3,53 s, p95 4,48 s; giải mã ≤ 259 ms; GRU ≤ 16 ms |
| Tương thích T059 | Sau khi pull T059 (`train.py` dựng metadata qua `build_model_metadata`), API + contract với extra `serving` 350 passed, 1 skipped: adapter vẫn nạp đúng artifact do CLI T036 tạo |

## Giới hạn và rủi ro

- Trọng số GRU là bản tổng hợp của test T036 nên mọi clip đều ra `CAM_ON_HN_1` (0,80–0,84). Kết quả chỉ chứng
  minh cơ chế đặc trưng thật → GRU → luật quyết định → response, **không** chứng minh nhận diện VSL.
- SC-002 (p95 ≤ 3 s) chưa đạt trên máy này: nút cổ chai là trích đặc trưng MediaPipe, khớp benchmark T095.
  Chuyển P3 (tối ưu decode/trích) và T095 (chọn instance, đo lại trên Linux).
- Clip dọc 360×640 từ điện thoại; chưa thử webcam ngang hay clip ghi trực tiếp từ trình duyệt (T043/T032).

**Reviewer result**: `PENDING`

## Independent review — P1/Huy

Review `2026-11-07T22:16:40+07:00` trên `0f3c557` (theo uỷ quyền của Huy). Evidence nhất quán với review T037/T049 trước: parity
offline ↔ API 32/32 clip trùng tuyệt đối, HTTP thật trả đúng 200/422, `X-Request-ID` khớp, không còn clip
tạm, log chỉ có field allowlist; tương thích metadata T059. T037 đã `[X]`.

**Rủi ro ghi nhận**: độ trễ trên máy đo **chưa đạt SC-002** (p95 ≤ 3 s) — cần tối ưu decode/extract (P3)
và đo lại trên máy demo trước CP8.

**Reviewer result**: `P1_VERIFIED`.
