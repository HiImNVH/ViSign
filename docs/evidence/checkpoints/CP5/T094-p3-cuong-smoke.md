# CP5 T094 · P3/Cường

Candidate `CP5 T094(eval): measure local resource and cost trade-offs`.
Baseline `c875ae5`. Reviewer P1/Huy, P2/Tín.

| Kiểm tra | Kết quả |
|---|---|
| `python services/inference-api/scripts/benchmark_serving_memory.py --runs 2` | Exit 0 cho cả baseline và candidate T065. Windows, 4 WebM tổng hợp × 2 lượt mỗi phương án, tiến trình riêng từng clip |
| Kích thước và truyền tải local | Đo byte của ba detector, bundle tổng hợp, và request/response của 6 lượt Edge |
| Dự toán USD | Giá EC2 Sydney Linux và IPv4 theo AWS. Dự toán EBS/ECR ghi giả định riêng |
| Linux/EC2, invoice, CPU credit, SC-002 và chất lượng thật | NOT_RUN. Chờ T095/T096 và artifact VSL thật |

[Kết quả và dự toán](../../../cost-report.md). T094 mở, chờ review.
