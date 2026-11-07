# ViSign · Báo cáo hiệu năng T065

## Phạm vi đo

- Local Windows 11, Intel Core i7-12700H (20 CPU logic), Uvicorn một worker, GRU CPU. Backend chạy với artifact pilot T036 tổng hợp `test-v1`, `demoReady=false` và detector MediaPipe. Kết quả đo hiệu năng, chưa dùng để đánh giá nhận diện VSL.
- HTTP chạy tuần tự trên 6 clip WebM review cục bộ, lặp 3 vòng và bỏ 1 request warm-up. Cả 18 request trả HTTP 200 và có request ID khớp. Báo cáo chỉ lưu chỉ số clip, không ghi tên, video hay landmark.
- Web dùng Edge headless và frontend local. Mỗi clip cấp hình cho luồng camera mô phỏng qua canvas. Web quay lại bằng MediaRecorder trong khoảng 2,3 giây rồi gửi POST thật qua Vite proxy đến cùng API. Đo từ sự kiện click **Gửi nhận diện** đến khi vùng kết quả hiện và được Playwright quan sát. Chạy 6 lượt, tất cả HTTP 200. Hai phép đo dùng độ dài đoạn đầu vào khác nhau và không ghép số liệu giữa hai bộ.

## Kết quả local

| Phép đo | p50 (ms) | p95 (ms) | Max (ms) |
|---|---:|---:|---:|
| Decode | 411 | 490,95 | 519 |
| Extract MediaPipe | 4.644,50 | 5.264,95 | 5.361 |
| Infer GRU | 3 | 4,15 | 5 |
| Xử lý API theo response | 5.064 | 5.694,85 | 5.830 |
| Client HTTP gửi đến nhận response | 5.085,60 | 5.708,97 | 5.862,94 |
| Web từ bấm gửi đến thấy kết quả, frontend 05d906f | 4.739,50 | 6.424,65 | 6.584,40 |

Throughput HTTP tuần tự **0,220 request/giây**, tính trên tổng thời gian request. Worker đạt **384,3 MiB** peak working set kể từ lúc khởi động và **197,1% CPU** ở cửa sổ request cao nhất (100% tương đương một CPU logic). Đây là peak giữa các mức CPU trung bình theo cửa sổ request, chưa đo peak tức thời. Mẫu web nhỏ, gồm cả lượt đầu và độ trễ quan sát của driver. Lượt trên frontend cedd013 trước khi đồng bộ ghi p95 8,10 s. Hai lượt được ghi riêng.

**SC-002 chưa đạt ở local** · Cả sáu lượt web vượt 3 giây. Trong phép đo HTTP, phần trích landmark chiếm phần lớn độ trễ, trong khi GRU dưới 5 ms ở p95. Ưu tiên đo lại riêng chi phí khởi tạo detector, số frame thực sự được đưa vào MediaPipe và thời gian chạy detector. Khi tối ưu, kiểm lại tensor/mask parity và chất lượng landmark trên cùng clip.

## Thử tối ưu khởi tạo detector

Trên baseline `cfa9f04`, phần tạo ba detector tuần tự mất khoảng 175–196 ms ở năm
lượt sau lần đầu (489 ms). Bản thử cho từng worker tạo, chạy và đóng detector của
mình. Mỗi clip vẫn có ba detector mới, cùng model, timestamp và thứ tự điểm.

Đo `process_video` trên Windows, CPython 3.12.15 và MediaPipe 1.1.1 với cùng
sáu clip review. Mỗi phương án có một lượt warm-up và 12 lượt đo. Đảo thứ tự A/B
giữa các clip và hai vòng. Các clip có 56–104 frame, trong đó 56–64 frame được
đưa vào MediaPipe.

| Phép đo | Baseline p50 / p95 (ms) | Khởi tạo song song p50 / p95 (ms) |
|---|---:|---:|
| Decode | 429 / 536 | 333 / 556 |
| Extract gồm khởi tạo | 4.070 / 5.338 | 2.893 / 4.575 |
| Tiền xử lý toàn bộ | 4.646 / 6.002 | 3.332 / 5.250 |
| CPU time của tiến trình | 9.695 / 11.820 | 7.695 / 11.285 |

Tensor khớp trong sai số tuyệt đối `1e-6` và ba mask khớp chính xác ở cả 12/12
cặp. Độ trễ dao động đáng kể giữa các lượt, kể cả phần decode dùng cùng mã.
Mức giảm p95 khoảng 13% là quan sát của lần đo này. Schema và giới hạn lấy mẫu
vẫn dùng bản v0.3 draft.

Smoke HTTP trên candidate dùng Uvicorn loopback và artifact T036 tổng hợp
`pilot-gru-test-v1`. Sau một lượt warm-up, 6/6 clip review trả 200 và request ID
khớp. p50/p95 HTTP là 3.912/5.473 ms. p95 decode/extract/GRU là 586/4.850/5 ms.
Throughput tuần tự 0,263 request/s. Tổng video gửi 3,831 MiB chưa tính multipart.
Đỉnh CPU theo cửa sổ request là 216,2%. Peak working set 866,7 MiB của tiến trình
đo chung với bộ kiểm thử và Uvicorn chỉ để tham chiếu. Đo RAM worker riêng khi
chọn instance. Số đo HTTP này là smoke một vòng, còn đối chứng ở bảng trên chỉ
đo tiền xử lý.

Đo lại web local trên `c875ae5` với candidate, Edge headless, MediaRecorder
khoảng 2,3 giây, sáu clip review cấp qua camera mô phỏng và POST thật qua
Vite proxy đến một worker Uvicorn. Từ click **Gửi nhận diện** đến khi thấy
kết quả, p50/p95/max lần lượt là **4,91 / 5,87 / 6,16 giây**. 6/6 HTTP 200,
0/6 đạt 3 giây. Worker dùng GRU tổng hợp `pilot-gru-test-v1`.
**SC-002 vẫn chưa đạt local.** Các lượt đo cũ và mới chạy ở hai phiên
riêng. Đối chứng trong cùng tiến trình ở bảng trên chỉ đo tiền xử lý.

## Tái lập và production

Chạy backend với artifact và detector xác định. Từ gốc repo, chạy CLI dưới đây với video đại diện, một worker riêng và không có tải khác.

```powershell
uv run --locked --project ai python -m visign_ai.evaluation.benchmark_inference --base-url http://127.0.0.1:8000 --clips "PATH/clip-1.webm" "PATH/clip-2.webm" --repeats 3 --warmup 1 --server-pid 1234 --output "PATH/t065-local.json"
```

`--server-pid` là PID của worker chạy cùng máy với CLI trên Windows hoặc Linux. Để đo qua mạng từ máy demo, dùng URL production và bỏ PID. Thu CPU/RAM ở host production trong lượt tải tương ứng, rồi đo web từ máy demo trên URL thật. Ghi commit, revision deploy, phần cứng, codec, mẫu đo và tỷ lệ lỗi cạnh kết quả. Percentile dùng nội suy tuyến tính trên các lượt đo, throughput ở đây mô tả tải tuần tự.

**Production chưa đo.** Repo hiện có bằng chứng chuẩn bị triển khai AWS, chưa có URL production và PID worker đã xác nhận cho lượt đo T065. [Trạng thái AWS T096](evidence/checkpoints/CP7/T096-aws-access-bootstrap.md)

Tham chiếu [smoke 32 clip của Tín](evidence/checkpoints/CP3/T037-p2-tin-real-clip-smoke.md) và [benchmark RAM T095](evidence/checkpoints/CP7/T095-p2-tin-serving-ram-benchmark.md). Các phép đo đó dùng môi trường hoặc tập clip khác.
