# CP5 T065 · P3/Cường

P3/Cường đo local trên baseline cedd013. Review P1/Huy và P2/Tín. [Báo cáo và lệnh chạy](../../../performance-report.md)

| Gate | Kết quả |
|---|---|
| Ruff và mypy AI | PASS, mypy kiểm 27 file |
| Pytest AI | 79 passed, 1 skipped do quyền symlink trên Windows |
| CLI benchmark HTTP thật | 18/18 request hợp lệ trả 200. Tách decode/extract/infer, tổng, throughput, CPU/RAM |
| Kiểm lại CLI bản cuối | 1 clip hợp lệ có report. Input sai trả 415, CLI exit 2 và không tạo báo cáo |
| Edge local qua API thật | 6/6 HTTP 200 sau đồng bộ frontend 05d906f. p95 từ bấm gửi đến thấy kết quả 6,42 s. Trước đồng bộ 8,10 s |
| Production | Chờ URL deploy và đo tài nguyên worker trên host |

Local chưa đạt SC-002. Kết quả API p95 5,71 s ở client HTTP, phần trích landmark p95 5,26 s. Artifact pilot dùng trọng số tổng hợp. Evidence này phục vụ tối ưu hiệu năng và chưa đóng T065.

**Reviewer result** PENDING

## Independent review — P1/Huy

Review `2026-11-07T22:43:49+07:00` trên `cc9a214` (theo uỷ quyền của Huy). Ruff, mypy (27 file) PASS; `benchmark_inference --help` chạy.

Số đo local nhất quán với evidence P2 (p95 API 4,73 s) và cho thấy nút thắt rõ: **extract MediaPipe p50
4.644 ms / p95 5.265 ms**, GRU p95 4 ms; web p95 6.425 ms → **SC-002 (≤ 3 s) trượt gấp đôi**.

Nguyên nhân có bằng chứng trong code: `ai/src/visign_ai/landmarks/holistic_extractor.py` dòng ~93 vẫn đọc
model và `create_from_options` 3 detector **cho mỗi clip** (đã ghi ở review T014–T016 mục 4), cộng với decode
toàn bộ frame trước khi lấy mẫu (mục 3). Đề xuất P3 đo tách chi phí khởi tạo, thử giữ detector giữa các
request (reset bằng timestamp mới/instance pool) và lấy mẫu trước khi chuyển RGB; mọi thay đổi phải giữ
parity offline ↔ API.

**Reviewer result**: `P1_VERIFIED` phần local. T065 giữ `[ ]` vì task yêu cầu cả **production** (chưa có
URL/host đo) và SC-002 chưa đạt.

## Candidate khởi tạo detector song song

Baseline đo `cfa9f04`. Dùng cùng 6 clip review, detector đã kiểm SHA-256, cùng
schema và cùng lịch lấy mẫu. Số đo và cách đối chứng ở [báo cáo T065](../../../performance-report.md#thử-tối-ưu-khởi-tạo-detector).
Chạy lại Ruff, mypy, pytest AI/API và T064 trên `5cec97b` sau khi đồng bộ các
commit CP2/CP4 mới. Phần mã AI dùng cho phép đo giống nhau giữa hai mốc.

| Kiểm tra local | Kết quả |
|---|---|
| `ruff check ai` và `python -m mypy ai/src ai/tests` | PASS, mypy kiểm 27 file |
| `pytest ai/tests -q -rs` | 79 pass, 1 skip do Windows thiếu quyền tạo symlink. Có cấp 4 clip VP8/VP9 Chrome/Edge và clip WebM tham chiếu |
| `pytest services/inference-api/tests tests/contract -q -rs` | 374 pass trên `5cec97b`, có cấp `VISIGN_CP2_REFERENCE_WEBM` cho parity. Dùng metadata wheel API 0.0.1 dựng từ mã repo |
| `pytest tests/integration/test_prediction_pipeline.py -q -rs` (T064) | 4 pass trên `5cec97b`, gồm parity clip thật, đổi artifact fixture/pilot/full và cleanup |
| Candidate ↔ baseline trên WebM thật | 12/12 tensor đạt `atol=1e-6, rtol=0`; `point_valid`, `masks` và `tensor_mask` khớp tuyệt đối |
| Uvicorn loopback + artifact T036 tổng hợp | 6/6 HTTP 200 và request ID khớp. Payload sai trả 415. Hai WebM trống đen/trắng trả 422 `NO_PERSON_DETECTED`. Đây là smoke T049, chưa có số đo false accept của model VSL cho T089 |
| Edge web trên candidate ở `c875ae5` | 6/6 HTTP 200, web p95 5,87 giây. SC-002 chưa đạt |
| Production | Chưa có URL/worker production để đo |

Candidate chờ P1/P2 review. T065 giữ mở.

## Independent review — P1/Huy (cập nhật sau `fd2656f`)

Review `2026-11-08T00:37:34+07:00` trên `dc9e357` (P1 review theo uỷ quyền của Huy). AI 79 passed, 5 skipped; Ruff, mypy (29 file) PASS — đổi extractor không làm vỡ test parity/pipeline.

Detector giờ khởi tạo song song trên worker riêng, p95 giảm ~13%, nhưng **vẫn tạo mới mỗi clip**; web p95
5,87 s → SC-002 vẫn trượt. Bước kế tiếp đề xuất: giữ detector giữa các request (pool theo worker, reset tracking
bằng timestamp mới) và lấy mẫu trước khi chuyển RGB; đo lại kèm parity.

**Reviewer result**: T065 giữ `[ ]` (chưa đạt SC-002, chưa đo production).

## Bàn giao bộ detector dùng một lần cho P2

Baseline đo `231f8d2`. Đã đồng bộ và kiểm lại API trên `dc9e357`. Tín có thể gọi
`prepare_detectors(load_schema(schema_path), model_dir)` ở worker nền, giữ
context sống và truyền bộ trả về qua `prepared_detectors` vào
`process_video(..., schema_path=schema_path, model_dir=model_dir)`. Bên gọi
`extract` trực tiếp có thể dùng cùng tham số. Ví dụ vòng đời một bộ:

```python
with ExitStack() as lease:
    prepared = worker.submit(
        lease.enter_context, prepare_detectors(load_schema(schema_path), model_dir)
    ).result()
    result = process_video(
        clip_path, schema_path=schema_path, model_dir=model_dir,
        prepared_detectors=prepared,
    )
```

API giữ quyền sở hữu context và đóng sau request hoặc khi bỏ bộ chưa dùng,
ví dụ lúc đổi artifact hoặc shutdown. Mỗi bộ chỉ dùng một lần, kể cả khi detector
lỗi giữa chừng. Factory kiểm hash trên chính byte dùng để tạo detector.
Bộ đã chuẩn bị bị từ chối nếu schema hoặc thư mục detector khác. Đường gọi
không truyền bộ sẵn vẫn tạo detector cho từng clip như trước. Phần bộ đệm
nền và chính sách timeout/đổi artifact thuộc API của P2.

| Kiểm tra | Kết quả |
|---|---|
| Ruff, mypy và `pytest ai/tests -q -rs` | Ruff và mypy đạt. 87 pass, 1 skip do quyền symlink, gồm 4 test vòng đời detector |
| `pytest ai/tests/landmarks/test_prepared_detectors.py services/inference-api/tests tests/contract tests/integration tests/security/test_api_security.py -q -rs` | 415 pass trên `dc9e357` với WebM tham chiếu |
| 6 WebM review, detector thật, tạo bộ ở thread nền | 6/6 tensor khớp `atol=1e-6, rtol=0`; mask, timestamp, chỉ số frame và hash schema khớp chính xác |
| Đối chứng 64 frame cục bộ | p95 tiền xử lý xấp xỉ 5,31 giây ở cả hai nhánh. Tạo bộ sẵn mất 478–579 ms ngoài thời gian xử lý đã đo. Chưa có bằng chứng giảm độ trễ trên HTTP/web |
| Thử 48 frame ngoài luồng serving | Mask khớp 93,75–99,12% điểm/bước. Hai clip mất lần lượt 1 và 2 bước tensor dùng được. Chưa có metric nhận diện VSL |

Schema hiện tại giữ tối đa 64 frame. Phương án 48 cần schema version mới, trích
lại và train/evaluate trên dữ liệu đã audit trước khi chọn cho serving.

## Independent review — P2/Tín

Review `2026-11-08T00:45+07:00` trên `dc9e357` (extractor `fd2656f`; bộ detector chuẩn bị sẵn `592db9c` đến
sau, không nằm trong phép đo này). Từ `c875ae5` đến `dc9e357`, đường trích đặc trưng chỉ khác
`holistic_extractor.py`, nên A/B dưới đây thay đúng hàm `extract` của `c875ae5` vào một server.

| Kiểm tra | Kết quả |
|---|---|
| Ruff, mypy AI | PASS, mypy 29 file |
| Pytest AI | 78 passed, 6 skipped (1 symlink Windows, 4 cần `VISIGN_BROWSER_FIXTURES`, 1 cần clip tham chiếu); cấp clip tham chiếu thì `test_video_pipeline.py` 15 passed |
| Integration API với clip người thật | `services/inference-api/tests/integration` + `tests/integration` có `VISIGN_CP2_REFERENCE_WEBM`: 40 passed, 0 skipped (parity offline ↔ API, đổi artifact T064) |
| A/B qua uvicorn thật | Hai server cùng máy, cùng artifact `pilot-gru-test-v1`; 38 clip người thật × 2 vòng, đảo thứ tự baseline/candidate theo từng clip và từng vòng |
| Đầu ra | 76/76 cặp cùng mã, nhãn và `accepted`; confidence lệch 0; 12 lượt `CLIP_TOO_LONG` giống nhau ở hai bên |
| Độ trễ (64 request 200 mỗi bên) | Processing p50/p95 3.208/3.484 → 2.940/3.221 ms; extract 3.022/3.260 → 2.759/3.044 ms; nhanh hơn ở 97% cặp, trung vị giảm 246 ms/request; request đầu sau khởi động 4.342 → 2.753 ms |
| Lỗi trong worker (probe detector giả) | Lần lượt cho hand, pose, face lỗi: lỗi nổi lên luồng gọi, 3/3 detector được tạo và đóng trên chính worker, không còn thread sót. Phía API, lỗi bất ngờ trả 500 `PREDICTION_FAILED` và vẫn giải phóng slot, clip tạm (test T045/T050) |

Nhận xét:

- Đầu ra giống hệt và p95 qua API giảm khoảng 8%. Bước đóng detector giờ chạy song song trong worker nhưng vẫn nằm
  trước khi `extract` trả kết quả. Bộ detector chuẩn bị sẵn của `592db9c` cho phép API tạo trước và đóng sau
  request: P2 nhận bàn giao, tích hợp vào API rồi đo lại độ trễ HTTP kèm parity.
- Khi một detector lỗi, luồng gọi vẫn chờ hai worker còn lại chạy hết clip rồi mới báo lỗi. Chấp nhận được vì hiếm.
- Chưa có unit test cho nhánh `parallel-by-group` (thứ tự kết quả theo frame, đóng detector khi lỗi). Đề nghị P3 thêm
  test bằng detector giả như probe trên; không chặn.
- Số tuyệt đối thấp hơn lần đo T037 trên cùng máy (p95 4,73 s ở `0f3c557`) dù pipeline không đổi giữa hai mốc, nên
  chỉ dùng A/B xen kẽ để so sánh tương đối. SC-002 vẫn chưa đạt (p95 3,22 s trên CPU Windows); cần đo trên host
  production (T095).

**Reviewer result**: `P2_VERIFIED` cho ứng viên khởi tạo detector song song (parity, dọn tài nguyên, độ trễ qua API).
T065 giữ `[ ]` theo P1: chờ số đo production và SC-002.


## Theo dõi review P2 — P3/Cường

Trên baseline `02cb36a`, bổ sung bốn ca cho nhánh `parallel-by-group`: giữ thứ tự frame của cả ba nhóm và đóng detector trên đúng worker khi xử lý thành công hoặc khi từng nhóm hand, pose, face báo lỗi.

Gate Windows gồm toàn bộ test AI và parity offline ↔ API trên một clip thật: **88 passed, 5 skipped** (bốn fixture MediaRecorder chưa cấp, một ca symlink thiếu quyền). Ruff check AI, format file test và mypy AI đạt. Phép chạy này chưa đo độ trễ qua HTTP của bộ detector tạo sẵn.

## Tích hợp API — P2/Tín

API dùng `prepare_detectors` qua pool một bộ dự phòng ở thread nền (`DETECTOR_PREWARM_ENABLED`, mặc định bật).
A/B 38 clip người thật × 2 vòng: 76/76 cặp cùng đầu ra; extract p50 2.861 → 2.589 ms; processing giảm trung vị
194 ms khi request có khoảng nghỉ, không lợi khi request dồn liên tục; RAM đỉnh +157 MiB; p95 processing 3.259 ms nên
SC-002 vẫn chưa đạt. Chi tiết: [evidence P2](T065-p2-tin-prepared-detectors-smoke.md).

## Đo lấy mẫu trước khi chuyển RGB — P2/Tín

Đo `2026-11-08` trên `7739c66`, CPU Windows. Bản thử giữ frame YUV khi giải mã, chọn tối đa 64 frame theo PTS bằng
`select_frame_indices`, rồi mới chuyển RGB và thu nhỏ đúng như `video_decoder.py`; các bước kiểm PTS, 6 s, 900 frame,
4K giữ nguyên. 32 clip người thật (6 clip dài hơn 6 s bị từ chối như decoder hiện tại), mỗi clip đo 5 lần mỗi cách,
đảo thứ tự; mọi clip trên 64 frame (trung vị 126, tối đa 154).

| Cỡ clip | Decode hiện tại p50 / p95 | Lấy mẫu trước p50 / p95 | Giảm p50 | Bộ nhớ frame (trung vị) |
|---|---:|---:|---:|---:|
| 360×640 | 134 / 165 ms | 125 / 157 ms | 11 ms | 83 → 87 MB |
| 480×640 (bằng số điểm ảnh 640×480 web xin) | 170 / 205 ms | 154 / 182 ms | 16 ms | 111 → 115 MB |
| 720×1280 (camera bỏ qua ràng buộc 640×480) | 511 / 596 ms | 433 / 503 ms | 78 ms | 83 → 219 MB |

Ảnh RGB của frame được chọn giống hệt nhau ở 32/32 clip mỗi cỡ. Kết luận: ở độ phân giải web gửi lên, cách này chỉ
giảm khoảng 16 ms (khoảng 0,5% của ~3 s xử lý); với video lớn giảm 78 ms nhưng tốn gấp 2,6 lần bộ nhớ vì phải giữ
frame YUV chưa thu nhỏ. Không đề xuất làm; chi phí chính vẫn là MediaPipe trên 64 frame.
