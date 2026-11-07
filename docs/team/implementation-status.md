# ViSign implementation tracking snapshot

Snapshot date: 2026-11-07

Repository: `HiImNVH/ViSign`

Source of truth: `specs/001-vsl-recognition-mvp/tasks.md`

## Current baseline

Cập nhật `2026-11-08T02:55:00+07:00` trên `origin/main` `a214a3c`.

### Checkpoint

| CP | Trạng thái | Ghi chú |
|---|---|---|
| CP0 | `VERIFIED` | Spec Kit, rubric, member/checkpoint docs — `docs/evidence/checkpoints/CP0/` |
| CP1 | `VERIFIED` | T001–T008, T086 `[X]`; closure trong `docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md` |
| CP2 | `OPEN` | Đóng khi đủ bảng "CP2 còn mở" bên dưới |
| CP3 | `NOT OPEN` | T039 `[X]`; endpoint, registry và CLI train đã có trên `main`; không đóng trước CP2 |
| CP7 | `PARTIAL / BLOCKED` | T091 quality CI chạy trên mọi push; OIDC bootstrap rollback do AWS Free Plan SCP; Tín đã có project access, chưa có workload production |

### CP2 còn mở

| Hạng mục | Owner → reviewer | Trạng thái |
|---|---|---|
| T099 FE–BE API convention | P2 → P1 lead, P5 consumer | `VERIFIED`, `[X]` |
| T024–T025 temporary clip | P2 → P1 | `VERIFIED`, `[X]` |
| T021 error catalog, T023 logging | P2 → P1, P5 | `VERIFIED`, `[X]` |
| T019 model metadata | P2 → P1, P3 | `VERIFIED`, `[X]` — P3 xác nhận (`989533e`); T059 ghi `demoReady` theo gate full là việc tiếp theo |
| T020, T022, T026 | P2 → P1, P5 | `VERIFIED`, `[X]` — fix của P2 đã được P1 kiểm chứng; P5 kiểm lại độc lập trên `bb40476` (179 passed, 1 skipped) và ghi `P5_VERIFIED` trong evidence CP2 |
| T014–T016 shared pipeline | P3 → P1, P2 | `VERIFIED`, `[X]` — Huy duyệt schema v0.3 trên 6 clip; `status: APPROVED` (digest không đổi) |
| T017 batch extraction CLI | P3 → P2, P1 | `VERIFIED`, `[X]` — P2 verify test batch; P3 verify fix `--help` của P1 (`d258baf`) |
| T009–T013 dataset entities/schema/validator/registry | P4 → P3, P1 | Snapshot P4 review `CHANGES_REQUESTED` (P3): Ruff/mypy lỗi, T010 chưa nối `sampleId/rawPath` sang T017; inventory 27 clip, decode 24/27; **chưa push** |
| T098 data convention | P4 + P3 | Chờ xác nhận vùng `O` và variant (`data-convention.md` mục 8) rồi đóng băng |
| T040 typed API client | P5 → P2, P1 | `VERIFIED`, `[X]` — contract (P2) + tích hợp FastAPI thật (P5, P1) |

### Đã lên `main` theo micro-commit, checkpoint sau (chưa đóng)

| Task | Owner | Nội dung | Review |
|---|---|---|---|
| T029, T033 | P3 | GRU classifier + test | `VERIFIED`, `[X]` (P1) |
| T034–T036 | P3 | Loader, preset pilot/full, CLI train + xuất artifact | `VERIFIED`, `[X]` (P1; P2 xác nhận artifact) |
| T030, T037, T038 | P2 | Registry, adapter đặc trưng (parity 6/6), adapter GRU pilot/full, `POST /predictions` | `VERIFIED`, `[X]` |
| T041–T043, T046, T052 | P5 | State machine, màn hình kết quả, nối camera ↔ API, test luồng lỗi, thông báo lỗi tiếng Việt | `VERIFIED`, `[X]` (P1) |
| T065 | P3 + P2 | Benchmark latency/tài nguyên | Detector song song (P3) + bộ detector tạo sẵn (P2, `a214a3c`, −194 ms/request khi có khoảng nghỉ) P1_VERIFIED; local p95 3,26 s — **SC-002 vẫn trượt**; chờ production |
| T044, T045, T048–T050 | P2 | Luật ngưỡng, test lỗi, kiểm tra clip, cleanup | `VERIFIED`, `[X]` |
| T066, T072, T073 | P2 | Audit privacy + dọn clip tạm; 404/405/307 theo contract | `VERIFIED`, `[X]` (P1) |
| T064 | P2 | Pipeline clip đại diện + đổi artifact fixture/pilot/full | `VERIFIED`, `[X]` (P1) |
| T053 | P5 | Timeout/cancel/reset | `VERIFIED`, `[X]` (P1) |
| T074, T075 | P5 | Lỗi tương thích 404/405 + câu tiếng Việt riêng | `VERIFIED`, `[X]` (P1) |
| T100–T104 (US6) | P5 | Bản dịch trực tiếp + lịch sử trình duyệt 24 giờ | `VERIFIED`, `[X]` (P1) |
| T092 | P2 | Audit bảo mật, header, tắt docs, quét secret/dependency | `VERIFIED`, `[X]` (P1) |
| T068, T090 | P1 | Demo script; báo cáo kiến trúc (6 hành động đề xuất) | Bản đầu; T090 chờ P5 phần FE; chờ review |
| T027, T028, T031, T051 | P5 | Types, câu chữ, component test, kết quả bị từ chối | `VERIFIED`, `[X]` (P1) |
| T063 | P5 | Audit accessibility (Hiển, `b5ca295`, sửa recorder `a6d8a9d`) | `VERIFIED`, `[X]` (P1): 90/90 lặp 3 lần; trình đọc màn hình thật NOT_RUN |
| T088 | P5 + P1 | Audit UX (P1) + sửa a11y/bố cục 320 px (P5 `a40c68a`) | `VERIFIED`, `[X]` (review chéo) |
| T095 | P2 → P1 | Docker local (Tín bàn giao) | Local PASS sau bản vá P1 thêm `libegl1 libgles2` (thiếu → 500 mọi predict); API 2,86 GB, RAM đỉnh 962 MiB; chờ Tín review bản vá + AWS |
| T032, T047 | P1 | E2E camera giả + 3 backend FastAPI thật (`npm run test:e2e`, 6/6) | Chờ P5/P2 review |
| T069, T085, T087, T093 | P1 | README, ma trận rubric, hồ sơ sáng tạo/khả thi, tác động cộng đồng | Bản đầu đã push; chờ P2/P5 review |
| T089, T094 | P3 | Robustness, chi phí | P1_VERIFIED phần local/code; chờ artifact thật và production |
| T054, T057, T058 | P3 | Metric, release gate, CLI đánh giá | `VERIFIED`, `[X]` (P1) |
| T055, T060 | P2 | `health`, `model-info` | `VERIFIED`, `[X]` |
| T059 | P3 | Ghi `demoReady` theo gate full + phê duyệt lead `--approve-demo` | `VERIFIED`, `[X]` (P1) |
| T062 | P3 | Model card `docs/model-card.md` | P1_VERIFIED cấu trúc; giữ `[ ]` chờ metric thật |
| T083 | P3 | Pilot **Sốt–Cảm ơn** (`SOT`, `CAM_ON`) | **BLOCKED 0 clip**: manifest ghi `licenseStatus=unknown` trái quyết định khai quyền mức bộ dữ liệu (P4 sửa); split trống; schema v0.3 đã APPROVED |

Bản tự train (lead chốt 2026-11-07, sau khi khảo sát dataset/model công khai không phủ đủ 10 từ P0 và phần
lớn thiếu license): pilot thật cần T013 manifest + T098 đóng băng (P4), schema APPROVED sau review clip
đại diện (P3 → P1) và parity offline ↔ API trên clip có người.

### Quyết định lead 2026-11-07

- P0 = 10 ý nghĩa: Giấy tờ, Đau bụng, Sốt, Nhận, Bạn, Cảm ơn, Giúp đỡ, Xin lỗi, Đau đầu, Không; file raw
  `<VÙNG>_<NGHĨA>_<số video>.mp4` (ánh xạ ở `data-convention.md` mục 8).
- Full gate chia theo video gốc (`video-held-out`, FR-015), không tuyên bố unseen-signer; nguồn/giấy phép
  khai một lần ở mức bộ dữ liệu (video giáo dục công khai).
- Hạ tầng: hoàn thiện bản local trước. Kế hoạch AWS: `ap-southeast-2`, một EC2 + Elastic IP, ECR, S3,
  CloudFront, GitHub OIDC + SSM. Lần bootstrap OIDC ngày 2026-11-07 bị AWS-managed SCP explicit-deny
  `iam:CreateOpenIDConnectProvider`; stack `ROLLBACK_COMPLETE`, provider `DELETE_COMPLETE`, không có
  deploy role/credential/workload. Tín đã là team member project `Rubber Ducking`; chỉ dùng phiên
  Console/CloudShell cá nhân cho integration thủ công, không static access key. T091/T096 vẫn mở.
  Evidence: `docs/evidence/checkpoints/CP7/T096-aws-access-bootstrap.md`.
- `HealthResponse.modelVersion` optional + nullable theo OpenAPI.
- **US6 mới (FR-034–FR-036, SC-016, T100–T104, P5)**: bản dịch trực tiếp nối các kết quả `accepted` và lịch sử
  bản dịch lưu **chỉ trên trình duyệt** ít nhất 24 giờ; không lưu video/landmark, không lưu server, API không đổi.
  FR-017 sửa để chỉ loại lịch sử lưu server/đồng bộ thiết bị.

### Rủi ro đang theo dõi

- **Dữ liệu (rủi ro lớn nhất cho bản tự train)**: split `video-held-out` cần mỗi lớp có video ở cả
  train/validation/test; raw material hiện chỉ vài video mỗi nghĩa → cần tự quay bổ sung (planning floor
  20–30 mẫu/lớp, nhiều người ký) trước khi pilot có ý nghĩa.

- **Latency (rủi ro nghiêm trọng)**: T065 đo web p95 6,4 s, extract MediaPipe p50 4,6 s, GRU < 5 ms → SC-002
  (p95 ≤ 3 s) trượt gấp đôi. Nguyên nhân chính: tạo lại 3 detector mỗi clip và decode toàn bộ frame (review
  T014–T016 mục 3–4). P3 tối ưu, giữ parity offline ↔ API.
- RAM: đỉnh 480–600 MB/clip; host 1 GB quá sát — chọn instance sau khi đo trên Linux.
- Hiến pháp III còn yêu cầu báo cáo kết quả với người chưa xuất hiện; chờ lead quyết định sửa hiến pháp
  hay ghi giới hạn trong model card.
- Merge commit `fc7d606` (P3) trái quy tắc lịch sử thẳng; dùng `git pull --rebase origin main`.

## Status rules

- `LOCAL-DRAFT`: Có thay đổi cục bộ, chưa được lead duyệt/commit/push.
- `PUSHED`: Commit đã có trên `origin/main`, chưa chạy verification độc lập.
- `VERIFIED`: Gate đã được reviewer chạy lại và evidence khớp commit.
- `BLOCKED`: Có dependency cụ thể; ghi owner và điều kiện mở khóa.

## Member status

| Person | Owner | Canonical scope | Current status | Next gate |
|---|---|---|---|---|
| P1 | Huy | Spec Kit, integration queue, CI, verification, presentation | ACTIVE | Review T034–T036; bắt đầu E2E T032 (endpoint đã có); duyệt schema khi có clip |
| P2 | Tín | `services/inference-api/`, `infra/aws/`, security | ACTIVE | Factory GRU cho registry pilot/full (T037); T049 theo quy tắc P3; xác nhận artifact T036 |
| P3 | Cường | `ai/landmarks`, `ai/training`, `ai/evaluation` | ACTIVE | Gửi clip đại diện cho schema review; tối ưu latency decode; xác nhận T019 metadata |
| P4 | Quang | `data/`, `ai/dataset`, dataset card | ACTIVE | Push T013; xác nhận vùng `O`/variant rồi đóng băng T098 |
| P5 | Hiển | `apps/web/`, frontend tests/UX evidence | ACTIVE | Tích hợp T040 với endpoint thật; review T055/T060; sau đó US6 T100–T104 |

## External reference only

Code/test claims trong `7nghiep367` có thể giúp triển khai nhanh, nhưng không được tính là trạng thái
repo mới. Khi tái sử dụng, member log phải ghi legacy commit/path, task mới, diff đã review và test
trên checkpoint hiện tại.

## Immediate decision

CP1 chưa đóng cho đến khi P3/P5/P4 hoàn tất review tương ứng. CP2 micro-commit được phép tiếp tục
theo window, nhưng CP2 không được đóng trước khi CP1 `VERIFIED`. Không import full-code dump legacy.
