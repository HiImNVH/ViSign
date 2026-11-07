# CP3 T037 smoke evidence — ánh xạ lỗi pipeline sang API

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP3` (micro-commit đầu của T037) |
| Task | `T037` — phần ánh xạ mã lỗi; predictor/adapter đầy đủ vẫn mở |
| Owner | `P2 Tín` |
| Reviewer | `P3 Cường` (danh sách mã pipeline, kế hoạch T017 mục 3); `P1 Huy` |
| Candidate commit | `CP3 T037(api): map pipeline error codes to stable API codes` |
| Commit | `5b6a441e1e4d5a030ec5fdfde7479d3e252073b0` — [5b6a441](https://github.com/HiImNVH/ViSign/commit/5b6a441e1e4d5a030ec5fdfde7479d3e252073b0); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42353287941) (run riêng đỏ ở job Web do test flaky T039) |
| Ngày/giờ | `2026-11-07T14:46:51+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15 |
| Status | `PASS` local |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh: mọi mã `PipelineError` mà `visign_ai.landmarks` có thể raise đều có ánh xạ
  tường minh sang `ErrorCode` của API, theo kế hoạch T017 mục 3 của P3 và ghi chú review T014–T016:

| Mã pipeline | Mã API | HTTP |
|---|---|---|
| `INVALID_REQUEST`, `UNSUPPORTED_MEDIA_TYPE`, `CLIP_TOO_LARGE`, `CLIP_TOO_SHORT`, `CLIP_TOO_LONG`, `CLIP_DECODE_FAILED`, `NO_PERSON_DETECTED`, `INSUFFICIENT_LANDMARKS` | Giữ nguyên | 400/415/413/422 theo catalog |
| `INVALID_TIMESTAMPS` | `CLIP_DECODE_FAILED` | 422 |
| `FEATURE_SCHEMA_MISMATCH`, `EXTRACTOR_VERSION_MISMATCH`, `MODEL_ASSET_MISMATCH` | `MODEL_NOT_READY` | 503 |
| Mã chưa biết | `PREDICTION_FAILED` | 500, không lộ chi tiết |

- File: `services/inference-api/src/visign_api/inference/{__init__,pipeline_errors}.py`,
  `services/inference-api/tests/unit/test_pipeline_error_mapping.py`.
- Test quét `ai/src/visign_ai/landmarks/*.py` tìm `PipelineError("<CODE>"` nên mã mới của P3 (ví dụ từ CLI
  T017) làm CI fail cho đến khi API có ánh xạ; API env không cần cài `visign_ai`.
- Không thuộc phạm vi: gọi `process_video`, nạp artifact, quy tắc `NO_PERSON_DETECTED` từ report (chờ P3).

## 3. Pre-commit synchronization

- `origin/main...HEAD` = `0 1` (chỉ commit T099 `5add400` chưa push) lúc `2026-11-07T14:46:51+07:00`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `pytest services/inference-api/tests/unit/test_pipeline_error_mapping.py -q` trước khi có module | Fail | 1 collection error | `PASS` |
| 2 | GREEN | Cùng command | Đạt | 15 passed | `PASS` |
| 3 | Bắt thiếu ánh xạ | Tạm xóa dòng `MODEL_ASSET_MISMATCH` | Fail | 2 failed, 13 passed; khôi phục giống hệt | `PASS` |
| 4 | Toàn bộ API + contract | `pytest services/inference-api/tests tests/contract -q -W error`; Ruff; format check; `python -m mypy` | Không lỗi | 103 passed; Ruff/format đạt; mypy 18 files | `PASS` |
| 5 | Git hygiene | `git diff --cached --check`; quét file bị cấm/secret | Không lỗi | exit 0 | `PASS` |

## 5. Rủi ro và handoff

- Quy tắc phát `NO_PERSON_DETECTED`/`INSUFFICIENT_LANDMARKS` từ `report.inputStatus` vẫn chờ P3 chốt.
- CLI T017 của P3 ghi mã gốc; adapter T037 chỉ trả mã đã ánh xạ.
- Rollback: `git revert` riêng commit này.

**Reviewer result**: `PENDING`
