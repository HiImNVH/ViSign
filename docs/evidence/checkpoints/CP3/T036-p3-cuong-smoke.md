# CP3 T036 · P3/Cường

Baseline origin/main: 7a8c27717e6cf75482c4b1a0c4dbf0076244f4ad. Candidate LOCAL-DRAFT, chờ push và P1/Huy, P2/Tín review.

## Chạy từ gốc repo sau khi có schema và manifest đã duyệt

```powershell
uv run --locked --project ai python -m visign_ai.training.train --help
uv run --locked --project ai python -m visign_ai.training.train --manifest "PATH/pilot.csv" --feature-root "PATH/dataset" --class-map "PATH/class-map.json" --schema "PATH/feature_schema.json" --config ai/configs/pilot-gru.yaml --dataset-version pilot-v1 --model-version pilot-gru-v1 --output "PATH/pilot-gru-v1"
```

Class map JSON ánh xạ classLabel sang object có meaningId và displayText. CLI giữ thứ tự của class map ngay cả khi --classes được nhập theo thứ tự khác. Full dùng p0-gru.yaml và cần --p0-meanings trỏ tới registry 10 nghĩa.

CLI kiểm các cột dùng cho training trên manifest đã audit, yêu cầu schema APPROVED và licenseStatus approved. Mẫu rejected bị loại khỏi khả năng huấn luyện bằng lỗi preflight. Các split phải đủ lớp đã chọn và tách theo recordingSessionId. Chỉ train/validation được đọc tensor trong lượt train; test để riêng cho T058. CLI không gán split hay thay validator dữ liệu của Quang.

Checkpoint tốt nhất theo validation loss. Threshold được chọn chỉ từ validation. CLI công bố cùng lúc model.pt, feature_schema.json, model_info.json và training-report.json trong một thư mục mới. Checkpoint ràng buộc schema hash và thứ tự lớp, nghĩa, chữ hiển thị. Metadata giữ demoReady=false và metric đánh giá null. Bản sửa tái sử dụng bảo vệ encoding của T017 cho CLI mới.

Tham khảo train.py và cách ghi artifact bất biến ở 7nghiep367, commit 73825c7. Dùng loader T034 và preset T035 của repo mới, đối chiếu metadata với loader API hiện tại. Split chính thức là video-held-out theo FR-015, không yêu cầu signerId như bản legacy.

## Gate cục bộ

- 5 test T036 đạt. Pilot tổng hợp chạy hai lần với cùng seed cho stateDict bằng nhau. Full tổng hợp 10 nghĩa chỉ chạy khi registry đúng. Chặn schema draft, nguồn chưa approved, rò rỉ phiên và ghi đè output.
- AI 60 passed, 1 skipped do quyền symlink Windows. API và contract 179 passed, 1 skipped. Ruff và mypy AI PASS.
- CLI --help chạy với cp1252. API đọc model_info.json từ 2 artifact pilot và 1 artifact full tổng hợp. Kiểm tra này xác nhận metadata, chưa xác nhận dự đoán GRU qua API.
- Chưa train dữ liệu thật, chạy GPU, ghi W&B hoặc đánh giá test. W&B evidence của pilot thuộc T083.
