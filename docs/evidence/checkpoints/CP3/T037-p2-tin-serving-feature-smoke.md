# CP3 T037 smoke evidence — adapter đặc trưng phía API và parity offline ↔ API

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP3` (lát thứ hai của T037, module thuần, chưa mở endpoint) |
| Task | `T037` — đường serving đặc trưng; predictor GRU/registry/fixture vẫn mở |
| Owner | `P2 Tín` |
| Reviewer | `P3 Cường` (đường serving, parity); `P1 Huy` |
| Quyết định phạm vi | Owner làm theo đề nghị của P3 ("Tín nối đường serving T037") dù P1 chưa đóng CP2; giữ đúng tiền lệ P1 chấp nhận cho `5b6a441` (module thuần, không endpoint) |
| Candidate commit | `CP3 T037(api): add serving feature extraction adapter with parity test` |
| Commit | `7d5c16ac3db817764d042853b8b6276cd825b870` — [7d5c16a](https://github.com/HiImNVH/ViSign/commit/7d5c16ac3db817764d042853b8b6276cd825b870); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42361742686) — job `api` cài `uv sync --locked` không kèm extra `serving` |
| Ngày/giờ | `2026-11-07T16:50:27+07:00` |
| Môi trường | Windows 11, uv 0.13.7, CPython 3.12.15; extra `serving`: visign-ai 0.0.1 (editable), MediaPipe 1.1.1, torch 2.11.0+cpu |
| Status | `PASS` local và CI; parity clip đại diện chờ P1/P3 |

## 2. Phạm vi thay đổi

| File | Nội dung |
|---|---|
| `src/visign_api/inference/feature_extraction.py` | `FeatureExtractor.extract(clip_path)` gọi `visign_ai.landmarks.pipeline.process_video`; `PipelineError` → exception con của API qua `map_pipeline_error_code` (mã gốc giữ trong `__cause__`); tensor lệch schema → `MODEL_NOT_READY`, tensor không hữu hạn → `PREDICTION_FAILED`; chỉ trả `tensor`, `tensorMask`, `groupMask`, schema version, `inputStatus`, `qualityHints`, `decodeMs`, `extractMs` — không trả `coords`/`ambiguous` (FR-019) |
| `build_visign_ai_binding()` | Import `visign_ai` lười trong hàm; môi trường API/CI mặc định không tải torch/mediapipe/opencv |
| `src/visign_api/domain/errors.py` | `build_api_exception(code)` trả đúng lớp con (`ClipDecodeFailedException`…) để T050 bắt theo kiểu |
| `src/visign_api/config.py` | `FEATURE_SCHEMA_VERSION`, `FEATURE_SCHEMA_PATH`, `VISIGN_MODEL_DIR` (ghi chú review T022 của P1), mặc định `None` |
| `pyproject.toml`, `uv.lock` | Runtime thêm `numpy>=2.5` (lock 2.5.4, khớp pin của `ai`); extra `serving = ["visign-ai"]` với `[tool.uv.sources]` path `../../ai` editable |
| `tests/unit/test_feature_extraction.py` | 13 test adapter dùng pipeline giả |
| `tests/integration/test_serving_feature_parity.py` | Parity thật, skip khi thiếu `VISIGN_CP2_REFERENCE_WEBM` hoặc extra `serving` |

- `qualityHints.handsDetectedRatio` = tỉ lệ frame đã lấy mẫu có ít nhất một bàn tay đủ 21 điểm;
  `frameCount` = `decodedFrameCount`. `extractMs` = tổng pipeline trừ decode (gồm khởi tạo detector).
- Không thuộc phạm vi: quy tắc phát `NO_PERSON_DETECTED`/`INSUFFICIENT_LANDMARKS` từ `inputStatus` (T049,
  chờ P3), predictor GRU (cần T033/T036 của P3), registry/rollback, endpoint (T038).

## 3. Pre-commit synchronization

- Đã pull `013cded` (P1 chuyển hạ tầng sang AWS) trước khi sửa; `origin/main...HEAD` = `0 0` lúc `2026-11-07T16:50:27+07:00`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | Test adapter/config/error trước khi có code | Fail | Thiếu `numpy`, module và field; `build_api_exception` chưa có | `PASS` |
| 2 | GREEN | `pytest .../test_feature_extraction.py .../test_config.py .../test_error_catalog.py .../integration -q -W error` | Đạt | 38 passed, 1 skipped (parity không có clip) | `PASS` |
| 3 | Bắt hồi quy | Mất `__cause__`; bỏ kiểm shape; "hai tay" thay "ít nhất một tay"; import `visign_ai` đầu module | Fail | 5 / 1 / 1 / 1 failed; khôi phục giống hệt | `PASS` |
| 4 | Gate giống CI (không extra) | `uv sync --locked`; Ruff; `ruff format --check`; `python -m mypy`; `pytest services/inference-api/tests tests/contract -q -W error` ×3 | Không lỗi; `visign_ai`/torch không có trong env | 145 passed, 1 skipped; mypy 32 files | `PASS` |
| 5 | Parity thật | `uv sync --extra serving`; `VISIGN_CP2_REFERENCE_WEBM=<clip> pytest .../test_serving_feature_parity.py` với clip tổng hợp VP8 và VP9 (320×240, 46 frame, tạo bằng PyAV ngoài repo) | Tensor `atol=1e-6`, mask điểm/nhóm khớp tuyệt đối | VP8: 1 passed; VP9: 1 passed | `PASS` |
| 6 | Đường API chi tiết | bytes → `open_temporary_clip` → `extract` ×2 (VP9) | Tensor `[32,234]` float32, clip tạm bị xóa | 2613 ms rồi 2399 ms; decode 215–222 ms; `INSUFFICIENT_LANDMARKS`; `handsDetectedRatio=0.0`, `frameCount=46`; file tạm đã xóa | `PASS` |
| 7 | Parity clip đại diện có người | Clip camera/MediaRecorder thật | Như #5 | `NOT_RUN` — chưa có clip đại diện trên máy P2; P1/P3 chạy cùng test với `VISIGN_CP2_REFERENCE_WEBM` | `NOT_RUN` |
| 8 | Git hygiene | `git diff --cached --check`; quét file bị cấm | Không lỗi | exit 0; không có video/model/archive/secret trong 11 path staged; clip tổng hợp nằm ngoài repo | `PASS` |

Giới hạn của #5: clip tổng hợp là nhiễu, không có người nên tensor toàn 0; phép thử chứng minh đường nối (bytes,
file tạm, schema, detector, lấy mẫu, transform) khớp offline, chưa chứng minh trên động tác thật.

## 5. Rủi ro và handoff

- Độ trễ đặc trưng ~2,4–2,6 s/clip trên CPU máy P2, chưa gồm GRU/HTTP; gate p95 ≤ 3 s (SC-002) và RAM EC2
  1 GB (ghi chú AWS của P1) cần benchmark ở CP7.
- Cài extra `serving` kéo torch/mediapipe/opencv vào môi trường API; job `api` của CI không cài extra nên
  test parity skip. Image production (T095) phải cài `--extra serving` và tải detector bằng `ai/setup_models.py`.
- Cường: chạy parity với clip đại diện bằng lệnh ở #5; xác nhận quy tắc `NO_PERSON_DETECTED` cho T049.
- Rollback: `git revert` riêng commit này; T026/T024 không phụ thuộc adapter.

**Reviewer result**: `PENDING`
