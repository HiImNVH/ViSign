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

## Kiểm tải đồng thời (2026-11-08, P1)

`services/inference-api/scripts/load_test_predictions.py`: N client gửi liên tục 4 clip WebM có người (chuyển từ bộ
test pilot, 640×480, 470–620 KB) trong 30 giây mỗi mức; artifact `t083-pilot-v2-approved`; một uvicorn worker, **một
slot suy luận**, chờ slot quá hạn trả `503 SERVICE_BUSY` (thiết kế MVP).

| Môi trường | Client | Request | 200 | 503 | Khác | Ký hiệu thành công/phút | p50 / p95 (s) |
|---|---:|---:|---:|---:|---:|---:|---|
| Docker local (i7-12700H) | 1 | 19 | 19 | 0 | 0 | 36,2 | 1,69 / 1,95 |
| | 2 | 19 | 18 | 1 | 0 | 32,0 | 3,48 / 5,71 |
| | 3 | 27 | 17 | 10 | 0 | 30,4 | 3,86 / 5,75 |
| | 4 | 35 | 16 | 19 | 0 | 28,0 | 4,55 / 6,83 |
| | 8 | 74 | 15 | 59 | 0 | 27,7 | 4,79 / 5,63 |
| AWS c7i-flex.large qua Quick Tunnel (từ VN tới Sydney) | 1 | 8 | 8 | 0 | 0 | 14,4 | 3,92 / 5,36 |
| | 2 | 11 | 11 | 0 | 0 | 19,5 | 6,08 / 7,35 |
| | 4 | 25 | 11 | 14 | 0 | 19,0 | 6,61 / 8,97 |
| | 8 | 16 | 2 | 6 | 8 | 1,8 | 5,41 / 8,96 |

Nhận xét:

- Thông lượng bão hoà ở **~30–36 ký hiệu/phút (local)** và **~19 ký hiệu/phút (AWS)**: đúng giới hạn một slot, quyết
  định bởi thời gian trích landmark MediaPipe (local ~1,4–2,0 s, c7i ~2,5–3,4 s mỗi clip); GRU < 5 ms.
- Vượt mức bão hoà hệ thống **từ chối nhanh bằng 503 + `Retry-After`** thay vì xếp hàng vô hạn; API không khởi động lại,
  không OOM (`RestartCount=0`, `OOMKilled=false`), log API chỉ có 200/503.
- Ở 8 client trên AWS, 8 lỗi "khác" xảy ra ở tầng Quick Tunnel/mạng (API không ghi nhận các request đó) — Quick Tunnel
  không dùng cho tải thật; production cần CloudFront/ALB.
- RAM container API đạt 1,35 GiB / giới hạn 1,5 GiB khi tải cao (tính cả page cache của container); cần nâng giới hạn
  hoặc theo dõi khi tăng worker.

## Rò rỉ RAM và cách sửa (T113, 2026-11-08)

Đo RAM thật (`anon` trong cgroup, không tính page cache) của container API, artifact pilot, clip 470–620 KB:

- Trước khi sửa, 8 client trong 40 s: anon **1.523 MiB** trên giới hạn 1.536 MiB, chạm trần **4.260** lần
  (`memory.events max`); hết tải RAM không giảm. Chạy riêng với giới hạn 4 GiB, request tuần tự: 441 → 1.249 (12 req) →
  1.692 (36) → 1.921 MiB (72) — tăng liên tục.
- A/B 36 request: `MALLOC_ARENA_MAX=2` → 826 MiB; tắt detector prewarm → 1.076 MiB; cả hai → 533 MiB. Nguyên nhân
  chính là arena glibc riêng cho mỗi luồng (worker + detector song song) làm phân mảnh bộ nhớ.
- 108 request: `MALLOC_ARENA_MAX=2` + prewarm ổn định **789 → 806 → 814 MiB** trong **182 s**; tắt prewarm ổn định
  ~530 MiB nhưng chậm hơn 24% (226 s). Chọn giữ prewarm.
- Sửa: `ENV MALLOC_ARENA_MAX=2` trong `infra/aws/docker/inference-api.Dockerfile`. Đo lại 8 client: anon đỉnh
  **929 MiB**, **0** lần chạm trần; thông lượng không đổi (~26–29 ký hiệu/phút). Giữ `mem_limit: 1536m` (dư ~600 MiB).
