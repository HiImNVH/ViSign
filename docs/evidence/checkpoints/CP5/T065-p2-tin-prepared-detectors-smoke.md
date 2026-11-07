# CP5 T065 evidence (phần API của P2) — bộ detector tạo sẵn ở thread nền

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP5 / T065` — tích hợp `prepare_detectors` của P3 (`592db9c`) vào API: tạo và đóng detector ngoài đường găng của request (SC-002) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P3 Cường` (hợp đồng bộ detector dùng một lần) |
| Candidate commit | `CP5 T065(api): prewarm single-use detector sets off the request path` |
| Commit | `a214a3c80d354ddcacaa1f4ed223bcf34ed0ec4b` — [a214a3c](https://github.com/HiImNVH/ViSign/commit/a214a3c80d354ddcacaa1f4ed223bcf34ed0ec4b); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42406197930) |
| Ngày/giờ | `2026-11-08T02:25+07:00` |
| Status | `PASS` local và CI |

## Phạm vi

| File | Nội dung |
|---|---|
| `inference/detector_pool.py` (mới) | Giữ tối đa một bộ detector đã tạo trên một thread nền `visign-detectors`; mỗi request lấy một bộ (dùng một lần), sau request thì tạo bộ kế tiếp trước rồi đóng bộ vừa dùng, đều ở thread nền |
| `inference/feature_extraction.py` | `FeatureExtractor` nhận pool tùy chọn, truyền `prepared_detectors` vào `process_video`; `open_visign_ai_detectors` tạo bộ theo đúng `feature_schema.json` của artifact và thư mục detector |
| `inference/gru_predictor.py` | `GruRuntime.prewarmDetectors` (từ Settings); pool chỉ được tạo sau khi artifact qua mọi bước kiểm; `GruPredictor.close()` |
| `inference/predictor.py`, `predictor_registry.py`, `main.py` | Đổi artifact thì đóng tài nguyên nền của predictor cũ (candidate lỗi giữ predictor đang chạy); tắt app thì lifespan đóng bộ dự phòng |
| `config.py` | `DETECTOR_PREWARM_ENABLED` (mặc định `true`); đặt `false` để quay về tạo detector theo từng clip mà không đổi code |

Chính sách chờ: request chờ bộ đang tạo tối đa 2 s tính từ lúc bắt đầu tạo. Bộ quá hạn (có thể treo) thì request tự tạo
detector như trước và không chờ lại bộ đó; tạo bộ lỗi thì ghi cảnh báo, request tự tạo, bộ mới được tạo sau request.

## Pre-commit synchronization

- Bắt đầu trên `34e63ee`; trước commit pull 4 commit web/tài liệu của P5 (`a40c68a`…`e5d1f26`), không trùng file, digest 15 path khớp; unit test chạy lại 284 passed. `origin/main...HEAD` = `0 0` tại `e5d1f26`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | (1) 8 test pool lỗi import vì chưa có `detector_pool`. (2) 7 failed: extractor chưa truyền bộ, chưa có cờ Settings, `close()` của predictor/registry, lifespan chưa đóng. (3) 1 failed: candidate bị từ chối vẫn khởi động pool; đã chuyển việc tạo pool xuống sau `build_network` |
| GREEN | Unit: 8 pool + 1 extractor + 3 GRU + 4 registry/lifespan; integration: 3 (bộ thật cho schema artifact, candidate bị từ chối không có thread nền, parity) |
| Bắt hồi quy | 14/14 mutation. Lần đầu 12/14: bộ detector giả dạng generator được GC tự đóng nên test không thấy pool bỏ quên bộ dự phòng; đã đổi sang context dạng class chỉ ghi khi `__exit__` được gọi |
| Clip người thật | API + contract + integration + security có `VISIGN_CP2_REFERENCE_WEBM`: 439 passed, 0 skipped (parity bộ tạo sẵn ↔ tạo theo clip; T064/T037 HTTP chạy qua pool) |
| Như CI (`uv sync --locked`, không `serving`) | Ruff; format 66 file; mypy 61 file; API + contract 371 passed, 3 skipped; security + integration 44 passed, 2 skipped |

## A/B độ trễ qua uvicorn thật

Hai server cùng code và artifact `pilot-gru-test-v1`, một tắt và một bật `DETECTOR_PREWARM_ENABLED`; 38 clip người thật
× 2 vòng, đảo thứ tự từng clip; Windows CPU 8 lõi.

| Chỉ số | Tắt prewarm | Bật prewarm |
|---|---:|---:|
| Đầu ra | 76/76 cặp cùng mã, nhãn, `accepted`; confidence lệch 0 | |
| Processing p50 / p95 (ms) | 3.072 / 3.295 | 2.987 / 3.259 |
| Extract p50 / p95 (ms) | 2.861 / 3.072 | 2.589 / 2.810 |
| Request có khoảng nghỉ (32 cặp, request trước thuộc server kia) | | Processing trung vị giảm 194 ms |
| Request nối tiếp ngay request trước của cùng server (32 cặp) | | Trung vị giảm 0,5 ms |
| Đợt 10 request liên tục, processing p50 / max (ms) | 3.017 / 3.298 | 3.062 / 3.465 |
| RAM đỉnh tiến trình (MiB) | 572 | 729 |

Kết luận: khi người dùng có khoảng nghỉ giữa hai lần gửi (quay clip mới), bộ tạo sẵn bỏ được khoảng 250 ms trích đặc
trưng, tức khoảng 194 ms mỗi request. Khi request đến dồn liên tục, request sau phải chờ bộ đang tạo và tranh CPU với
việc đóng bộ cũ nên không có lợi. Chi phí là thêm khoảng 157 MiB RAM cho bộ dự phòng. SC-002 vẫn chưa đạt trên máy
này (p95 3,26 s); cần đo trên host production (T095).

## Rủi ro và việc tiếp theo

- Dưới tải (nhiều người dùng) prewarm không giúp; nếu cần, cân nhắc giữ hai bộ dự phòng (thêm khoảng 150 MiB nữa).
- T095: tính thêm khoảng 160 MiB RAM cho API khi chọn instance; giới hạn 1.536 MiB trong Compose vẫn đủ.

**Reviewer result**: `PENDING`
