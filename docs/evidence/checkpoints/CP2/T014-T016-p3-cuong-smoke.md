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

## Independent review — P1/Huy

Review time: `2026-11-07T14:23:43+07:00` trên `origin/main` chứa `865547e` (commit T014–T016; evidence chưa điền SHA).

| Gate | Kết quả độc lập |
|---|---|
| Local Windows | `uv sync --locked`, Ruff, mypy (10 files): PASS; pytest 15 passed, 5 skipped (thiếu clip browser/tham chiếu và detector local) |
| GitHub Actions Linux | [run 42351034900](https://github.com/HiImNVH/ViSign/actions/runs/42351034900) job `ai`: Ruff, mypy, 15 passed / 5 skipped — `success` |
| Contract | Schema `visign-xy-32-v0.3-draft`, tensor `[32,234]`, giới hạn 10 MiB/300–6000 ms/VP8-VP9 khớp [ai-backend-contract.md](../../../team/ai-backend-contract.md) |
| Real MediaPipe/parity | `NOT_RUN` bởi P1: chưa có clip đại diện; giữ `NOT_RUN` như owner |

Ghi chú không chặn — cần xử lý trước khi đóng CP2/CP3:

1. **Mã lỗi ngoài catalog API**: pipeline phát `INVALID_TIMESTAMPS`, `FEATURE_SCHEMA_MISMATCH`,
   `EXTRACTOR_VERSION_MISMATCH`. Adapter T037 (Tín) phải ánh xạ tường minh: `INVALID_TIMESTAMPS` →
   `CLIP_DECODE_FAILED` (422); hai mã schema/extractor → `MODEL_NOT_READY` (503) vì là lỗi cấu hình.
   Cần test mapping, không để rơi vào 500.
2. **Handedness**: MediaPipe gán `Left/Right` giả định ảnh đã lật kiểu selfie, còn pipeline giữ ảnh camera
   gốc nên nhãn có thể ngược với tay thật của người ký. Train/serve nhất quán nên chưa sai, nhưng video
   nguồn đã bị lật sẵn sẽ đảo trái/phải. Representative-clip review phải kiểm, và Quang ghi cờ
   `mirrored` trong inventory khi nguồn đã lật.
3. **Bộ nhớ decode**: mọi frame được giải mã sang RGB trước khi lấy mẫu 64 frame. Clip 6 s ở 60 fps,
   640 px là khoảng 250 MB RAM; trần 900 frame khoảng 600 MB. Cần đo với giới hạn RAM Cloud Run (T095) hoặc
   lấy mẫu theo PTS trước khi chuyển RGB.
4. **Khởi tạo detector mỗi clip**: đúng yêu cầu reset tracking, nhưng đọc lại model và tạo 3 detector mỗi
   request nằm trong p95 latency; số 1,8–2,1 s của Cường đã gồm phần này, cần đo lại trên máy Tín.
5. **CLIP_TOO_SHORT** dùng khoảng PTS frame đầu→cuối nên ngắn hơn thời lượng thật một khoảng frame
   (~33 ms ở 30 fps). FE ghi mặc định 5 s nên không ảnh hưởng thực tế; ghi lại để test biên khớp nhau.
6. Evidence còn `PENDING` commit SHA; Cường điền `865547e` trong commit link evidence kế tiếp.

**Reviewer result**: `P1_REVIEWED` — code/gate đạt; P2 review đường serving và representative-clip
review schema vẫn `PENDING`. Schema giữ `DRAFT_PENDING_LEAD_REVIEW`.

## Independent API-boundary review — P2/Tín

Review time: `2026-11-07T14:25+07:00` trên `origin/main` chứa `865547ebe637da010ac7c953bcce38389ecca831`;
worktree sạch. Phạm vi: đường serving mà adapter T037/T049 sẽ gọi.

| Gate | Kết quả độc lập |
|---|---|
| Env | `uv sync --project ai --locked`; `ai/setup_models.py` tải 3 detector, SHA-256 khớp manifest: PASS |
| Unit | `pytest ai/tests -q -rs`: 15 passed, 5 skipped (thiếu `VISIGN_BROWSER_FIXTURES`, `VISIGN_CP2_REFERENCE_WEBM`) |
| Lint/format/type | `ruff check ai`, `ruff format --check ai`, `python -m mypy ai/src`: PASS |
| Boundary probe | Gọi `process_video` như API với clip PyAV tổng hợp 320×240, 30 fps |

| Clip tổng hợp | Kết quả pipeline | Mã/status API |
|---|---|---|
| VP8 1,5 s, VP9 1,5 s (không có người) | Tensor `[32,234]`, `inputStatus=INSUFFICIENT_LANDMARKS` | Cần quy tắc T049 (mục 2) |
| 0,2 s | `CLIP_TOO_SHORT` | 422, khớp catalog |
| 6,5 s | `CLIP_TOO_LONG` | 422, khớp catalog |
| Thân file hỏng | `CLIP_DECODE_FAILED` | 422, khớp catalog |
| Không phải WebM | `UNSUPPORTED_MEDIA_TYPE` | 415, khớp catalog |
| > 10 MiB | `CLIP_TOO_LARGE` | 413, khớp catalog |

Bổ sung cho ghi chú P1 (không lặp lại mục 1–6 của P1):

1. **Độ trễ trên máy P2** (trả lời mục 4 của P1): `process_video` với 46 frame 320×240 mất `7400 ms`
   ở lần gọi đầu và `2580–2640 ms` ở các lần sau; extract kèm khởi tạo detector `2310–2540 ms`, kiểm
   hash detector `~60 ms` mỗi lần. Chưa gồm GRU/HTTP nên sát gate p95 ≤ 3 s. API sẽ warm-up lúc startup;
   đề xuất P3 cho phép cache `extractor_identity` một lần mỗi tiến trình.
2. **`NO_PERSON_DETECTED` không bao giờ được phát** và `INSUFFICIENT_LANDMARKS` chỉ nằm trong
   `report.inputStatus`, không raise. P2/P3 cần chốt quy tắc (ví dụ không frame nào có vai →
   `NO_PERSON_DETECTED`) trước T049.
3. **`MODEL_ASSET_MISMATCH`** (detector thiếu/sai hash) cũng nằm ngoài catalog; adapter T037 ánh xạ
   sang `MODEL_NOT_READY` (503) cùng nhóm với mục 1 của P1.
4. Đổi kích thước frame giữa clip, > 900 frame hoặc > 4K trả `INVALID_REQUEST` (400); với clip camera
   đây là lỗi nội dung clip hơn lỗi request, đề xuất 422 `CLIP_DECODE_FAILED` (đưa vào T099 nếu đồng ý).
5. Giới hạn 10 MiB/300/6000 ms đang khai báo ở cả decoder và `services/inference-api/.../config.py`
   (T022); đề xuất export hằng số từ `visign_ai` để dùng chung một nguồn.
6. Kết quả `process_video` chứa landmark thô (`coords`, `ambiguous[].candidateXY`); API chỉ dùng
   `tensor`/`report`, không log hoặc trả các trường này (FR-019).
7. Theo `.agent/core.md`: file chưa có header path, hàm chưa có type hint, comment tiếng Anh, vài hàm
   > 30 dòng (`process_video`, `extract`, `decode_video`). Không chặn.

**Reviewer result**: `P2_VERIFIED` cho đường serving của T014–T016; parity offline ↔ API giữ `NOT_RUN`
đến T037.

**Reviewer note**: Không cần sửa trước khi đóng T014–T016; mục 2 cần P3 xác nhận, mục 1/3 do P2 xử lý
trong T037/T049.
