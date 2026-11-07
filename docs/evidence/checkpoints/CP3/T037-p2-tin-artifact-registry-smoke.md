# CP3 T030/T037 smoke evidence — nạp artifact, fixture predictor và registry

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP3` (lát thứ ba của T037; phần fixture artifact của T030) — module thuần, chưa gắn app/endpoint |
| Task | `T037` (loader, interface predictor, registry fail closed); `T030` (fixture artifact) — contract test HTTP của T030 chờ T038 |
| Owner | `P2 Tín` |
| Reviewer | `P3 Cường` (định dạng `model_info.json`, thứ tự lớp); `P1 Huy` |
| Candidate commit | `CP3 T030,T037(api): add artifact loader, fixture predictor and registry` |
| Commit | `PENDING` — bổ sung full SHA/link sau push |
| Ngày/giờ | `2026-11-07T17:20+07:00` |
| Môi trường | Windows 11, uv 0.13.7, CPython 3.12.15 (môi trường API mặc định, không extra) |
| Status | `PASS` local |

## 2. Phạm vi thay đổi

| File | Nội dung |
|---|---|
| `inference/artifact_loader.py` | `load_artifact(dir, expected_schema_version)` đọc `model_info.json` → `ModelMetadata` (giữ nguyên thứ tự `classLabels`); từ chối bằng `ArtifactRejectedError` khi: thiếu/hỏng file, sai schema `ModelMetadata`, `featureSchemaVersion` khác schema phục vụ, `meanings`/`classLabels` trùng hoặc rỗng, khóa `meaningMap` ≠ `classLabels`, giá trị `meaningMap` ≠ `meanings` (ghi chú review T019 của P1), thiếu chữ hiển thị, pilot > 3 nghĩa, full ≠ 10 nghĩa, `fixtureResponse` trên artifact không phải fixture hoặc label/confidence không hợp lệ |
| `inference/predictor.py` | `Predictor` (Protocol: `metadata`, `predict(clip_path) -> RawPrediction`); `FixturePredictor` trả lớp đầu tiên hoặc `fixtureResponse`, confidence mặc định 0,95, timings/hints là giá trị cố định khai báo rõ (không phải số đo) |
| `inference/predictor_registry.py` | `activate()` chỉ thay predictor sau khi candidate nạp xong; lỗi ở bất kỳ bước nào giữ nguyên predictor đang chạy (rollback trong tiến trình); chưa có predictor → `MODEL_NOT_READY`; pilot/full chưa có factory → từ chối, **không lùi về fixture** (contract AI–BE) |
| `tests/fixtures/model-artifacts/{fixture,fixture-low-confidence}/model_info.json` | Fixture dùng nghĩa P0 hiện hành (`CAM_ON`, `SOT`, `GIAY_TO`; nhãn `CAM_ON_HN_1`, `SOT_HCM_1`, `GIAY_TO_HCM_1` theo `data-convention.md`); bản low-confidence trả `SOT_HCM_1` với 0,42; `demoReady=false` |

- Khác legacy `backend` `b708c72`: tách loader/predictor/registry; `activate()` không vừa đổi trạng thái vừa
  trả predictor (CQS); không còn biến global `predictor_registry`/`settings`; lý do từ chối chỉ nằm trong
  exception nội bộ, client chỉ nhận `MODEL_NOT_READY`; fixture legacy dùng `XIN_CHAO`/`TAM_BIET` không còn trong P0.
- Không thuộc phạm vi: gắn registry vào lifespan/health (T060) và endpoint (T038); predictor GRU (chờ T033/T036
  của P3); kiểm regex `classLabel` theo `data-convention.md` (chờ T098 đóng băng); checksum `FILES-SHA256.json`.

## 3. Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `76cdb0d` trước khi sửa.
- Trước commit: P3 push T017 (`4a5aa52`, `bc642c1`), không chạm file candidate; stash/pull/apply, so nội dung không lệch;
  gate chạy lại: 173 passed + 1 skipped, test quét mã lỗi pipeline 15 passed (lỗi CLI dùng `BatchSampleError` riêng).
- `origin/main...HEAD` = `0 0` tại `bc642c1`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `pytest .../test_artifact_loader.py .../test_predictor_registry.py -q` trước khi có module | Fail | 2 collection errors | `PASS` |
| 2 | GREEN | Cùng command, `-W error` | Đạt | 28 passed | `PASS` |
| 3 | Bắt hồi quy | Xóa predictor trước khi nạp candidate; bỏ kiểm giá trị `meaningMap`; lùi về `FixturePredictor` khi thiếu factory | Fail | 2 / 1 / 1 failed; khôi phục giống hệt | `PASS` |
| 4 | Toàn bộ API + contract | `pytest services/inference-api/tests tests/contract -q -W error` ×3; Ruff; format check; `python -m mypy` (src, tests, scripts, contract) | Không lỗi | 173 passed, 1 skipped ×3; mypy 38 files | `PASS` |
| 5 | Git hygiene | `git diff --cached --check`; quét file bị cấm | Không lỗi | exit 0; không có file bị cấm/secret trong 9 path staged | `PASS` |

## 5. Rủi ro và handoff

- Cường: xác nhận `model_info.json` của artifact pilot/full có `classLabels`, `meaningMap`, `displayTextMap`
  theo đúng các kiểm tra trên trước khi bàn giao; registry sẽ từ chối artifact thiếu chữ hiển thị.
- Pilot/full hiện luôn bị từ chối (chưa có factory GRU) — đúng fail closed cho tới khi có T033/T036.
- Rollback: `git revert` riêng commit này.

**Reviewer result**: `PENDING`
