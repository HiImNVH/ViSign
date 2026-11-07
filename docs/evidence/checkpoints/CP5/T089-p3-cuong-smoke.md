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
