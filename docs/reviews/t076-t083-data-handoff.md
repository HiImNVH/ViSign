# T076 / T083 — data-only review branch

Branch `quang/t076-t083`, tạo từ main `bed64a9`. Không sửa main trực tiếp.

## Yêu cầu Huy và kết quả

1. `sourceUri` được đối chiếu từng sample ID. Người dùng xác nhận rõ cả 15 clip
   pilot là tự quay, nên giữ `dataset:self-recorded` cùng evidence trực tiếp
   trong [pilot-source-confirmation.json](../evidence/dataset/t076-t083-handoff/pilot-source-confirmation.json).
   Bộ 101 clip gồm 76 tự quay và 25 công khai; mỗi clip công khai có URL đã biết
   hoặc URL/tên website được người cung cấp xác nhận. Không để trống hoặc gán
   tự quay cho các clip công khai. Xem [source-uri-validation.json](../evidence/dataset/t076-t083-handoff/source-uri-validation.json).
2. Split theo FR-015 trên main: cách ly video gốc, signer tùy chọn cả full,
   verified/unverified đều nhận và không tự đổi trạng thái. Rejected vẫn bị chặn.
   Solver ưu tiên signer khi khả thi, fallback theo video gốc và ghi kết quả thử.
3. `training_inputs.py`, tất cả source landmarks, schema và runtime của main
   được giữ nguyên. Không chép snapshot training/landmarks từ gói local.
4. Nhánh chỉ thêm dataset code/tests, manifest và evidence/tài liệu dạng text.
   Không có raw video, detector `.task`, `model.pt`, ZIP, NPZ hoặc W&B binary.

## Kiểm chứng

- 89 dataset tests và 61 subtests PASS; test full 200 mẫu giữ source URI từng
  dòng, nhận unverified và signer trống, không xuất manifest nếu rejected/leakage.
- Hash raw pilot 15/15, metadata/training gate PASS; raw DRAFT 101/101 PASS.
- DRAFT vẫn bị chặn full bởi class/quota/coverage; không có approved full manifest.
- Model, weights, test split và run `kbj3bpvu` không thay đổi. Metrics 25% / 0,3333
  là run được P3 đánh giá lại trên main, không phải kết quả retrain trong PR này.
- Có JUnit, source/gate evidence và kiểm biên file trong cùng thư mục evidence.

Raw clip/model ở gói `Nháp/T083` để reviewer kiểm cục bộ; những file này không
được đẩy lên GitHub. Các snapshot T013/T018/T056/T098 cũ không phải nguồn để chép
nguyên thư mục vào main; branch này là diff trên main mới để review từng file.

## Phần không tự nghiệm thu

Giữ T076/T083 mở cho quyết định lead. Scope Giấy tờ/Nhận đã được Huy chốt trên
main `3b29d4a`, P3 review metrics đã có tại `625a8b0`; không yêu cầu duyệt lại
hai việc đó. T078–T082 là dependency của Tín/Hiển, không được tự đóng trong PR dữ liệu.
`demoReady=false` giữ nguyên.
