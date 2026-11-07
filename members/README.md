# Member workspaces

Mỗi thư mục thành viên là nhật ký phối hợp, không phải bản sao source code.

| Member | Folder | Canonical ownership |
|---|---|---|
| P1 Huy | `members/p1-huy/` | Spec Kit, queue, CI coordination, verification, presentation |
| P2 Tín | `members/p2-tin/` | `services/inference-api/`, `infra/aws/`, security |
| P3 Cường | `members/p3-cuong/` | `ai/landmarks`, `ai/training`, `ai/evaluation` |
| P4 Quang | `members/p4-quang/` | `data/`, `ai/dataset`, dataset evidence |
| P5 Hiển | `members/p5-hien/` | `apps/web/`, frontend tests/UX evidence |

Mỗi README ghi current task, planned files, commands/results, evidence, blockers, handoff và pushed
commit. Shared files chỉ sửa trong integration window.

## Quy ước bắt buộc

- Commit theo `CPx Txxx(scope): outcome`; scope hợp lệ của từng người được khóa trong
  [`docs/team/git-checkpoints.md`](../docs/team/git-checkpoints.md).
- Mỗi commit cập nhật member README và một smoke evidence tạo từ
  [`checkpoint-evidence-template.md`](../docs/team/checkpoint-evidence-template.md).
- Evidence nằm tại `docs/evidence/checkpoints/CPx/Txxx-<owner>-smoke.md`; sau push bổ sung full SHA,
  commit link và Actions/report/cloud link nếu có.
- Member log không phải nơi chứa source thay thế; source luôn nằm ở canonical module.

## Khung bắt buộc trong mỗi member README

1. `Member profile`: owner, canonical path, scope và integration window.
2. `Current assignments`: task, trạng thái, planned paths, blocker và reviewer.
3. `Commit đang chuẩn bị`: đúng một candidate đang active, có proposed message và exact staged paths.
4. `Commit ledger`: lưu vĩnh viễn full SHA, GitHub link, gate, reviewer và trạng thái.
5. `Handoff`: input còn thiếu, rủi ro và người nhận tiếp theo.

Commit chưa push ghi `PENDING`; sau push phải ghi full SHA 40 ký tự và link
`https://github.com/HiImNVH/ViSign/commit/<sha>`. Không dùng short SHA làm bằng chứng cuối cùng.
Mọi candidate phải ghi kết quả đồng bộ `origin/main` ngay trước commit và ngay trước push; thiếu một
trong hai mốc thì không được commit/push.
