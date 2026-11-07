# CP5 T089 · P3/Cường

Candidate `CP5 T089(eval): add held-out robustness scoring`, baseline `c875ae5`.
Windows, CPython 3.12.15. Reviewer P1/Huy.

| Kiểm tra | Kết quả |
|---|---|
| `ruff check ai`, `python -m mypy ai/src ai/tests` | PASS, mypy 29 file |
| `pytest ai/tests -q -rs` | 83 pass, gồm 4 test T089. 1 skip do quyền symlink |
| `pytest services/inference-api/tests tests/contract tests/integration -q -rs` | 395 pass, có clip tham chiếu cho T064 và parity |
| `python -m visign_ai.evaluation.robustness --probes PATH/probes.csv --output PATH/robustness.json` | Exit 0. Hai response blank từ smoke T065 → 2 quyết định từ chối, 0 false accept, 0 lỗi. Chỉ áp dụng cho hai clip trống và GRU tổng hợp |
| OOD, bias và độ ổn định trên artifact VSL thật | NOT_RUN. Chờ artifact và tập probe đã audit |

[Protocol và cách diễn giải](../../../ai-safety-report.md). T089 mở, chờ review.

## Independent review — P1/Huy

Review `2026-11-08T00:37:34+07:00` trên `dc9e357` (P1 review theo uỷ quyền của Huy). AI 79 passed; Ruff, mypy PASS. Cơ chế chấm robustness và test đã có; phần đo OOD/bias/độ ổn định trên
artifact VSL thật là `NOT_RUN`.

**Reviewer result**: `P1_VERIFIED` phần code/test; T089 giữ `[ ]` đến khi có báo cáo trên artifact thật.
