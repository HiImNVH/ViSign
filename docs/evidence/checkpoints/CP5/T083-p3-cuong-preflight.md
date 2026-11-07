# CP5 T083 · P3/Cường

Baseline `c875ae5`. Reviewer P4/Quang và P1/Huy.

Đọc snapshot `T098/review-data/inventory-review.csv` bằng `Import-Csv` và lọc
`meaningId` theo `SOT`, `CAM_ON`. Kết quả 6 clip thuộc 4 lớp. Cả 6 có
`licenseStatus=unknown`, `verificationStatus=unverified`, split trống. Schema
trên main vẫn `DRAFT_PENDING_LEAD_REVIEW` và T076, T078–T082 vẫn mở.

**BLOCKED** · 0 clip đủ điều kiện. Chưa chạy trích hàng loạt, train, evaluate
hay W&B. [Chi tiết và bước mở khóa](../../../pilot-report.md).
