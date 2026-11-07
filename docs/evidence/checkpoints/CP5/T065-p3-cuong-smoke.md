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
