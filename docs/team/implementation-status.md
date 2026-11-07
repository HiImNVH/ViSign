# ViSign implementation tracking snapshot

Snapshot date: 2026-11-07

Repository: `HiImNVH/ViSign`

Source of truth: `specs/001-vsl-recognition-mvp/tasks.md`

## Current baseline

Cập nhật `2026-11-07T19:06:13+07:00` trên `origin/main` `9abd2f3`.

### Checkpoint

| CP | Trạng thái | Ghi chú |
|---|---|---|
| CP0 | `VERIFIED` | Spec Kit, rubric, member/checkpoint docs — `docs/evidence/checkpoints/CP0/` |
| CP1 | `VERIFIED` | T001–T008, T086 `[X]`; closure trong `docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md` |
| CP2 | `OPEN` | Đóng khi đủ bảng "CP2 còn mở" bên dưới |
| CP3 | `NOT OPEN` | T039 `[X]`; T030/T037/T040 trên `main` theo micro-commit; không đóng trước CP2 |
| CP7 | `PARTIAL` | T091 quality CI chạy trên mọi push; AWS (`infra/aws/`) là kế hoạch, chưa triển khai |

### CP2 còn mở

| Hạng mục | Owner → reviewer | Trạng thái |
|---|---|---|
| T099 FE–BE API convention | P2 → P1 lead, P5 consumer | `VERIFIED`, `[X]` |
| T024–T025 temporary clip | P2 → P1 | `VERIFIED`, `[X]` |
| T021 error catalog, T023 logging | P2 → P1, P5 | `VERIFIED`, `[X]` |
| T019 model metadata | P2 → P1, P3 | P1_VERIFIED; chờ P3 xác nhận metadata/`demoReady` (T059) |
| T020, T022, T026 | P2 → P1, P5 | `VERIFIED`, `[X]` — fix của P2 đã được P1 kiểm chứng; P5 kiểm lại độc lập trên `bb40476` (179 passed, 1 skipped) và ghi `P5_VERIFIED` trong evidence CP2 |
| T014–T016 shared pipeline | P3 → P1, P2 | Code đạt; schema `visign-xy-32-v0.3-draft` chờ representative-clip review (P3 gửi clip → P1 duyệt) |
| T017 batch extraction CLI | P3 → P2, P1 | P2 `VERIFIED`; lỗi `--help` trên Windows đã được P1 sửa + test, chờ P3 review bản sửa |
| T013 registry 10 meaning P0 | P4 → P3, P1 | Hoàn thành local trên máy P4, **chưa push** |
| T098 data convention | P4 + P3 | Chờ xác nhận vùng `O` và variant (`data-convention.md` mục 8) rồi đóng băng |
| T040 typed API client | P5 → P2 | P2_VERIFIED phần contract; tích hợp endpoint thật chờ T038/T060 |

### Quyết định lead 2026-11-07

- P0 = 10 ý nghĩa: Giấy tờ, Đau bụng, Sốt, Nhận, Bạn, Cảm ơn, Giúp đỡ, Xin lỗi, Đau đầu, Không; file raw
  `<VÙNG>_<NGHĨA>_<số video>.mp4` (ánh xạ ở `data-convention.md` mục 8).
- Full gate chia theo video gốc (`video-held-out`, FR-015), không tuyên bố unseen-signer; nguồn/giấy phép
  khai một lần ở mức bộ dữ liệu (video giáo dục công khai).
- Hạ tầng: hoàn thiện bản local trước. Kế hoạch AWS: `ap-southeast-2`, một EC2 + Elastic IP, ECR, S3,
  CloudFront, GitHub OIDC + SSM; chưa tạo tài nguyên.
- `HealthResponse.modelVersion` optional + nullable theo OpenAPI.

### Rủi ro đang theo dõi

- Latency: benchmark T095 đo 2,4–3,4 s/clip trên Windows **chưa gồm GRU**, sát/vượt SC-002 p95 ≤ 3 s.
  P3 xem lại decode toàn bộ frame trước khi lấy mẫu (review T014–T016 mục 3).
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
| P1 | Huy | Spec Kit, integration queue, CI, verification, presentation | ACTIVE | Điều phối đóng CP2; review T017; duyệt schema khi có clip; T085/T087/T093 |
| P2 | Tín | `services/inference-api/`, `infra/aws/`, security | ACTIVE | T020/T022/T026 xong; tiếp T038/T060 endpoint để mở E2E |
| P3 | Cường | `ai/landmarks`, `ai/training`, `ai/evaluation` | ACTIVE | Review fix `--help` T017 của P1; gửi clip đại diện; tối ưu latency decode; xác nhận T098 |
| P4 | Quang | `data/`, `ai/dataset`, dataset card | ACTIVE | Push T013; xác nhận vùng `O`/variant rồi đóng băng T098 |
| P5 | Hiển | `apps/web/`, frontend tests/UX evidence | ACTIVE | T040 chờ review; tiếp CP3 khi có endpoint T038/T060 |

## External reference only

Code/test claims trong `7nghiep367` có thể giúp triển khai nhanh, nhưng không được tính là trạng thái
repo mới. Khi tái sử dụng, member log phải ghi legacy commit/path, task mới, diff đã review và test
trên checkpoint hiện tại.

## Immediate decision

CP1 chưa đóng cho đến khi P3/P5/P4 hoàn tất review tương ứng. CP2 micro-commit được phép tiếp tục
theo window, nhưng CP2 không được đóng trước khi CP1 `VERIFIED`. Không import full-code dump legacy.
