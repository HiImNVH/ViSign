# CP3 T029, T033 · P3/Cường

Baseline origin/main: bf2565862019b7cb635a53363748017c8e6ee2fd. Candidate LOCAL-DRAFT, chờ push và P1/Huy, P2/Tín review.

GRU nhận batch landmark có padding và độ dài từng chuỗi. Packed sequence bỏ qua padding. Logits giữ thứ tự mẫu trong batch, còn caller quản lý thứ tự lớp. Đối chiếu GRU legacy tại commit 267419b của 7nghiep367, ai/src/visign_ai/training/gru_classifier.py. Giữ cấu trúc GRU + linear, thêm type hint và kiểm tra đầu vào.

Test dùng tensor tổng hợp 32×234 cho pilot 2/3 lớp và full 10 lớp. Bao phủ batch không sắp xếp, padding, forward tái lập với seed và độ dài sai.

| Gate cục bộ | Kết quả |
|---|---|
| Pytest GRU | 9 passed |
| Pytest AI có fixture browser/detector | 42 passed, 1 skipped vì quyền symlink Windows |
| Pytest API và contract | 179 passed, 1 skipped |
| Ruff và mypy AI | PASS |

T034 loader, T035 config và T036 train CLI là các bước sau. Chưa huấn luyện hoặc đánh giá nhận diện trên dữ liệu chính thức.

## Independent review — P1/Huy

Huy (P1) review và kết luận **đạt**; ghi nhận `2026-11-07T22:06:58+07:00` trên `630f9ab`. Gate tái chạy: AI 73 passed, 5 skipped (thiếu fixture clip local); API + contract 332 passed, 2 skipped; web lint, typecheck, Vitest 88/88, build PASS; CI `quality.yml` xanh.

**Reviewer result**: `P1_VERIFIED` → T029, T033 `[X]`.
