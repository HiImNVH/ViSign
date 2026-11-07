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
