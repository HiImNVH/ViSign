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
xác nhận host, kết quả và phạm vi chi phí. AWS production còn bị chặn ở
[T096](evidence/checkpoints/CP7/T096-aws-access-bootstrap.md).
