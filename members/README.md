# Member workspaces

Mỗi thư mục thành viên là nhật ký phối hợp, không phải bản sao source code.

| Member | Folder | Canonical ownership |
|---|---|---|
| P1 Huy | `members/p1-huy/` | Spec Kit, queue, CI coordination, verification, presentation |
| P2 Tín | `members/p2-tin/` | `services/inference-api/`, `infra/gcp/`, security |
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
