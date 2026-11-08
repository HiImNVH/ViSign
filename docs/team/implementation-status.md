# ViSign implementation tracking snapshot

Snapshot date: 2026-11-07

Repository: `HiImNVH/ViSign`

Source of truth: `specs/001-vsl-recognition-mvp/tasks.md`

## Current baseline

Cập nhật `2026-11-08T12:00:00+07:00` trên `origin/main` (83/112 task).

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
| T009–T013 dataset entities/schema/validator/registry | P4 → P1 | `VERIFIED`, `[X]` (P1, lead xác nhận 2026-11-08): validator chạy trên manifest v5 101 clip, 0 lỗi |
| T061 dataset card | P4 → P1, P3 | Gói local 2026-11-08 (chưa push) **P1 `CHANGES_REQUESTED`**: `docs/dataset-card.md` vẫn là snapshot 27 clip (07/11) trong khi đã có bản 100 clip v3 và ghi chú v4 101 clip; card 27 ghi 24 clip website/3 tự quay và `licenseStatus=unknown` trái quyết định khai quyền mức dataset, còn manifest pilot T076 ghi cả 15 là tự quay; chưa có mục pilot Giấy tờ/Nhận 15 clip; link `../../Audit-100vid` ra ngoài repo; checksum `README.md` lệch. Điểm tốt: nêu rõ bias/khoảng trống, 5/5 test coverage đạt |
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
| T068 | P1 | Demo script | Bản đầu; chờ P2/P5 review |
| T090 | P1 + P5 | Báo cáo kiến trúc (P1 §1–6, P5 §7 FE `a4eb02c`) | `VERIFIED`, `[X]` (review chéo); P5 làm FE-T090-01..06, ưu tiên lỗi mất lịch sử khi cleanup ghi lỗi |
| T027, T028, T031, T051 | P5 | Types, câu chữ, component test, kết quả bị từ chối | `VERIFIED`, `[X]` (P1) |
| T063 | P5 | Audit accessibility (Hiển, `b5ca295`, sửa recorder `a6d8a9d`) | `VERIFIED`, `[X]` (P1): 90/90 lặp 3 lần; trình đọc màn hình thật NOT_RUN |
| T088 | P5 + P1 | Audit UX (P1) + sửa a11y/bố cục 320 px (P5 `a40c68a`) | `VERIFIED`, `[X]` (review chéo) |
| T095 | P2 → P1 | Docker local (Tín bàn giao) | Local PASS sau bản vá P1 thêm `libegl1 libgles2` (thiếu → 500 mọi predict); API 2,86 GB, RAM đỉnh 962 MiB; chờ Tín review bản vá. **AWS (2026-11-08)**: Free Plan, credit 100 USD; Budget `visign-monthly-credit-guard` (5/20/50 USD); stack `visign-storage` (ECR + S3) tạo xong; image `3b29d4a2cec1` + artifact fixture đã đẩy; **EC2 chạy artifact pilot Giấy tờ/Nhận** qua HTTPS tạm (Cloudflare Quick Tunnel), webcam thật end-to-end đạt; processing 4–4,7 s/clip trên t3.small, **2,5–3,4 s trên c7i-flex.large** (đổi cho ngày demo) → round-trip 3,9–5,4 s, vẫn trượt SC-002; CloudFront chờ AWS xác minh ([báo cáo](../deployment-report.md)) |
| T032, T047 | P1 | E2E camera giả + 3 backend FastAPI thật (`npm run test:e2e`, 6/6) | Chờ P5/P2 review |
| T069, T085, T087, T093 | P1 | README, ma trận rubric, hồ sơ sáng tạo/khả thi, tác động cộng đồng | Bản đầu đã push; chờ P2/P5 review |
| T089, T094 | P3 | Robustness, chi phí | P1_VERIFIED phần local/code; chờ artifact thật và production |
| T054, T057, T058 | P3 | Metric, release gate, CLI đánh giá | `VERIFIED`, `[X]` (P1) |
| T055, T060 | P2 | `health`, `model-info` | `VERIFIED`, `[X]` |
| T059 | P3 | Ghi `demoReady` theo gate full + phê duyệt lead `--approve-demo` | `VERIFIED`, `[X]` (P1) |
| T062 | P3 | Model card `docs/model-card.md` | P1_VERIFIED cấu trúc; đã ghi metric pilot nội bộ, chờ review cập nhật và đánh giá full |
| T081, T082 | P5 | Giao diện admin `/admin/train-model` (`a498da5`, `c0d598f`) | `VERIFIED`, `[X]`: T082 smoke với backend admin thật (job thật 15/15 clip) |
| T091 | P1 | CI quality gate | Thêm job `docker` (build 2 image, nạp 3 detector MediaPipe trong container chỉ đọc, smoke Compose 14/14 qua nginx), xanh trên `bed64a9`; OIDC deploy bị SCP Free Plan chặn. Chờ P2 review |
| T084 | P1 | Nghiệm thu ranh giới user/admin, secret, retention | `VERIFIED`, `[X]`: public + admin đạt ([admin-acceptance.md](../admin-acceptance.md)) |
| T078–T080 | P2 | Admin API opt-in (`70f2601`) | `VERIFIED`, `[X]` (P1): 404 khi tắt, 401, 409, cleanup, inspect ZIP trong Docker; runner pilot P3 còn thiếu (prepare 503) |
| T018, T056 | P4 | Split theo video + regression leakage | `VERIFIED`, `[X]` (P1 tích hợp theo allowlist); T098 `CHANGES_REQUESTED` nhỏ (cho phép trống `sourceUri`) |
| T105–T108 | P1 (tiếp quản một phần P3) | **Dịch trực tiếp**: MediaPipe trên trình duyệt phát hiện người/mặt/tay, tự cắt và tự gửi từng ký hiệu, 11 trạng thái (`de14b19`) | Code + test xong (unit 191, Playwright 75, E2E 6/6, CI xanh), đã deploy AWS `d7637107d8be`; **chờ P5 review** (code P1 viết) và T108 smoke webcam thật |
| T036 (bổ sung) | P1 (tiếp quản một phần P3) | Trọng số nhóm điểm tay 0,7 / mặt 0,2 / vai 0,1 trong đầu vào GRU (`f6d61a2`), mặc định ở `pilot-gru.yaml`/`p0-gru.yaml`; artifact lưu `feature_scale`, API nạp được cả model cũ | AI 188, API 408 test đạt, CI xanh; train lại pilot: test 25% / Macro-F1 0,33 như cũ (4 clip không đủ đo); **chờ P3 review** |
| T109–T113 | P2, P3, P5 | Convergence 2026-11-08 (Spec Kit): ~~T109~~ **xong**: `model-info.meaningDisplayTexts` + UI hiện "Giấy tờ (giấy), Nhận"; ~~T110 runner pilot~~ **xong** (`[X]`, P1 tiếp quản P3); T111 giới hạn file admin 10 MiB (P5); ~~T112~~ **xong**; ~~T113~~ **xong**: sửa rò rỉ RAM bằng `MALLOC_ARENA_MAX=2` (8 client: 1.523 → 929 MiB, 0 lần chạm trần) | Mới, chưa bắt đầu |
| T083 | P3 → P1 | Pilot Giấy tờ / Nhận | `VERIFIED`, `[X]`: chạy hết luồng admin thật (prepare 15/15 → train → complete), accuracy 0,25 / Macro-F1 0,33, `demoReady=false` |

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
