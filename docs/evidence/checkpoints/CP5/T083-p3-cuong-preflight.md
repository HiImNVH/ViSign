# CP5 T083 · P3/Cường

Baseline `c875ae5`. Reviewer P4/Quang và P1/Huy.

Đọc snapshot `T098/review-data/inventory-review.csv` bằng `Import-Csv` và lọc
`meaningId` theo `SOT`, `CAM_ON`. Kết quả 6 clip thuộc 4 lớp. Cả 6 có
`licenseStatus=unknown`, `verificationStatus=unverified`, split trống. Schema
trên main vẫn `DRAFT_PENDING_LEAD_REVIEW` và T076, T078–T082 vẫn mở.

**BLOCKED** · 0 clip đủ điều kiện. Chưa chạy trích hàng loạt, train, evaluate
hay W&B. [Chi tiết và bước mở khóa](../../../pilot-report.md).

## Independent review — P1/Huy

Review `2026-11-08T00:37:34+07:00` trên `dc9e357` (P1 review theo uỷ quyền của Huy). Đồng ý trạng thái `BLOCKED`. Một phần blocker **không phải thiếu dữ liệu**: manifest đang ghi
`licenseStatus=unknown`, trong khi quyết định lead 2026-11-07 khai nguồn/căn cứ sử dụng **một lần ở mức bộ
dữ liệu** cho video giáo dục công khai → các clip của bộ này phải là `licenseStatus=approved`
(`data/README.md`, `docs/team/data-convention.md` mục 4). P4 cập nhật manifest; split và schema `APPROVED`
vẫn là blocker riêng.

**Reviewer result**: T083 giữ `[ ]`.
