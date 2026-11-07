# ViSign implementation tracking snapshot

Snapshot date: 2026-11-07

Repository: `HiImNVH/ViSign`

Source of truth: `specs/001-vsl-recognition-mvp/tasks.md`

## Current baseline

- Remote repository trống trước CP0; baseline hiện đã có trên `origin/main`.
- CP0 Spec Kit/rubric/checkpoint/member files đã push tại commit
  `5102bbbbe7efcf327a64477051bfc6137e9b5bce`.
- CP0 đã `VERIFIED`: P2 tái lập 5/5 gate trên `22226b25d17e70ce48b153914d7eee1e15e8d3f4`; ghi chú
  không chặn (owner T001–T007, owner kép T090, link legacy hỏng) nằm trong
  `docs/evidence/checkpoints/CP0/T085-T086-p1-huy-smoke.md`.
- Application code legacy chưa được nhập; task checkbox chưa đóng trước independent review.
- CP1 toolchain T001–T007 đã push tại `84958a34c44bc5e1d7e655cae6b6ed85e07d0c08`; P1 đã tái lập
  API/AI/Web gates. T003 còn chờ P3 review, T004/T006 còn chờ P5 review.
- T008 raw-material/rights guidance đã push tại `189d34bcd4875752dab460716756aa8239996f9f`; chờ P4 review.
- CP2 T019–T021 (API domain models) đã push tại `9b888a182592a2739b665a287ec37a8a4aa9f8f3`
  (evidence link `5dc97a6`); P1 đã tái lập gate (44 passed, Ruff, mypy); chờ P3 review metadata,
  P5 review response/error shape.
- CP2 T014–T016 (shared WebM feature pipeline) của P3 đã push tại `865547e`; chờ P2/P1 review và
  representative-clip review cho schema `visign-xy-32-v0.3-draft`.
- Lead đã bàn giao quy ước: [fe-be-api-convention.md](fe-be-api-convention.md) cho T099 và
  [data-convention.md](data-convention.md) cho T098. Owner xác nhận các quyết định bổ sung rồi đóng băng.

## Status rules

- `LOCAL-DRAFT`: Có thay đổi cục bộ, chưa được lead duyệt/commit/push.
- `PUSHED`: Commit đã có trên `origin/main`, chưa chạy verification độc lập.
- `VERIFIED`: Gate đã được reviewer chạy lại và evidence khớp commit.
- `BLOCKED`: Có dependency cụ thể; ghi owner và điều kiện mở khóa.

## Member status

| Person | Owner | Canonical scope | Current status | Next gate |
|---|---|---|---|---|
| P1 | Huy | Spec Kit, integration queue, CI, verification, presentation | ACTIVE | Thu xác nhận quy ước T098/T099; review T014–T016; T091 quality CI |
| P2 | Tín | `services/inference-api/`, `infra/gcp/`, security | PARTIAL_VERIFIED / REVIEW | CP1 chờ P3/P5; CP2 T019–T021 chờ review; tiếp T022–T023 local; T099 mở — xác nhận quy ước API |
| P3 | Cường | `ai/landmarks`, `ai/training`, `ai/evaluation` | REVIEW | Review T003; T014–T016 chờ review; xác nhận data-convention D1–D4 |
| P4 | Quang | `data/`, `ai/dataset`, dataset card | REVIEW | Review T008; T098 mở — xác nhận data-convention D1–D4 rồi đóng băng |
| P5 | Hiển | `apps/web/`, frontend tests/UX evidence | REVIEW | Review T004/T006; xác nhận API convention D1–D4 với Tín |

## External reference only

Code/test claims trong `7nghiep367` có thể giúp triển khai nhanh, nhưng không được tính là trạng thái
repo mới. Khi tái sử dụng, member log phải ghi legacy commit/path, task mới, diff đã review và test
trên checkpoint hiện tại.

## Immediate decision

CP1 chưa đóng cho đến khi P3/P5/P4 hoàn tất review tương ứng. CP2 micro-commit được phép tiếp tục
theo window, nhưng CP2 không được đóng trước khi CP1 `VERIFIED`. Không import full-code dump legacy.
