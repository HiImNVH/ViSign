# T083 · Kiểm tra đầu vào pilot Sốt và Cảm ơn

T083 đang chờ bàn giao. Chưa có training run, dataset/run ID, metrics VSL hay
bằng chứng W&B. Artifact pilot vẫn phải công bố `demoReady=false`.

## Kiểm tra bàn giao

Đối chiếu snapshot T098 ở bản làm việc của Quang với danh mục `SOT`, `CAM_ON`
trên `main`. Đây là inventory review, chưa phải manifest train.

| Lớp ứng viên | Clip trong inventory |
|---|---:|
| SOT_HCM_1 | 2 |
| SOT_HCM_2 | 1 |
| CAM_ON_HCM_1 | 1 |
| CAM_ON_HN_2 | 2 |

Cả 6 clip có quyền `unknown`, xác minh `unverified` và split trống. Có 0 clip
đủ điều kiện train. Nếu giữ cả 4 lớp, mỗi lớp cần ít nhất một mẫu ở mỗi tập
train/validation/test, tức ít nhất 12 mẫu trước khi tính ràng buộc nhóm video
nguồn và lọc quyền. Quang cần xác minh nhãn, quyền, chọn lớp và audit coverage
trước khi bàn giao T076. Huy cần duyệt schema v0.3 và xác nhận các điều kiện
T078–T082 của US4. [Kế hoạch T083](../specs/001-vsl-recognition-mvp/tasks.md)

## Khi nhận đủ đầu vào

1. Ghim phiên bản manifest, class map, extractor/schema được duyệt, split
   theo video nguồn và hash bộ detector. Chạy T017 trên các mẫu được phép.
2. Chạy T036 với preset pilot và T058 trên tập test đã audit. Ghi số mẫu theo
   lớp/split, metric theo nghĩa, confusion matrix, artifact hash và run ID.
3. Lưu bằng chứng W&B và kiểm model-info/prediction với Tín. Giữ
   `demoReady=false` cho pilot.

[T017](evidence/checkpoints/CP2/T017-p3-cuong-smoke.md) ·
[T036](evidence/checkpoints/CP3/T036-p3-cuong-smoke.md) ·
[T058](evidence/checkpoints/CP5/T058-p3-cuong-smoke.md)
