# CP2 T018, T056, T098 — tích hợp gói P4/Quang và review P1

**Ngày**: 2026-11-08 · **Owner**: P4 Quang · **Tích hợp/review**: P1 Huy

## Nguồn

Gói local `T018/T056/T098 review-20261108-v2` (Quang gửi, không có nhánh GitHub). Chỉ chép đúng 25 đường dẫn trong
`INTEGRATION-ALLOWLIST.json` của mỗi gói (ba gói không xung đột nhau); **không** chép `training_inputs.py`,
`landmarks/`, video, `.task`, `model.pt`, `Dataset.zip`. Toàn bộ là file mới so với `main`.

## Kiểm

| Kiểm | Kết quả |
|---|---|
| Luật split (`create_splits.py`) | Gom theo `recordingSessionId` (bắc cầu, cả xuyên meaning), `signerId` tùy chọn, nhận `verified`/`unverified`, chặn `rejected` và license khác `approved`; `splitEvidence = video-held-out` — khớp FR-015 |
| Gate AI trên worktree `main` + gói | ruff sạch; mypy 49 file sạch; **175 passed, 5 skipped, 61 subtests**; riêng dataset **88 passed** |
| Manifest `p0-source-v5.DRAFT.csv` | 101 clip; `sourceUri` có ở **101/101** (76 `dataset:self-recorded`, 25 URL `nnkh.thaiphong.net`); `licenseStatus=approved`, `verificationStatus=unverified` |
| Format | `ruff format --check` báo 19 file khác định dạng (CI không kiểm format) |

## Kết luận

- **T018, T056**: `P1_VERIFIED`, tick `[X]`.
- **T098**: `CHANGES_REQUESTED` nhỏ — `docs/contracts/data-conventions.md` dòng 23 và 63 vẫn cho phép để trống
  `sourceUri` với video công khai, lệch quyết định 2026-11-08 (bộ dữ liệu gồm cả hai nguồn nên ghi nguồn từng clip).
  Manifest đã điền đủ nên chỉ cần sửa câu chữ + validator.
- T009–T013 (entities/schema/validator/registry) đã vào `main` cùng gói; chờ P3 review lại các điểm cũ
  (nối `sampleId/rawPath` sang T017) trước khi tick.
- Dữ liệu full còn thiếu quota (mục tiêu 200 video) và duyệt lớp; T077 chưa bắt đầu.
