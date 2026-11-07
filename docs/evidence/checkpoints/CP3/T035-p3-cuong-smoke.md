# CP3 T035 · P3/Cường

Baseline origin/main: f128fa5b0246f1e3641631ac85cbff07571b219a. Candidate LOCAL-DRAFT, chờ push và P1/Huy, P2/Tín review.

| Cấu hình | Loại artifact | Số nghĩa | Seed | Hidden size | Batch | Epoch |
|---|---|---:|---:|---:|---:|---:|
| pilot-gru.yaml | pilot | 1–3 | 42 | 64 | 16 | 30 |
| p0-gru.yaml | full | đúng 10 | 42 | 128 | 32 | 60 |

Hai cấu hình dùng 32 bước, 234 đặc trưng, một lớp GRU, learning rate 0,001 và năm ứng viên ngưỡng từ 0,5 đến 0,9. Các siêu tham số nền kế thừa hai YAML của 7nghiep367 ở commit 267419b. Thêm loại artifact, giới hạn số nghĩa và kích thước theo schema của repo mới. Giới hạn áp dụng cho meaningId. Số logits theo class map thực tế, nên có thể lớn hơn số nghĩa khi có biến thể.

Smoke trên CPU: đọc YAML bằng safe_load, đối chiếu kích thước với feature schema, tạo GRU và chạy một bước Adam trên tensor tổng hợp. Với mỗi cấu hình, hai lượt khởi tạo cùng seed cho trọng số sau bước đó khớp tuyệt đối. Pytest ai/tests/training: 21 passed.

T036 sẽ đọc và áp dụng các trường này, giữ thứ tự class map, kiểm phạm vi nghĩa và chọn ngưỡng từ validation. Chưa chạy train chính thức, chưa có ngưỡng được chọn hay số đo chất lượng.
