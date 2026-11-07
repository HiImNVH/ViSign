# CP5 T054 và T057 · P3/Cường

Owner P3/Cường. Reviewer P1/Huy. Baseline đã đồng bộ bằng git pull --rebase origin main tại 7315314.

## Kết quả

- T057 tính accuracy, Macro-F1, precision/recall, confusion matrix và số clip theo nghĩa. Báo cáo có số signer đã biết, số clip thiếu signer và p50/p95 khi có số đo. Mẫu bị từ chối vẫn được tính và có cột riêng trong ma trận.
- T054 xác nhận fixture/pilot luôn trượt full gate, kể cả khi metric tổng hợp đạt 100%. Full cần đúng 10 nghĩa P0, có mẫu test ở mỗi nghĩa, audit split FR-015 đạt, Macro-F1 ≥ 0.80 và recall từng nghĩa ≥ 0.65.
- Cách tính tham khảo checkout 7nghiep367 tại 267419b, điều chỉnh split theo FR-015 của repo ViSign.

| Gate cục bộ | Kết quả |
|---|---|
| python -m ruff check --no-cache ai | PASS |
| python -m mypy ai/src ai/tests | PASS · 25 file |
| python -m pytest ai/tests -q -rs | 75 passed, gồm 15 test mới. 1 skipped do Windows không cho tạo symlink |
| python -m pytest services/inference-api/tests tests/contract -q -rs | 211 passed. 1 skipped do môi trường API thiếu MediaPipe |

Các metric trong test dùng dữ liệu tổng hợp. Latency p50/p95 của bộ đánh giá chưa xác nhận mục tiêu end-to-end SC-002.

## Handoff

T058 cần chạy dự đoán trên tập test, audit clip chung video gốc và xuất JSON, ảnh confusion matrix cùng provenance. T059 còn phần ghi metadata và nối kết quả audit T058 với demoReady. Đánh giá model thật cần manifest đã audit và schema được duyệt.

**Reviewer result** PENDING

## Independent review — P1/Huy

Huy (P1) review và kết luận **đạt**; ghi nhận `2026-11-07T22:06:58+07:00` trên `630f9ab`. Gate tái chạy: AI 73 passed, 5 skipped (thiếu fixture clip local); API + contract 332 passed, 2 skipped; web lint, typecheck, Vitest 88/88, build PASS; CI `quality.yml` xanh.

**Reviewer result**: `P1_VERIFIED` → T054, T057 `[X]`.
