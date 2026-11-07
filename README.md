# ViSign source of truth

Repository chính thức: `https://github.com/HiImNVH/ViSign`.

`main` là nguồn sự thật cho yêu cầu, kế hoạch, contract, task và source code. Nhóm không dùng nhánh
vai trò dài hạn; mỗi thành viên làm trong clone cục bộ, ghi evidence tại `members/<person>/` và push
theo integration queue/checkpoint nhỏ.

## Start here

- Feature spec: `specs/001-vsl-recognition-mvp/spec.md`
- Technical plan: `specs/001-vsl-recognition-mvp/plan.md`
- Authoritative backlog: `specs/001-vsl-recognition-mvp/tasks.md`
- Rubric mapping: `docs/team/judging-criteria-mapping.md`
- Commit/push checkpoints: `docs/team/git-checkpoints.md`
- Team status: `docs/team/implementation-status.md`
- Member work logs: `members/README.md`

## Spec Kit

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-vsl-recognition-mvp'
```

## Integration rule

Mỗi checkpoint chỉ được push khi Huy mở integration window, owner pull/rebase `origin/main`, chạy
quality gate, cập nhật member evidence, commit nhỏ, pull/rebase lần cuối, rerun gate ảnh hưởng và push
thường. Cấm force-push, raw video/model/secret và full-code dump.

Chi tiết CP0–CP8 nằm trong `docs/team/git-checkpoints.md`.

## Pending conventions

- Quy ước đặt tên và chuẩn hóa file dữ liệu — T098.
- Quy ước API thống nhất FE-BE — T099.

CP2 không được đóng trước khi hai contract này được version, review và đồng bộ vào validator,
OpenAPI, client types và contract tests.
