# CP2 T019–T021 smoke evidence — API domain models

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP2` |
| Task | `T019-T021` |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P3 Cường` review metadata artifact (T019); `P5 Hiển` review response/error shape |
| Candidate commit | `CP2 T019-T021(api): add model metadata, prediction and error domain` |
| Commit | `9b888a182592a2739b665a287ec37a8a4aa9f8f3` — [9b888a1](https://github.com/HiImNVH/ViSign/commit/9b888a182592a2739b665a287ec37a8a4aa9f8f3) |
| Ngày/giờ | `2026-11-07T14:05:00+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15, pydantic 2 |
| Status | `PASS` local; remote verification pending |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh:
  - T019: `ModelMetadata` cho `fixture|pilot|full`, metric nullable, `demoReady` chỉ `True` khi artifact
    khai `True` **và** đạt gate `full && 10 meanings && macroF1 >= 0.80 && mọi perMeaningRecall >= 0.65`.
  - T020: `PredictionResponse` không cho phép accepted thiếu text/classLabel hoặc rejected có
    classLabel; `timingsMs`/`qualityHints` optional, bị bỏ khỏi JSON khi vắng và cấm field lạ
    (chặn landmark/frame).
  - T021: `ErrorCode` khớp đúng thứ tự enum `ErrorEnvelope.code` trong `openapi.yaml`; catalog
    status/message/Retry-After tập trung tại một chỗ.
- File/module chính: `services/inference-api/src/visign_api/domain/`
  (`model_version.py`, `prediction.py`, `errors.py`, `request_id.py`), 3 file unit test, dev dependency
  `pyyaml` + `types-pyyaml` trong `services/inference-api/pyproject.toml`/`uv.lock`.
- Không thuộc phạm vi: `ROUTE_NOT_FOUND`/`METHOD_NOT_ALLOWED` (T073), config/logging (T022–T023),
  FastAPI app (T026), sửa `openapi.yaml` (T099).
- Nguồn tham khảo: legacy `HiImNVH/7nghiep367` nhánh `backend` commit `b708c72`. Khác legacy:
  - `demoReady` không còn tự nâng lên `True` khi đạt gate; artifact phải khai `True` (fail closed).
  - Ngưỡng gate và Retry-After thành hằng số có tên; exception lấy status/message từ `ERROR_CATALOG`
    và chỉ nhận một tham số `code` (core §6.1).
  - Diagnostics dùng `extra="forbid"`; tách `ensure_uuid` sang `request_id.py` để tránh phụ thuộc chéo.
- Dependency/contract/version: release `0.0.1`, API `v1`, `contracts/openapi.yaml` chỉ được đọc.

## 3. Pre-commit synchronization

- `git fetch origin main`; `git rev-list --left-right --count origin/main...HEAD`: `0 0` tại
  `18a07aef641b424ddf4772249623b1bc04a4b926`.
- Pre-push: `git pull --rebase origin main` không có commit mới (`0 1`); push `18a07ae..9b888a1`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `uv run --project services/inference-api pytest services/inference-api/tests -q` trước khi có domain | Test mới fail | 3 collection errors (module chưa tồn tại), exit 2 | `PASS` |
| 2 | Unit GREEN | Cùng command sau khi cài domain | Toàn bộ đạt | 44 passed, exit 0 | `PASS` |
| 3 | Lint | `uv run --project services/inference-api ruff check services/inference-api` | Không lỗi | All checks passed, exit 0 | `PASS` |
| 4 | Type | `uv run --project services/inference-api python -m mypy services/inference-api/src services/inference-api/tests` | Không lỗi | 10 source files no issues, exit 0 | `PASS` |
| 5 | Contract drift | `test_error_codes_match_openapi_enum_in_order` đọc `openapi.yaml` | Enum khớp thứ tự | Đạt trong bước 2 | `PASS` |
| 6 | Runtime HTTP | — | — | `NOT_RUN`: chưa có FastAPI app/endpoint (T026) | `NOT_RUN` |
| 7 | Git hygiene | `git diff --cached --check`; quét file bị cấm | Không lỗi | exit 0; không có file bị cấm/secret trong 12 path staged | `PASS` |

## 5. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/9b888a182592a2739b665a287ec37a8a4aa9f8f3` | Pushed 2026-11-07T14:05:47+07:00 |
| GitHub Actions | `NOT_RUN` — workflow thuộc T091/CP7 | Local gate |
| API/cloud | `NOT_RUN` — chưa có endpoint | `/api/v1/health` thuộc T026/T060 |
| Data/model | `NOT_RUN` | Không có artifact trong candidate |

## 6. Rủi ro, rollback và handoff

- Rủi ro còn lại:
  - Cường cần xác nhận `release_gate`/metadata writer (T059) ghi `demoReady=true` cho full model đạt
    gate, vì API không còn tự suy ra từ metric.
  - Ruff không biết `visign_api` là first-party nên gộp import vào nhóm third-party; muốn tách nhóm
    cần thêm `known-first-party` vào `pyproject.toml` gốc (file dùng chung, chưa sửa).
  - Field Python dùng camelCase để khớp JSON contract; chưa có T1 Python quy định khác.
- Rollback: `git revert` riêng commit này; không có module khác phụ thuộc.
- Việc người kế tiếp cần làm: Huy/Cường/Hiển review; Tín tiếp tục T022–T023.
- Blocker: không có.

## 7. Xác nhận

- [x] Owner đã chạy lại gate sau lần đồng bộ cuối.
- [x] Không có secret, raw video, landmark bulk hoặc model binary bị stage.
- [x] Full SHA và link đã được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

## 8. Independent integration review — P1/Huy

Review time: `2026-11-07T14:09:05+07:00` trên `origin/main` `a36c4cd` (chứa `9b888a1` + evidence `5dc97a6`); worktree sạch.

| Gate | Kết quả độc lập |
|---|---|
| Env | `uv sync --locked --project services/inference-api`: PASS |
| Unit | `pytest services/inference-api/tests -q`: 44 passed |
| Lint | `ruff check services/inference-api`: All checks passed |
| Type | `python -m mypy src tests`: no issues in 10 source files |
| Contract | `ErrorCode` khớp thứ tự enum OpenAPI (drift test); status 400/413/415/422/500/503 khớp `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`; danh sách mã khớp `docs/team/ai-backend-contract.md` |
| Spec T019 | Gate `full && 10 meanings && macroF1 >= 0.80 && mọi perMeaningRecall >= 0.65`; metric nullable; `demoReady` fail closed |
| Spec T020 | accepted cần text + classLabel; rejected cấm classLabel; diagnostics `extra="forbid"`, bị bỏ khi vắng |

Ghi chú không chặn:

- `ruff format --check` báo 6 file cần reformat (chỉ wrap dòng > 88; root config không bật `E501`).
  Format chưa phải gate CP1/CP2; Tín nên chạy `ruff format` trong micro-commit kế tiếp, T092 quyết
  định có đưa format check vào CI hay không.
- `CLIP_DECODE_FAILED` trả 422 trong khi mô tả 422 của OpenAPI là "clip is readable but…"; P5 xác
  nhận placeholder frontend xử lý được, nếu cần đổi mô tả thì đưa vào T099.
- `ModelMetadata` chưa kiểm tra nhất quán `classLabels`/`meaningMap` với `meanings`; nên bổ sung khi
  model loader (CP3) đọc artifact thật.
- Rủi ro T059 (`demoReady=true` do metadata writer ghi) vẫn chờ P3 xác nhận.

**Reviewer result**: `P1_VERIFIED`; `P3` (metadata T019) và `P5` (response/error shape) còn `PENDING`.

**Reviewer note**: Không cần sửa trước specialized review.

## Follow-up sau review P5 — T020 (`2026-11-07T19:05+07:00`)

| # | Ghi chú P5 | Xử lý |
|---|---|---|
| T020 | `accepted=false`, `classLabel=null`, `text="unexpected"` vẫn hợp lệ, trái quy ước API mục 4 | Thêm hằng `REJECTED_PREDICTION_TEXT = "Không nhận diện được"` và `ensure_rejected_state()`: response bị từ chối phải có `classLabel = null` **và** đúng chữ này |

- Test viết trước: thêm 2 trường hợp không hợp lệ (`"unexpected"`, `"Xin chào"` khi bị từ chối) và test hằng khớp quy ước →
  RED (import lỗi); sau khi sửa 18 passed.
- Bắt hồi quy: bỏ kiểm chữ → 2 failed; khôi phục giống hệt.
- Toàn bộ API + contract `-W error`: 176 passed, 1 skipped; Ruff, `ruff format --check`, mypy đạt.
- Ảnh hưởng: chỉ siết validation domain; OpenAPI/TS không đổi (OpenAPI không có `const` cho `text`).

## Task closure — P1/Huy (2026-11-07)

- **T021**: `VERIFIED` (P1 + P5 tại `docs/evidence/checkpoints/CP2/T020-T021-T022-T026-p5-hien-review.md`), `[X]`.
- **T019**: mở — chờ P3 xác nhận metadata và việc metadata writer T059 ghi `demoReady`.
- **T020**: mở — P5 `CHANGES_REQUESTED`: `accepted=false` phải dùng đúng `Không nhận diện được`; `classLabel` không được rỗng/khoảng trắng.

## Follow-up sau closure P1 — T020 `classLabel` khoảng trắng (`2026-11-07T19:30+07:00`)

- Ghi chú closure P1: `classLabel` của kết quả được chấp nhận không được rỗng **hoặc chỉ gồm khoảng trắng**. Bản sửa
  `6ee9e61` đã chặn chuỗi rỗng và chữ sai khi bị từ chối; nay `ensure_accepted_state()` chặn thêm `"   "`.
- Test viết trước: thêm `{"classLabel": "   "}` → 1 failed; sau khi sửa 19 passed.
- Toàn bộ API + contract `-W error`: 179 passed, 1 skipped; Ruff, mypy đạt.
- T020 chờ P5 kiểm lại cả hai điểm (`6ee9e61` và commit này).
- Follow-up đã push: [`542e33f`](https://github.com/HiImNVH/ViSign/commit/542e33f9061a9b9a8374b8c4cabf378805f7a320); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42371289103).
- Follow-up T020 lần 1 đã push: [`6ee9e61`](https://github.com/HiImNVH/ViSign/commit/6ee9e613e5fcafa5ed2fdcbc83aaf863d110d00d); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42370782722).
