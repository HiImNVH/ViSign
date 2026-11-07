# Ma trận tiêu chí chấm điểm ViSign

Tổng: 100 điểm. Không tự nhận điểm khi evidence chưa `VERIFIED`. Cập nhật: 2026-11-08 trên `origin/main`
(58/104 task `[X]` trong `specs/001-vsl-recognition-mvp/tasks.md`).

**Trạng thái**: `PLANNED` (chưa có artifact) → `IN_PROGRESS` (có artifact, chưa đủ task) → `PARTIAL`
(phần lớn task `[X]`, còn thiếu evidence bắt buộc) → `READY` (đủ task `[X]`, artifact trên `origin/main`,
reviewer khác owner đã kiểm).

| Nhóm | Điểm | Task ảnh hưởng | Task `[X]` | Trạng thái | Evidence hiện có | Còn thiếu | Owner |
|---|---:|---|---:|---|---|---|---|
| I. Sáng tạo & đổi mới | 10 | T085, T087 | 0/2 | `IN_PROGRESS` | `docs/innovation-feasibility.md` (bản đầu) | Review T087; demo điểm khác biệt | Huy |
| II. Thực tiễn & khả năng áp dụng | 10 | T087, T093 | 0/2 | `IN_PROGRESS` | `docs/innovation-feasibility.md`, `docs/community-impact.md` (bản đầu) | Chờ P2/P5 review; T071 đã bỏ (không có người dùng thật) | Huy |
| III.1 Dữ liệu | 5 | T061, T076–T077, T098 | 0/4 | `IN_PROGRESS` | `data/README.md`, `docs/team/data-convention.md`; snapshot P4 (chưa push) | Manifest pilot/full, dataset card, đóng băng T098 | Quang |
| III.2 Mô hình | 5 | T054, T057–T062 | 5/7 | `PARTIAL` | `docs/model-card.md`, CLI train/eval/gate (T036, T058, T059) | Metric trên artifact VSL thật (T062), dataset card (T061) | Cường |
| III.3 An toàn AI & thiên lệch | 5 | T044, T048, T066, T089 | 3/4 | `PARTIAL` | Luật ngưỡng, audit privacy, `docs/ai-safety-report.md` | OOD/bias trên artifact thật (T089) | Cường |
| III.4 Chất lượng đầu ra & kiểm thử | 5 | T054–T065, T067, T089 | 7/14 | `IN_PROGRESS` | 399+ test API/contract/integration, parity offline↔API 32/32, CI xanh | Split test (T056), latency SC-002 (T065), quickstart (T067) | Cường |
| IV.1 Cấu trúc dự án | 3 | T001, T069, T090 | 1/3 | `IN_PROGRESS` | Monorepo CP1, `README.md` (bản mở rộng) | Review T069; audit kiến trúc T090 | Huy |
| IV.2 FE/UI/UX | 3 | T028, T031, T039–T043, T063, T088 | 5/9 | `PARTIAL` | Camera flow, kết quả, lỗi tiếng Việt, US6 lịch sử 24 giờ | Accessibility audit (T063), UX audit (T088); tick T028/T031 | Hiển |
| IV.3 BE & hiệu suất | 5 | T019–T026, T037–T038, T064–T065, T090 | 11/13 | `PARTIAL` | REST v1 đóng băng, 404/405/307, đổi artifact, `docs/performance-report.md` | SC-002 trượt (web p95 5,87 s), T090 | Tín |
| IV.4 CI/CD | 3 | T091 | 0/1 | `PARTIAL` | `quality.yml` xanh trên mọi push | `deploy-aws.yml` (OIDC bị chặn trên Free Plan) | Huy |
| IV.5 Bảo mật & độ tin cậy | 3 | T066, T092, T096 | 2/3 | `PARTIAL` | `docs/security-report.md`, header, quét secret/dependency | IAM/OIDC production (T096) | Tín |
| IV.6 Độ hoàn thiện | 3 | T067, T070, T095–T096 | 0/4 | `PLANNED` | — | Production smoke, rollback, tổng duyệt | Huy |
| V. Đóng góp & cộng đồng | 10 | T063, T093 | 1/2 | `IN_PROGRESS` | `docs/community-impact.md` (bản đầu), T063 `VERIFIED` | T093 chờ review; T071 đã bỏ | Huy |
| VI. Chi phí & hiệu quả | 10 | T065, T094 | 0/2 | `IN_PROGRESS` | `docs/cost-report.md`, `docs/performance-report.md` (local) | Số đo production, tối ưu latency | Cường |
| VII. AWS/Google Cloud | 10 | T091, T095–T096 | 0/3 | `IN_PROGRESS` | Kế hoạch `infra/aws/`, evidence bootstrap OIDC T096 | URL HTTPS công khai, monitoring, rollback | Tín |
| VIII. Làm việc nhóm & trình bày | 10 | T085–T086, T097 | 1/3 | `IN_PROGRESS` | Member logs, evidence theo checkpoint, CI | Demo/Q&A (T097), ma trận này được review | Huy |

## Rủi ro ảnh hưởng điểm

1. **Dữ liệu** (III, VI): chưa có manifest đã audit → chưa train/đánh giá model thật; ảnh hưởng III.1–III.4.
2. **Latency** (IV.3, VI): web p95 5,87 s so với SC-002 ≤ 3 s; nút thắt là trích landmark MediaPipe.
3. **Cloud** (IV.4, IV.6, VII): OIDC bị chặn trên AWS Free Plan; chưa có URL production.

Một dòng chỉ chuyển `READY` khi artifact ở `origin/main`, link đúng commit/revision được demo và
reviewer khác owner đã kiểm. Slide hoặc lời trình bày không thay thế test/report/cloud evidence.
