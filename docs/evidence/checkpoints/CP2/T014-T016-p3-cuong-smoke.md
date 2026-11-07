# CP2 · T014–T016 · P3/Cường

| Mục | Kết quả |
|---|---|
| Baseline `main` | `18a07aef641b424ddf4772249623b1bc04a4b926` |
| Candidate commit và link GitHub | `PENDING`, bổ sung sau push |
| Review | P2/Tín review đường serving, P1/Huy review clip và quyết định chốt schema |
| Gate cục bộ | `PASS` |
| Parity offline ↔ API và review schema | `NOT_RUN` |
| Cửa tích hợp | `WAITING` |

## Phạm vi

- T014 có bộ test decoder, orientation, thời lượng theo PTS, corrupt, format, giới hạn kích thước, tensor/mask, lấy mẫu, schema và hash detector.
- T015 có decoder PyAV cho WebM VP8/VP9, MediaPipe VIDEO cho hai tay, vai/cánh tay và mặt. MP4 chỉ bật tường minh cho công cụ offline. Có thêm giới hạn tài nguyên 4K và 900 frame, ảnh đầu vào MediaPipe có cạnh dài tối đa 640 px.
- T016 có pipeline chung `visign_ai.landmarks.pipeline.process_video`. Schema `visign-xy-32-v0.3-draft` tạo tensor float32 32×234, chuẩn hóa theo hai vai, lấy tối đa 64 frame theo PTS và giữ mask điểm thiếu. Schema còn `DRAFT_PENDING_LEAD_REVIEW`.
- T017 CLI trích manifest thuộc lượt kế tiếp. Không có bulk extraction hoặc huấn luyện trong lần này.

## Bằng chứng ngày 2026-11-07

| Kiểm tra | Kết quả |
|---|---|
| Pytest AI với Python 3.12.15 | 20 passed, gồm 19 test CP2 và 1 test CP1 |
| Chrome 156.0.8078.76 và Edge 156.0.4314.50 | 4/4 clip MediaRecorder VP8/VP9 giải mã được, PTS tăng. Video thu từ canvas phát clip tham chiếu |
| MediaPipe 1.1.1, 3 detector đúng SHA-256 | Clip Chrome VP9 có frame dùng được, hai lượt offline khớp tensor ở atol=1e-6 và khớp tuyệt đối các mask |
| Ruff check và format, mypy | Đạt |
| Clip camera vật lý và review động tác đại diện | `NOT_RUN`, chờ clip đại diện để kiểm độ giữ động tác sau lấy mẫu và quy ước trái/phải |
| Golden offline ↔ đường API | `NOT_RUN`, checkout hiện có scaffold backend. Sau T037, cùng một WebM và schema phải so tensor ở atol=1e-6 và so tuyệt đối mask điểm, nhóm và tensor |

SHA-256 tệp schema là `f0c61f1987fb608a6b49db1c7b66bea7e00a4f2e3e675c11ea6b096d9c37badd`.
SHA-256 tệp manifest detector là `2ea6002c441d28d777a547ea92820ff9a34ad94d28d3cb9a9d882dc932b680f4`.
Detector version là `tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3`.

## Tái lập từ gốc repo

```powershell
uv sync --project ai --locked
uv run --project ai --locked python ai/setup_models.py
uv run --project ai --locked pytest ai/tests -q
uv run --project ai --locked ruff check ai
uv run --project ai --locked mypy ai/src
```

Để chạy cả test browser và MediaPipe thật, đặt `VISIGN_BROWSER_FIXTURES` trỏ vào thư mục có `chrome-vp8.webm`, `chrome-vp9.webm`, `msedge-vp8.webm`, `msedge-vp9.webm` và `VISIGN_CP2_REFERENCE_WEBM` trỏ vào clip tham chiếu có người. Có thể chỉ định detector đã tải qua `VISIGN_MODEL_DIR`. Các tệp video và detector được giữ ngoài Git. Thiếu fixture, pytest báo skip các test tương ứng.

Đóng CP2 còn cần T098/T099. Trước commit và push thực hiện quy trình đồng bộ và chạy lại gate theo [Git checkpoints](../../../team/git-checkpoints.md).
