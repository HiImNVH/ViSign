# T094 · Tài nguyên và chi phí ViSign

## Đo local

Windows, Intel Core i7-12700H, CPython 3.12.15, MediaPipe 1.1.1, PyAV 19.0.2.
So sánh `c875ae5` với candidate T065 khởi tạo detector song song. Dùng
`services/inference-api/scripts/benchmark_serving_memory.py --runs 2`, bốn
gradient WebM 5,9 giây, mỗi clip và mỗi phương án có tiến trình riêng. Script
import API, pipeline và PyTorch rồi trích đặc trưng qua adapter T037.

| Clip | Baseline ms hai lượt / RAM đỉnh MiB | Candidate ms hai lượt / RAM đỉnh MiB |
|---|---:|---:|
| VP8 640×480 30 fps | 4.495, 1.795 / 840,3 | 3.606, 3.303 / 844,1 |
| VP9 640×480 30 fps | 4.482, 3.855 / 840,6 | 3.785, 3.495 / 843,4 |
| VP8 1280×720 30 fps | 5.067, 4.414 / 825,2 | 4.094, 3.849 / 830,6 |
| VP8 640×480 60 fps | 4.510, 3.875 / 904,4 | 3.928, 3.857 / 907,2 |

Trong tám lượt mỗi phương án, p95 trích qua adapter giảm từ 4,87 xuống
4,04 giây, RAM đỉnh tăng khoảng 2,8 MiB. Mỗi phương án chỉ có hai lượt mỗi clip.
Trên bộ sáu WebM review có người, p50 CPU time của tiến trình giảm từ 9,70
xuống 7,70 CPU-giây trong đối chứng T065, với tensor/mask khớp ở 12/12 cặp.
Web local với GRU tổng hợp vẫn có p95 5,87 giây. [Kết quả T065](performance-report.md)

Ba detector chiếm 20.975.899 byte (20,00 MiB). Bundle pilot tổng hợp chiếm
21.515 byte, trong đó trọng số 14.613 byte. Chưa đo kích thước image triển khai,
bundle VSL thật hoặc log theo tải. Sáu lượt web gửi tổng 3.554.105 byte
multipart và nhận 1.914 byte JSON, chưa tính HTTP headers/TLS. Ngoại suy theo
mẫu này, 1.000 lượt tương đương khoảng 0,59 GB request body và 0,32 MB JSON.

## Dự toán AWS Sydney

Giá EC2 Linux On-Demand theo dữ liệu AWS công bố 07/11/2026. Tính 730 giờ
và một địa chỉ IPv4 công khai giữ suốt kỳ, chưa tính credit hoặc thuế.

| Instance | RAM | EC2 USD/giờ | EC2 + IPv4 USD/730 giờ |
|---|---:|---:|---:|
| t3.micro | 1 GiB | 0,0132 | 13,29 |
| t3.small | 2 GiB | 0,0264 | 22,92 |
| t3.medium | 4 GiB | 0,0528 | 42,19 |

Nguồn giá [EC2 Sydney Linux](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/Asia%20Pacific%20%28Sydney%29/Linux/index.json)
và [IPv4 0,005 USD/giờ](https://aws.amazon.com/vpc/pricing/).

Kịch bản dự toán dùng 20 GB gp3 với giả định 0,10 USD/GB-tháng và 1 GB ECR
với 0,10 USD/GB-tháng theo ví dụ AWS. Tổng t3.small là khoảng **25,02 USD**
cho 730 giờ trước S3/CloudFront, egress, logs, snapshot, CPU credit và thuế.
Xác nhận lại đơn giá gp3 Sydney và các mục biến đổi bằng cấu hình thực khi
Tín chốt deploy. [EBS](https://aws.amazon.com/ebs/pricing/) · [ECR](https://aws.amazon.com/ecr/pricing/) · [CloudFront](https://aws.amazon.com/cloudfront/pricing/)

## Phương án gửi lead

Ưu tiên thử t3.small với một worker. Bản local đã dùng tới 907,2 MiB chỉ
cho tiến trình đo, nên 1 GiB có ít dư địa cho hệ điều hành và dịch vụ đi kèm.
Candidate song song giảm latency trong hai phép đối chứng local với ít thay
đổi RAM và giữ parity. Giữ nguyên số frame/schema để tránh đổi đầu vào model.
Chạy lại tải trên Linux đích, gồm CPU credit, RAM, kích thước image, egress,
p95 end-to-end và chất lượng model thật. Chỉ chốt budget sau khi Tín/Huy
xác nhận host, kết quả và phạm vi chi phí.

## Đối chiếu cấu hình EC2 đã triển khai

Theo [báo cáo triển khai T095](deployment-report.md) tại `2182f85`, origin đang dùng t3.small Sydney, EBS 30 GB và Elastic IP. Dự toán của nhóm triển khai là khoảng **0,9 USD/ngày (~27 USD/tháng nếu chạy liên tục)** trước credit. Đây là dự toán cho cấu hình triển khai, chưa có hóa đơn đối chiếu.

| Phép đo đã ghi nhận | Kết quả | Phạm vi |
|---|---|---|
| Image API / web trên ECR | Khoảng 665 MB / 26 MB nén | Image tag `3b29d4a2cec1` |
| RAM trên EC2 khi nghỉ | API 58 MiB, web 4,8 MiB | Artifact fixture |
| Upload và round-trip từ Việt Nam | 1,65–2,07 s, fixture xử lý khoảng 1 ms | Origin HTTP, chưa qua CloudFront |
| A/B detector tạo sẵn của Tín | Processing p95 3,295 → 3,259 s; RAM đỉnh 572 → 729 MiB | Windows local, cùng workload; request có khoảng nghỉ giảm trung vị 194 ms |
| Pilot Giấy tờ / Nhận trong Docker | 1,4–2,3 s/clip trên 4 clip, RAM 890 MiB | Smoke local của Huy |

t3.small đang chạy origin với fixture. Số đo pilot local cho thấy cần giữ dư địa RAM cho detector tạo sẵn. Phần cần đo tiếp là CPU credit, RAM đỉnh và p95 web khi EC2 phục vụ artifact thật qua HTTPS. [Đối chứng T065 của Tín](evidence/checkpoints/CP5/T065-p2-tin-prepared-detectors-smoke.md) · [Trạng thái pilot](team/implementation-status.md)

## Chi phí và tài nguyên thực tế sau deploy (T094, 2026-11-08)

Giá on-demand Sydney lấy từ AWS Pricing API ngày 2026-11-08: **t3.small 0,0264 USD/giờ** (2 vCPU, 2 GiB),
**c7i-flex.large 0,1107 USD/giờ** (2 vCPU, 4 GiB), gp3 **0,096 USD/GB-tháng**; IPv4 công khai 0,005 USD/giờ.

| Hạng mục | Thực tế | Chi phí |
|---|---|---|
| EC2 | t3.small thường ngày; c7i-flex.large trong ngày demo | 0,63 / 2,66 USD mỗi ngày chạy 24 giờ |
| EBS gp3 30 GB | Đĩa dùng ~21% (6,3 GB) | 2,88 USD/tháng (~0,10 USD/ngày) |
| Elastic IP / IPv4 | 1 địa chỉ | 0,12 USD/ngày |
| ECR | Image API ~665 MB nén, web ~26–60 MB; giữ 5 image mỗi repo | < 0,4 USD/tháng |
| S3 | Artifact ~250 KB + compose | không đáng kể |
| Mạng | Mỗi ký hiệu upload ~0,5–0,6 MB (vào AWS miễn phí); phản hồi < 1 KB | không đáng kể |
| CloudFront | Chưa bật (chờ xác minh tài khoản) | 0 |

Một ngày demo trên c7i-flex.large ≈ **2,9 USD**; một tháng t3.small chạy liên tục ≈ **22,9 USD** (EC2 + IPv4) +
2,9 USD đĩa. Credit Free Plan 100 USD; Budget cảnh báo 5/20/50 USD.

### So sánh cấu hình (số đo cùng 4 clip pilot, cùng artifact)

| Cấu hình | Xử lý trên server | Round-trip từ VN | Thông lượng bão hoà | RAM API đỉnh | Chi phí |
|---|---|---|---|---|---|
| Docker local (i7-12700H) | 1,2–2,0 s | 1,2–2,0 s | ~30–36 ký hiệu/phút | 929 MiB (8 client, sau sửa) | 0 |
| AWS t3.small | 4,0–4,7 s | 5,5–6,3 s | chưa đo tải | ~1 GiB / 2 GiB máy | 0,63 USD/ngày |
| AWS c7i-flex.large | 2,5–3,4 s | 3,9–5,4 s | ~19 ký hiệu/phút | ~0,9 GiB / 4 GiB máy | 2,66 USD/ngày |

### Phương án tối ưu đã đánh giá

| Phương án | Kết quả | Trạng thái |
|---|---|---|
| Sửa rò rỉ RAM `MALLOC_ARENA_MAX=2` | RAM đỉnh 1.523 → 929 MiB, 0 lần chạm trần, thông lượng không đổi — cho phép giữ giới hạn 1,5 GiB, **đủ chạy trên t3.small 2 GiB** | Đã đo, đã áp dụng |
| Đổi t3.small → c7i-flex.large | Xử lý nhanh ~35%, chi phí ×4,2 | Đã đo; chỉ bật ngày demo |
| Trình duyệt trích landmark, gửi tensor thay video | Server chỉ chạy GRU (< 5 ms), bỏ upload video → ước lượng < 1 s/ký hiệu và nhiều người dùng/instance hơn | Ước lượng, chưa làm (M2) |
| Chuyển region Singapore | Giảm độ trễ mạng từ VN; giá EC2 tương đương | Ước lượng, chưa làm |

### Quyết định

Chất lượng model chưa đạt cổng phát hành nên không chi thêm cho hạ tầng lớn hơn. Demo chính chạy **local** (đạt
≤ 3 s, 0 USD); bản AWS dùng **c7i-flex.large chỉ trong ngày demo** rồi dừng hoặc xoá stack `visign-origin`; khi cần
chạy dài ngày dùng **t3.small** (đủ RAM sau khi sửa rò rỉ, chấp nhận 5,5–6,3 s). Hướng đầu tư tiếp theo cho độ trễ là gửi
landmark từ trình duyệt, không phải máy lớn hơn.
