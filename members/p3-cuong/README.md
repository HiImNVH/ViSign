# P3 Cường - AI/Training/Evaluation

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P3` |
| Current member | Cường |
| Role | AI preprocessing, training và evaluation |
| Canonical ownership | `ai/landmarks/`, `ai/training/`, `ai/evaluation/` |
| Allowed commit scopes | `ai`, `extractor`, `train`, `eval`, `model` |
| Current checkpoint | `CP5` · T059 VERIFIED, T062 chờ metric thật, T065 P1_VERIFIED phần local |
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T003 / CP1` | `VERIFIED` | `ai/pyproject.toml` do Tín tạo | Ruff, mypy và 8 import đạt. Pytest 15 passed, 5 skipped. [Review độc lập](../../docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md#independent-review--p3cường) | P3/Cường |
| `T014-T016 / CP2` | `REVIEW` | decoder, extractor, transform, schema và tests | Parity qua T037 đã đạt. Chờ Huy duyệt schema từ clip đại diện | P2/Tín và P1/Huy |
| `T017 / CP2` | `VERIFIED` | CLI trích landmark từ danh sách sampleId/rawPath | D1–D4 đã xác nhận cùng Quang. CI xanh. Test tự động đã push ở 57311bf, 13 pass/1 skip local; P2 đã duyệt test batch; P3 review bản sửa --help bb40476, đạt trên cp1252 và UTF-8; T010 và duyệt schema là gate dữ liệu chính thức | P2/Tín và P1/Huy |
| `T029, T033 / CP3` | `VERIFIED` | Test GRU và classifier packed sequence | P1 đã xác minh trên main | P1/Huy, P2/Tín |
| `T034 / CP3` | `VERIFIED` | NPZ loader và batching theo class map | P1 đã xác minh trên main | P1/Huy, P2/Tín |
| `T035 / CP3` | `VERIFIED` | Cấu hình seed GRU cho pilot/full | P1 đã xác minh trên main | P1/Huy, P2/Tín |
| `T036 / CP3` | `VERIFIED` | CLI train và artifact model | P1 đã xác minh. T037 đã smoke artifact pilot/full tổng hợp | P1/Huy, P2/Tín |
| `T054, T057 / CP5` | `VERIFIED` | Metric theo nghĩa và test full gate | 15 test mới đạt. [Evidence](../../docs/evidence/checkpoints/CP5/T054-T057-p3-cuong-smoke.md) | P1/Huy |
| `T058 / CP5` | `VERIFIED` | CLI đánh giá, JSON, ảnh confusion matrix và provenance | Gate cục bộ đạt. [Evidence](../../docs/evidence/checkpoints/CP5/T058-p3-cuong-smoke.md) | P1/Huy, P4/Quang |
| `T059 / CP5` | `VERIFIED` | Metadata writer và full release gate | Gate cục bộ đạt. [Evidence](../../docs/evidence/checkpoints/CP5/T059-p3-cuong-smoke.md) | P1/Huy, P2/Tín |
| `T062 / CP5` | `PUSHED` | [Model card](../../docs/model-card.md) | P1 duyệt cấu trúc. Pilot đã chốt Sốt–Cảm ơn. Chờ metric VSL thật | P1/Huy |
| `T065 / CP5` | `P1_VERIFIED local` | [Benchmark](../../docs/performance-report.md) | Đã push `cc9a214`. Candidate giữ parity, web local p95 5,87 s. Cần tối ưu tiếp và đo production | P1/Huy, P2/Tín |
| `T083 / CP5` | `BLOCKED` | [Preflight Sốt–Cảm ơn](../../docs/pilot-report.md) | 0/6 clip đủ điều kiện. Chờ T076, schema APPROVED và T078–T082 | P1/Huy, P4/Quang |
| `T089 / CP5` | `LOCAL-DRAFT` | [Scorer và báo cáo robustness](../../docs/ai-safety-report.md) | Đã kiểm scorer và hai clip trống. Chờ probe audit và artifact VSL thật | P1/Huy |
| `T094 / CP5` | `LOCAL-DRAFT` | [Tài nguyên và chi phí](../../docs/cost-report.md) | Đã đo local và lập dự toán Sydney. Chờ Linux/EC2 và Huy/Tín chốt budget | P1/Huy, P2/Tín |

## Commit gần nhất

| Field | Value |
|---|---|
| Task/checkpoint | `CP5 / T065` · đã push |
| Commit message | `CP5 T065(eval): benchmark inference latency and resources` |
| Smoke evidence | [T065](../../docs/evidence/checkpoints/CP5/T065-p3-cuong-smoke.md) |
| Full SHA | cc9a2144723a029b7b1b1973a475d202184259c1 |
| Push status | `PUSHED` · local đã được P1 review tại `cfa9f04` |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T014-T016` | Shared WebM feature pipeline | `CP2 T014-T016(extractor): add shared WebM feature pipeline` | 865547ebe637da010ac7c953bcce38389ecca831 | [Commit 865547e](https://github.com/HiImNVH/ViSign/commit/865547ebe637da010ac7c953bcce38389ecca831) | PASS cục bộ · 20 test AI | P2/Tín, P1/Huy | PUSHED · P1/P2 đã review code, schema còn draft |
| `CP2/T017` | Batch extraction CLI | `CP2 T017(extractor): add batch landmark extraction CLI` | 4a5aa5295702197d9509302d4bcf07a1dcd0d154 | [Commit 4a5aa52](https://github.com/HiImNVH/ViSign/commit/4a5aa5295702197d9509302d4bcf07a1dcd0d154) | [PASS cục bộ](../../docs/evidence/checkpoints/CP2/T017-p3-cuong-smoke.md) | P2/Tín, P1/Huy | PUSHED · [CI bản sửa bc642c1](https://github.com/HiImNVH/ViSign/actions/runs/42364019259) đạt · VERIFIED · P2 review 57311bf, P3 review --help bb40476 |
| `CP3/T029,T033` | GRU classifier and contract tests | `CP3 T029,T033(train): add packed GRU classifier and tests` | 2a3769d6dd3b86441abad5f84295dcc47d76ebb4 | [Commit 2a3769d](https://github.com/HiImNVH/ViSign/commit/2a3769d6dd3b86441abad5f84295dcc47d76ebb4) | [PASS cục bộ](../../docs/evidence/checkpoints/CP3/T029-T033-p3-cuong-smoke.md) | P1/Huy, P2/Tín | VERIFIED |
| `CP3/T034` | NPZ sequence loader and batching | `CP3 T034(train): load landmark sequences in class map order` | 6912242c7f1cb69f9f476c25996c89ef2e1b7ec3 | [Commit 6912242](https://github.com/HiImNVH/ViSign/commit/6912242c7f1cb69f9f476c25996c89ef2e1b7ec3) | [PASS cục bộ](../../docs/evidence/checkpoints/CP3/T034-p3-cuong-smoke.md) | P1/Huy, P2/Tín | VERIFIED |
| `CP3/T035` | Seeded pilot/full GRU presets | `CP3 T035(train): add reproducible pilot and full GRU presets` | 7a8c27717e6cf75482c4b1a0c4dbf0076244f4ad | [Commit 7a8c277](https://github.com/HiImNVH/ViSign/commit/7a8c27717e6cf75482c4b1a0c4dbf0076244f4ad) | [PASS cục bộ](../../docs/evidence/checkpoints/CP3/T035-p3-cuong-smoke.md) | P1/Huy, P2/Tín | VERIFIED |
| `CP3/T036` | Reproducible GRU training CLI | `CP3 T036(train): add GRU training CLI and artifact export` | 15384cc10f6104bb727adbf33697966e239f2522 | [Commit 15384cc](https://github.com/HiImNVH/ViSign/commit/15384cc10f6104bb727adbf33697966e239f2522) | [PASS cục bộ](../../docs/evidence/checkpoints/CP3/T036-p3-cuong-smoke.md) | P1/Huy, P2/Tín | VERIFIED |
| `CP5/T054,T057` | Meaning metrics and full gate tests | `CP5 T054,T057(eval): add meaning metrics and release gate tests` | d92436a67fceb4bedf62f750ff257f5904065cca | [Commit d92436a](https://github.com/HiImNVH/ViSign/commit/d92436a67fceb4bedf62f750ff257f5904065cca) | [PASS cục bộ](../../docs/evidence/checkpoints/CP5/T054-T057-p3-cuong-smoke.md) | P1/Huy | VERIFIED |
| `CP5/T058` | Held-out evaluation CLI | `CP5 T058(eval): export held-out metrics and confusion matrix` | 29c0464f55f6ae4e30630e5eeea31d789701cc82 | [Commit 29c0464](https://github.com/HiImNVH/ViSign/commit/29c0464f55f6ae4e30630e5eeea31d789701cc82) | [PASS cục bộ](../../docs/evidence/checkpoints/CP5/T058-p3-cuong-smoke.md) | P1/Huy, P4/Quang | VERIFIED |
| `CP5/T059` | Artifact metadata and full release gate | `CP5 T059(model): write evaluated metadata and gate release` | 630f9ab815c80cde374a2df3772c33fe7a5de811 | [Commit 630f9ab](https://github.com/HiImNVH/ViSign/commit/630f9ab815c80cde374a2df3772c33fe7a5de811) | [PASS cục bộ](../../docs/evidence/checkpoints/CP5/T059-p3-cuong-smoke.md) | P1/Huy, P2/Tín | VERIFIED |
| `CP5/T062` | Model card | `CP5 T062(model): document ViSign model scope and evaluation` | 3777d0cf0dc7ab22c744a791860943de0fd50875 | [Commit 3777d0c](https://github.com/HiImNVH/ViSign/commit/3777d0cf0dc7ab22c744a791860943de0fd50875) | [PASS cục bộ](../../docs/evidence/checkpoints/CP5/T062-p3-cuong-smoke.md) | P1/Huy | PUSHED |
| `CP5/T065` | HTTP benchmark and local performance evidence | `CP5 T065(eval): benchmark inference latency and resources` | cc9a2144723a029b7b1b1973a475d202184259c1 | [Commit cc9a214](https://github.com/HiImNVH/ViSign/commit/cc9a2144723a029b7b1b1973a475d202184259c1) | [Local measured](../../docs/evidence/checkpoints/CP5/T065-p3-cuong-smoke.md) | P1/Huy, P2/Tín | P1_VERIFIED local |

## Handoff

- Current risks: feature schema v0.3 chưa được APPROVED; không được bulk-extract trước review.
- Required input: representative WebM clips và data manifest đã audit.
- Next owner/action: P3 đã xuất bộ review 6 WebM gồm 6 JSON và 18 ảnh L/R. Cả 6 tạo được tensor hữu hạn, 20–32/32 bước dùng được. Huy chờ nhận bộ clip để duyệt schema và xác nhận clip nghi lật. T017 đã push, CI xanh. P3 đã push test tự động theo review P2 tại 57311bf; đã được Huy/Tín duyệt; nối T010 khi Quang bàn giao. Tín phối hợp kiểm parity qua đường serving.
- Review lại T098 (snapshot Quang/T098): CHANGES_REQUESTED. Pytest 12 test và 25 subtest đạt; Ruff 5 lỗi, mypy 2 lỗi. Hash và mapping khớp 27/27. Decoder đọc 24/27; T017 xuất NPZ cho 3/3 clip S001-R01. Sáu nguồn website chưa đối chiếu độc lập; còn chờ quyền, nhãn và manifest đã audit.
- Review T009–T012 (snapshot Quang): CHANGES_REQUESTED. Pytest đạt ở cả bốn snapshot; Ruff/mypy còn lỗi. T010 cần chiếu sampleId/rawPath sang T017. T012 audit inventory 27 clip đúng và chặn release, cần phân biệt releaseEligible metadata với đủ split để chạy T036.
- Review API cho Tín: T019 metadata VERIFIED, T059 ghi demoReady theo gate full. T037 parity 6/6 WebM đạt và đã chốt quy tắc T049; T033/T036 smoke nạp được metadata và trọng số, factory GRU đã tích hợp qua T037.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P2/Tín | P3/Cường | Review AI toolchain T003 |
