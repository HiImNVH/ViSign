# Kế hoạch ban đầu ViSign trên repository mới

Ngày chốt dự thảo: 2026-11-07

Repository: `https://github.com/HiImNVH/ViSign`

Trạng thái: local draft, chờ lead xác nhận trước commit/push CP0.

## Nguyên tắc chuyển dự án

- Repo mới bắt đầu trống; `7nghiep367` chỉ là nguồn tham khảo code/evidence.
- Không import một lần toàn bộ application code hoặc lịch sử nhánh vai trò.
- Source được đưa sang theo T-task và checkpoint nhỏ, có test/evidence.
- Mỗi người có clone cục bộ và `members/pN-name/`; source chính vẫn ở module canonical.
- Tích hợp trực tiếp trên `main` nhưng push tuần tự qua integration queue do Huy điều phối.

## Checkpoint

| CP | Nội dung | Owner chính | Điều kiện push |
|---|---|---|---|
| CP0 | Spec Kit, rubric, members, Git rules | Huy | Lead duyệt tài liệu; validate Spec Kit |
| CP1 | Monorepo/toolchain rỗng | Huy + owners | Install/lint/test/build tối thiểu pass |
| CP2 | Data/extractor/API foundation | Quang, Cường, Tín, Hiển | T098–T099 contract freeze; unit/contract pass |
| CP3 | Camera→fixture API→result | Hiển, Tín, Huy | Happy-path E2E pass |
| CP4 | Reject/error/privacy/routing | Tín, Hiển, Huy | Negative E2E + privacy/security pass |
| CP5 | Dataset/model/evaluation/full gate | Quang, Cường | Reproducible reports; full gate evidence |
| CP6 | Admin internal tool | Tín, Hiển | Auth/cleanup/concurrency tests pass |
| CP7 | CI/security/cost/community/cloud | Huy, Tín, Cường, Hiển | CI pass; HTTPS production smoke/rollback pass |
| CP8 | Nghiệm thu và trình bày | Huy + toàn nhóm | Rubric 100% mapped; rehearsal/Q&A complete |

## Ưu tiên ngay sau CP0

1. Chờ lead bàn giao data filename/normalization convention và FE-BE API convention.
2. Không chờ hai convention để tạo toolchain rỗng, member logs và CI skeleton.
3. Chỉ tái sử dụng code legacy khi task mô tả đúng file, review diff và test đỏ→xanh.
4. Cloud/CI/cost/community evidence là commitment do rubric, không còn là M2.

## Completion rule

Task chỉ chuyển `[x]` khi code/evidence đã có trên `origin/main`, gate pass sau rebase cuối và
`members/<owner>/README.md` ghi commit SHA cùng handoff. Code chỉ tồn tại ở máy cá nhân hoặc legacy
repo không được tính hoàn thành.
