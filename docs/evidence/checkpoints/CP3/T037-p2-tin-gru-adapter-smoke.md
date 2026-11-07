# CP3 T037 smoke evidence — adapter GRU cho artifact pilot/full

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP3 / T037` (lát cuối: adapter GRU pilot/full); xác nhận phía P2 cho bàn giao `T036` |
| Owner | `P2 Tín` |
| Reviewer | `P3 Cường` (định dạng artifact, `labelBinding`, schema đi kèm); `P1 Huy` |
| Candidate commit | `CP3 T037(api): add GRU adapter for pilot and full artifacts` |
| Commit | `64ecf72f5d5049bf40e46b89c49c88c01d463359` — [64ecf72](https://github.com/HiImNVH/ViSign/commit/64ecf72f5d5049bf40e46b89c49c88c01d463359); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42381710523) |
| Ngày/giờ | `2026-11-07T20:40+07:00` |
| Môi trường | Windows 11, uv 0.13.7, CPython 3.12.15; môi trường API mặc định (như CI) và extra `serving` (torch 2.11.0+cpu, MediaPipe 1.1.1) |
| Status | `PASS` local và CI; đã push cùng T049/T045/T050 trong `7315314..3b47521` |

## Phạm vi

| File | Nội dung |
|---|---|
| `inference/gru_bundle.py` | Kiểm gói không cần torch (CI chạy được): schema đi kèm phải `APPROVED`, trùng `featureSchemaVersion`/`extractorVersion` của `model_info.json`; checkpoint đủ `modelConfig`, `stateDict`, `schemaSha256`, `labelBinding`; `schemaSha256` = hash schema đi kèm; `labelBinding` trùng `classLabels` (đúng thứ tự), `meaningMap`, `displayTextMap`; `modelConfig` đúng 4 kích thước nguyên dương (loại `bool`), `input_size = 3 × số landmark`, `num_classes = số classLabels` |
| `inference/gru_predictor.py` | `GruPredictor`: trích đặc trưng bằng pipeline chung → GRU → top-1 theo thứ tự `classLabels` đã train; timings `decode/extract` từ pipeline, `infer` đo quanh GRU; vector xác suất sai số lớp/NaN/ngoài [0,1] → 500 `PREDICTION_FAILED`. `load_gru_predictor`: kiểm extra `serving`, đọc schema đi kèm + kiểm hash detector trên máy phục vụ, `torch.load(..., weights_only=True)`, kiểm gói, `load_state_dict(strict=True)`, `eval()`; mọi lỗi → `ArtifactRejectedError` |
| `inference/predictor_registry.py` | `FIXTURE_PREDICTOR_FACTORIES` (thay `DEFAULT_PREDICTOR_FACTORIES`); `build_predictor_factories(GruRuntime)` đăng ký fixture + GRU cho pilot/full; torch chỉ được import khi kích hoạt artifact thật |
| `main.py` | `create_app` dùng `build_predictor_factories` với `VISIGN_MODEL_DIR` từ settings |

Quyết định theo `docs/team/ai-backend-contract.md`:

- **Schema đi kèm artifact**: adapter trích đặc trưng bằng chính `feature_schema.json` của artifact (không dùng schema
  mặc định của máy phục vụ), `expected_schema_version` lấy từ `model_info.json`.
- **Label binding bắt buộc**: checkpoint thiếu `labelBinding` (định dạng cũ) bị từ chối, phải train lại bằng CLI T036;
  không tự gắn binding cho trọng số cũ.
- **Không chạy pickle tùy ý**: `weights_only=True`; test chứng minh payload trong `model.pt` không chạy (và sẽ chạy nếu
  tắt `weights_only`).
- **Fail closed**: máy thiếu extra `serving`, detector khác hash, gói lệch → artifact bị từ chối; khởi động thì
  `degraded`, đổi artifact trong tiến trình thì giữ predictor cũ; không lùi về fixture.

Không thuộc phạm vi: chặn clip thiếu người/landmark (T049, commit kế tiếp); kiểm checksum `FILES-SHA256.json` (CLI T036
chưa xuất manifest); đối chiếu `evaluation-report.json` (chờ định dạng T057–T059); lệnh `check_artifact` và parity trên
clip người thật (T064).

## Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `2f83975` trước khi sửa (đã pull T017/T034–T036 review, T098, spec US6 của P1).
- Trước commit: `git fetch` lần đầu lỗi mạng (`curl 56`), chuỗi lệnh dừng trước khi stage. Fetch lại thấy P5 T041
  (`9430655`) và review T009–T012 (`f1eb7ea`), không chạm file API; stash → `pull --rebase` → apply, hash nội dung
  9 path khớp rồi mới drop stash; gate chạy lại đạt.
- `origin/main...HEAD` = `0 0` tại `f1eb7ea`.
- Trước push: rebase thêm hai lần khi remote có review T019/T037 của P3 (`989533e`, `1b14f1e`) và review endpoint
  của P1 (`7315314`), không trùng file; SHA cuối `64ecf72`; pre-push `0 4` trên `7315314`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 4 collection errors (module chưa có, hằng factory đổi tên) |
| GREEN | 57 passed: 24 unit `gru_bundle`, 12 unit `gru_predictor`, 8 registry, 13 tích hợp |
| Tích hợp với CLI T036 thật | Artifact train bằng `visign_ai.training.train.main` trên tensor tổng hợp, nạp qua registry mặc định: `GruPredictor`, pilot, `classLabels` giữ thứ tự class map (`SOT_HCM_1`, `CAM_ON_HN_1`), `demoReady=false`; health `ok`, model-info đúng; xác suất adapter = `GRUClassifier` + `collate_sequences` lúc train (atol 1e-6) |
| Gói bị sửa | Lý do từ chối đúng từng ca: đảo `classLabels` → `labelBinding.classLabels`; đổi chữ hiển thị → `labelBinding.displayTextMap`; sửa schema → hash schema; schema DRAFT → chưa `APPROVED`; cắt `model.pt` → `RuntimeError`; thiếu `model.pt`/schema → `FileNotFoundError`; pickle độc → `UnpicklingError`, không tạo file đánh dấu. Mọi ca giữ predictor đang chạy |
| `VISIGN_MODEL_DIR` sai | Thư mục không có detector → health `degraded`, không phục vụ pilot |
| Bắt hồi quy | 11/11 mutation bị bắt: bỏ kiểm `APPROVED`, bỏ so hash, bỏ so thứ tự lớp, cho `bool` làm kích thước, `argmin`, bỏ kiểm shape xác suất, `weights_only=False`, độ dài chuỗi lệch 1, bỏ đăng ký full, bỏ `VISIGN_MODEL_DIR`, bỏ kiểm extra (test được siết để khớp đúng lý do) |
| Toàn bộ API + contract | Extra `serving`: 260 passed, 1 skipped (parity cần clip tham chiếu). Môi trường như CI (không torch): 247 passed, 2 skipped (module tích hợp GRU tự skip). Ruff, format, mypy 48 files |
| Live uvicorn | `MODEL_ARTIFACT_PATH` = artifact pilot train ở trên: sẵn sàng sau 4,3 s; health `ok`, `cache-control: no-store`; model-info pilot, ngưỡng 0,5 (chọn từ validation), `demoReady=false`; POST clip VP8 tổng hợp 2 lần: 200, `decode` 27–43 ms, `extract` 2,8–3,7 s, `infer` 3–5 ms, `requestId` khớp header; log JSON chỉ có field allowlist; 0 file `visign_clip_*` còn lại |

## Phát hiện

- Clip tổng hợp **không có người** (`handsDetectedRatio` 0,0) vẫn được GRU trả "Cảm ơn" `accepted=true` (0,66 ≥ 0,5).
  T049 phải chặn `INSUFFICIENT_LANDMARKS` trước khi gọi GRU, giống CLI T017. Không push commit này riêng lẻ.
- GRU chỉ tốn 3–5 ms; độ trễ nằm ở trích đặc trưng MediaPipe (2,8–3,7 s), khớp benchmark T095. Rủi ro SC-002 vẫn ở P3.

## Handoff

- Cường: artifact của CLI T036 nạp đúng qua registry T037 (`model_info.json`, `labelBinding`, schema đi kèm). Giữ
  nguyên khóa checkpoint và tên file; đổi định dạng thì báo P2 vì adapter từ chối gói lệch.
- Huy: CI job API không cài extra `serving` nên 13 test tích hợp GRU chỉ chạy local. Đề xuất (không tự sửa
  `quality.yml`): thêm bước `uv sync --locked --project services/inference-api --extra serving` + pytest tích hợp.
- Hiển: không đổi contract API; pilot/full trả cùng schema response với fixture.

## Bổ sung sau review P3 — dự đoán GRU qua HTTP

Review P3 (`1b14f1e`) ghi "chưa kiểm thử dự đoán GRU qua HTTP" và "Tín cần áp dụng, test quy tắc T049 ở API".
Commit `CP3 T037(api): test GRU predictions over HTTP for pilot and full` chỉ thêm test, không đổi code phục vụ.

| Gate | Kết quả |
|---|---|
| Commit | `PENDING` |
| Artifact full | CLI T036 train 10 nghĩa P0 (`--p0-meanings`), nạp qua registry mặc định; GRU ra 10 xác suất (tổng 1); `demoReady=false` vì metric còn null |
| `POST /api/v1/predictions` qua GRU đã train | Chỉ thay MediaPipe bằng đặc trưng xác định; HTTP, kiểm clip, slot, clip tạm, GRU và luật quyết định chạy thật. Pilot: 200 "Cảm ơn" `accepted` (0,562 ≥ 0,5). Full: 200 "Không nhận diện được" (0,169 < 0,5). Khớp phép tính độc lập từ trọng số và metadata; adapter dùng schema đi kèm artifact; clip tạm bị xóa |
| Quy tắc P3 qua HTTP | Không có điểm hợp lệ → 422 `NO_PERSON_DETECTED`; có điểm nhưng không có bước tensor đủ vai + tay → 422 `INSUFFICIENT_LANDMARKS` |
| Bắt hồi quy | 5/5 mutation bị bắt: `argmin`, dùng schema mặc định thay schema artifact, quy tắc mask cũ, bỏ cổng người/landmark, bỏ đăng ký full |
| Toàn bộ API + contract | Extra `serving`: 350 passed, 1 skipped. Môi trường như CI: 332 passed, 2 skipped (module tích hợp GRU tự skip). Ruff, format, mypy 54 files |

Còn thiếu: parity và dự đoán qua HTTP trên clip có người thật, cần một clip review từ P3.

**Reviewer result**: `PENDING`
