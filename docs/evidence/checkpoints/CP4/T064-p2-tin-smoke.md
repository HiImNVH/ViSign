# CP4 T064 smoke evidence — luồng dự đoán với clip đại diện và đổi artifact

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T064` — clip đại diện: parity offline ↔ API, nạp artifact, dự đoán, xóa clip tạm, đổi fixture/pilot/full |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P3 Cường` (parity, artifact T036) |
| Candidate commit | `CP4 T064(api): add representative-clip pipeline and artifact swap tests` |
| Commit | `5cec97b5fd59b81fae86729f775f4c3cbedb01b7` — [5cec97b](https://github.com/HiImNVH/ViSign/commit/5cec97b5fd59b81fae86729f775f4c3cbedb01b7); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42392276509) |
| Ngày/giờ | `2026-11-07T23:20+07:00` |
| Status | `PASS` local và CI |

## Phạm vi

| File | Nội dung |
|---|---|
| `tests/integration/test_prediction_pipeline.py` | 4 test theo quickstart Scenario 3: đổi artifact bằng khởi động lại với `MODEL_ARTIFACT_PATH` mới; artifact hỏng → degraded, không lùi về fixture; khởi động lại với đường dẫn cũ là rollback; mỗi lần đều kiểm thư mục tạm riêng của API trống |
| `tests/integration/conftest.py` | Cho test ở gốc repo dùng chung bộ dựng artifact T036 của API |
| `services/inference-api/tests/integration/t036_artifact_builder.py` | Tách bộ dựng artifact pilot/full (CLI T036 thật trên tensor tổng hợp) khỏi test GRU để dùng chung; test GRU không đổi hành vi (18 passed) |

| Test | Cần | Khẳng định |
|---|---|---|
| Đổi fixture ↔ fixture-low-confidence | Không (chạy được trên CI) | Health `ok`, `modelVersion` đổi theo artifact, schema response giữ nguyên, accepted rồi rejected đúng artifact |
| Artifact hỏng rồi rollback | Không | Health `degraded`, model-info và dự đoán 503 `MODEL_NOT_READY` (không lùi về fixture); khởi động lại với fixture → `ok`, 200 |
| Parity clip đại diện | Extra `serving` + `VISIGN_CP2_REFERENCE_WEBM` | Tensor `32×234` khớp offline (atol 1e-6), tensor mask, group mask và `inputStatus` khớp; clip tạm bị xóa |
| Chuỗi fixture → pilot → full → fixture | Extra `serving` + clip | Mỗi bước khởi động lại: `artifactKind` đúng, `demoReady=false`, dự đoán 200 qua pipeline MediaPipe thật (pilot/full train bằng CLI T036), response đúng contract, `modelVersion` khớp model-info; không còn file tạm |

Clip đại diện là một clip có người thật của owner, chuyển sang WebM VP8 đứng thẳng 360×640 trong thư mục tạm của phiên làm
việc, chỉ trỏ tới qua biến môi trường, xóa ngay sau khi chạy; không vào repo. Trọng số GRU tổng hợp chỉ chứng minh cơ chế,
không chứng minh nhận diện VSL.

## Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `28de816` trước khi sửa (đã pull T053 của P5).
- Trước commit: pull review T053/T066/T072/T073 của P1 (`0242745`) và T040 của P5 (không trùng file); gate chạy lại trong venv còn extra `serving`: API + contract + integration 392 passed, 3 skipped (bản đầu ghi nhầm 374/4 là số của môi trường như CI, sửa ở link commit).
- `origin/main...HEAD` = `0 0` tại `72733aa`.

## Smoke

| Gate | Kết quả |
|---|---|
| Không có clip đại diện | 2 passed (phần CI), 2 skipped đúng lý do |
| Có clip đại diện (extra `serving`) | 4/4 T064 passed + test parity của API passed |
| Bắt hồi quy | 4/4 mutation bị bắt: lùi về fixture khi artifact hỏng, bỏ qua đường dẫn artifact khi đổi, không xóa clip tạm, lệch tensor phục vụ 0,001 (trên clip thật) |
| Toàn bộ | Extra `serving`: 392 passed, 3 skipped (cần clip). Như CI: 374 passed, 4 skipped. Ruff, format, mypy 60 files |

Đề xuất P1: thêm `tests/integration` vào lệnh pytest của job `api` trong `quality.yml` để phần không cần torch của T064 và
audit T066 chạy trên CI.

**Reviewer result**: `PENDING`

## Independent review — P1/Huy

Review `2026-11-07T23:47:41+07:00` trên `24a9e21` (theo uỷ quyền của Huy).

| Gate | Kết quả |
|---|---|
| Như CI | API + contract + integration 374 passed, 4 skipped |
| Extra `serving` (P1 tự cài vào venv local) | `tests/integration` + `services/inference-api/tests/integration`: **19 passed**, 4 skipped |
| Skip còn lại | Cần detector MediaPipe tải về và `VISIGN_CP2_REFERENCE_WEBM` (clip có người của owner — P1 không dùng video người khác) |

Đạt: artifact hỏng → `degraded`/503 `MODEL_NOT_READY`, **không lùi về fixture**; khởi động lại với artifact
hợp lệ phục hồi. Chuỗi đổi artifact và parity trên clip thật dựa vào kết quả owner, nhất quán với xác nhận độc
lập của P3 (parity 6/6 `1b14f1e`, 32/32 clip thật trong evidence T037).

**Reviewer result**: `P1_VERIFIED` → T064 `[X]`.
