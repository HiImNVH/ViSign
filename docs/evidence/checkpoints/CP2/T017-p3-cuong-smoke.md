# CP2 T017 · P3/Cường

| Mục | Kết quả |
|---|---|
| Baseline kiểm thử | `779d4b3794d67a58e013db084eedb39cb2dcf7cc` |
| Trạng thái | PUSHED · bản sửa CI ở local |
| Schema | `visign-xy-32-v0.3-draft` |
| Commit | [4a5aa5295702197d9509302d4bcf07a1dcd0d154](https://github.com/HiImNVH/ViSign/commit/4a5aa5295702197d9509302d4bcf07a1dcd0d154) |

## Chạy thử tại gốc repo

Danh sách CSV thử nghiệm có đúng hai cột `sampleId,rawPath`. `sampleId` là mã nguồn + dấu gạch dưới + 12 ký tự đầu SHA-256 của file. `rawPath` dùng dấu `/` và tính từ dataset root. Chuẩn bị danh sách và video ở ngoài Git.

```powershell
uv run --locked --project ai python -m visign_ai.landmarks.extract_manifest --samples "<DATASET_ROOT>/samples.csv" --dataset-root "<DATASET_ROOT>" > "<DATASET_ROOT>/t017-report.json"
```

Đặt `VISIGN_MODEL_DIR` hoặc dùng `--model-dir` nếu detector nằm ngoài thư mục mặc định. CLI ghi JSON tổng hợp ra stdout, kèm report `process_video` của từng clip đạt. Exit 0 khi toàn bộ đạt, 1 nếu có clip bị từ chối và 2 nếu không đọc được đầu vào batch. Kết quả hợp lệ được ghi từng clip vào `processed/<featureSchemaVersion>/<sampleId>.npz`. CLI từ chối ghi đè. Để chạy lại cùng sample, dùng dataset root thử nghiệm khác hoặc lưu riêng artifact trước đó. Cơ chế công bố file hoàn chỉnh cần hệ thống tệp hỗ trợ hard link, ví dụ NTFS.

NPZ có tensor float32 32×234, timestamp, mask thiếu theo bốn nhóm và theo 78 điểm, tên chuẩn hóa, version và SHA schema. Không sửa video nguồn. Decoder chung hiện resize frame trong RAM nếu cạnh dài vượt 640 px, theo D3 đã thống nhất. Việc đánh giá ảnh hưởng trên clip đại diện vẫn chờ review schema.

CLI giữ mã pipeline gốc trong báo cáo. Ánh xạ HTTP thuộc đường API T037:

| Mã pipeline | Mã API |
|---|---|
| `INVALID_TIMESTAMPS` | `CLIP_DECODE_FAILED` · 422 |
| `FEATURE_SCHEMA_MISMATCH`, `EXTRACTOR_VERSION_MISMATCH` | `MODEL_NOT_READY` · 503 |

## Kiểm thử cục bộ

- Ruff và mypy đạt, pytest AI 20/20 với fixture Chrome/Edge cục bộ.
- Chạy module CLI với MediaPipe thật. Hai clip tham chiếu WebM qua MediaRecorder cho hai NPZ hợp lệ. Kiểm tra shape, kiểu dữ liệu, timestamp, mask và metadata.
- Một WebM hỏng, một path thoát dataset root và một hash sai bị từ chối đúng mã. Chạy lần hai trả `OUTPUT_EXISTS` cho hai NPZ đã có. Byte của cả video nguồn và artifact được giữ nguyên.
- Clip tham chiếu quay từ canvas. Review 5–10 clip camera vật lý, parity offline ↔ API, nhập manifest T010, trích dữ liệu chính thức và train đều chưa chạy trong T017 này.

D1–D4 đã được Quang xác nhận. Danh sách thử nghiệm chỉ dùng ID/path, không định nghĩa schema manifest T010 và không gán nhãn, split hay quyền sử dụng.

## Sửa gate API sau khi push

Gate ánh xạ lỗi quét PipelineError trong thư mục landmark. Bốn mã thao tác file của CLI bị tính vào tập lỗi API. Bản sửa dùng BatchSampleError riêng ở CLI, giữ nguyên JSON/mã lỗi batch và catalog API.

Tái lập trước sửa · 1 fail, 14 pass ở test ánh xạ. Sau sửa · API và contract 145 pass, 1 skip. AI 20 pass, smoke CLI đạt. Ruff và mypy của API/AI đều đạt. GitHub Actions cho bản sửa chờ commit và push.

## Independent review — P2/Tín

Review time: `2026-11-07T17:45+07:00` trên `origin/main` `7adc7e5` (chứa `4a5aa52`, `bc642c1`); Windows 11,
`uv run --project ai --locked`, detector đúng SHA-256 tại `ai/models`.

| Gate | Kết quả độc lập |
|---|---|
| CI | `4a5aa52`: [run 42363066732](https://github.com/HiImNVH/ViSign/actions/runs/42363066732) `failure` (test ánh xạ lỗi T037 quét `PipelineError` mới); `bc642c1`: [run 42364019259](https://github.com/HiImNVH/ViSign/actions/runs/42364019259) `success` |
| AI tests | `pytest ai/tests -q -rs`: 15 passed, 5 skipped — **không có test nào cho `extract_manifest.py`** |
| API + contract | 173 passed, 1 skipped; test quét mã lỗi 15 passed (lỗi CLI tách sang `BatchSampleError`) |
| CLI smoke | Dataset thử ngoài repo, 4 dòng: clip không có người → `INSUFFICIENT_LANDMARKS`; `../outside.webm` → `INVALID_RAW_PATH`; hash sai → `SAMPLE_HASH_MISMATCH`; file thiếu → `SOURCE_NOT_FOUND`; exit 1; không có NPZ nào được ghi |
| Quy ước | Regex `sampleId` khớp `docs/team/data-convention.md`; MP4 chỉ bật ở CLI offline (`allow_mp4=True`), API giữ WebM |
| Accepted path | `NOT_RUN` bởi P2 — không có clip có người; P3 đã chạy với 2 clip tham chiếu |

Phát hiện:

1. `CHANGES_REQUESTED` — **chưa có test tự động cho T017**. Hiến pháp yêu cầu thay đổi pipeline dữ liệu có
   kiểm thử; hiện các bảo vệ quan trọng chỉ được kiểm bằng tay. Đề xuất `ai/tests/landmarks/test_extract_manifest.py`
   với `process_video` giả (monkeypatch) cho: header/cột/`sampleId` sai hoặc trùng, `rawPath` tuyệt đối/`..`/`\`/`:`/
   symlink thoát root, hash sai, file thiếu, `OUTPUT_EXISTS` không ghi đè, `inputStatus` thiếu → `INSUFFICIENT_LANDMARKS`,
   nội dung NPZ (shape, dtype, mask đảo), exit code 0/1/2.
2. Ghi chú quy trình: commit `4a5aa52` làm đỏ job API vì test T037 quét `ai/src/visign_ai/landmarks`. Khi sửa
   `landmarks/`, chạy cả `uv run --project services/inference-api pytest services/inference-api/tests tests/contract`
   trước khi push.
3. Ranh giới API (T049): CLI coi mọi `inputStatus != HAS_USABLE_FRAMES` là `INSUFFICIENT_LANDMARKS`. API sẽ dùng
   cùng quy tắc để train và serve nhất quán; `NO_PERSON_DETECTED` không được phát ra trong MVP trừ khi P3 định nghĩa
   quy tắc riêng — đề nghị P3 xác nhận.
4. `LOW` Lỗi ngoài `PipelineError`/`BatchSampleError`/`OSError` (ví dụ `RuntimeError` của MediaPipe) làm hỏng cả
   batch và Python thoát với mã 1, trùng nghĩa "có clip bị từ chối". Nên bắt riêng hoặc dùng mã thoát khác.
5. `LOW` Theo `.agent/core.md`: `extract_sample` nhận 5 tham số, `run_batch` 3 tham số (giới hạn 2); docstring
   có dấu (comment nên không dấu). Evidence còn ghi "bản sửa CI ở local" dù `bc642c1` đã push.

**Reviewer result**: `CHANGES_REQUESTED` (P2) — chỉ mục 1; hành vi CLI đúng qua smoke. P1 còn `PENDING`.
