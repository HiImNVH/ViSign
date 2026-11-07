# ViSign implementation tracking snapshot

Snapshot date: 2026-11-07

Repository: `HiImNVH/ViSign`

Source of truth: `specs/001-vsl-recognition-mvp/tasks.md`

## Current baseline

- Remote repository trống trước CP0; baseline hiện đã có trên `origin/main`.
- CP0 Spec Kit/rubric/checkpoint/member files đã push tại commit
  `5102bbbbe7efcf327a64477051bfc6137e9b5bce`.
- CP0 đang ở trạng thái `PUSHED`, chờ P2 chạy verification độc lập trước khi đổi thành `VERIFIED`.
- Application code legacy chưa được nhập; task checkbox chưa đóng trước independent review.

## Status rules

- `LOCAL-DRAFT`: Có thay đổi cục bộ, chưa được lead duyệt/commit/push.
- `PUSHED`: Commit đã có trên `origin/main`, chưa chạy verification độc lập.
- `VERIFIED`: Gate đã được reviewer chạy lại và evidence khớp commit.
- `BLOCKED`: Có dependency cụ thể; ghi owner và điều kiện mở khóa.

## Member status

| Person | Owner | Canonical scope | Current status | Next gate |
|---|---|---|---|---|
| P1 | Huy | Spec Kit, integration queue, CI, verification, presentation | PUSHED | P2 verify CP0 từ `origin/main` |
| P2 | Tín | `services/inference-api/`, `infra/gcp/`, security | PLANNED | CP1 toolchain, T099 API convention; AI-backend contract đã xác nhận |
| P3 | Cường | `ai/landmarks`, `ai/training`, `ai/evaluation` | PLANNED | Representative-clip review cho schema v0.3 |
| P4 | Quang | `data/`, `ai/dataset`, dataset card | BLOCKED/PARTIAL | Lead gửi T098 data convention |
| P5 | Hiển | `apps/web/`, frontend tests/UX evidence | PLANNED | CP1 web project, T099 API convention |

## External reference only

Code/test claims trong `7nghiep367` có thể giúp triển khai nhanh, nhưng không được tính là trạng thái
repo mới. Khi tái sử dụng, member log phải ghi legacy commit/path, task mới, diff đã review và test
trên checkpoint hiện tại.

## Immediate decision

Không nhập application code cho đến khi CP0 được reviewer xác nhận. Sau đó mở CP1 theo từng module,
không import full-code dump từ repository legacy.
