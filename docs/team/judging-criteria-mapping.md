# Ma trận tiêu chí chấm điểm ViSign

Tổng: 100 điểm. Trạng thái ban đầu: `PLANNED`; không tự nhận điểm khi evidence chưa `VERIFIED`.

| Nhóm | Điểm | Task ảnh hưởng | Evidence bắt buộc | Owner |
|---|---:|---|---|---|
| I. Sáng tạo & đổi mới | 10 | T085, T087 | Innovation report, comparison và demo khác biệt | Huy |
| II. Thực tiễn & khả năng áp dụng | 10 | T071, T087, T093 | User validation, nhóm mục tiêu, deployment/scale limits | Huy |
| III.1 Dữ liệu | 5 | T061, T076–T077, T098 | Dataset card, nguồn/quyền, chất lượng, đại diện, convention | Quang |
| III.2 Mô hình | 5 | T054, T057–T062 | Rationale, protocol tái lập, metrics, limitations | Cường |
| III.3 An toàn AI & thiên lệch | 5 | T044, T048, T066, T089 | Reject/OOD/bias/privacy/edge-case report | Cường |
| III.4 Chất lượng đầu ra & kiểm thử | 5 | T054–T065, T067, T089 | Test report, robustness, latency, full gate | Cường |
| IV.1 Cấu trúc dự án | 3 | T001, T069, T090 | Module tree, dependency/code-quality audit | Huy |
| IV.2 FE/UI/UX | 3 | T028, T031, T039–T043, T063, T088 | Responsive/a11y/usability/component evidence | Hiển |
| IV.3 BE & hiệu suất | 5 | T019–T026, T037–T038, T064–T065, T090 | REST contract, errors, performance/resource report | Tín |
| IV.4 CI/CD | 3 | T091 | Quality/deploy workflows và run history | Huy |
| IV.5 Bảo mật & độ tin cậy | 3 | T066, T092, T096 | Security scan, abuse boundaries, recovery/log privacy | Tín |
| IV.6 Độ hoàn thiện | 3 | T067, T070, T095–T096 | Production smoke, rollback, rehearsal | Huy |
| V. Đóng góp & cộng đồng | 10 | T063, T071, T093 | Impact, accessibility, user evidence, roadmap | Huy |
| VI. Chi phí & hiệu quả | 10 | T065, T094 | CPU/RAM/storage/network/cost và optimization comparison | Cường |
| VII. AWS/Google Cloud | 10 | T091, T095–T096 | HTTPS URL, cloud config, security, monitoring, rollback | Tín |
| VIII. Làm việc nhóm & trình bày | 10 | T085–T086, T097 | Member logs, checkpoint commits, demo/Q&A evidence | Huy |

Một dòng chỉ chuyển `READY` khi artifact ở `origin/main`, link đúng commit/revision được demo và
reviewer khác owner đã kiểm. Slide hoặc lời trình bày không thay thế test/report/cloud evidence.
