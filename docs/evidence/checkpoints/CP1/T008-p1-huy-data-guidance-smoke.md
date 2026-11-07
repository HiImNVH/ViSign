# CP1 T008 smoke evidence — raw material và quyền sử dụng

## Identification

| Field | Value |
|---|---|
| Checkpoint/task | `CP1 / T008` |
| Implementer | `P1 Huy` — integration docs candidate |
| Reviewer | `P4 Quang` |
| Candidate commit | `CP1 T001-T008(docs): review setup and document raw data` |
| Commit SHA | `189d34bcd4875752dab460716756aa8239996f9f` — [189d34b](https://github.com/HiImNVH/ViSign/commit/189d34bcd4875752dab460716756aa8239996f9f) |
| Run time | `2026-11-07T13:55:07+07:00` |
| Status | `PUSHED`; P4 review pending |

## Pre-commit synchronization

- Time: `2026-11-07T13:56:33+07:00`.
- `git fetch origin main`: PASS.
- Local HEAD và `origin/main`: `18a07aef641b424ddf4772249623b1bc04a4b926`.
- Behind/ahead: `0/0`.
- Re-sync: origin nhận thêm `9b888a1`/`5dc97a6` (CP2 T019–T021 của P2). Local work được stash,
  rebase lên `5dc97a6`, conflict duy nhất ở ledger `members/p2-tin/README.md` đã resolve giữ cả
  dòng CP1 và CP2. Gate T008 chạy lại sau re-sync.

## Acceptance coverage

| Requirement | Evidence | Status |
|---|---|---|
| Raw material outside Git | External/local folder guidance và `.gitignore` paths | `PASS` |
| Model input boundary | Raw video -> audit -> landmark/tensor -> GRU được mô tả rõ | `PASS` |
| Rights and privacy | Source, license, consent, retention và sensitive-data exclusions | `PASS` |
| Metadata | sample/class/meaning/signer/session/source/license/verification/path/duration/frame fields | `PASS` |
| Split safety | signer-held-out bắt buộc cho full; session-only chỉ pilot/dev | `PASS` |
| Pending convention | Không bulk rename/normalize trước khi T098 được đóng băng | `PASS` |
| Handoff | Trình tự Quang -> Cường -> Tín và pilot/full disclosure | `PASS` |

## Commands

- Content validator kiểm các mục raw/model boundary, rights, `signerId`, T098 và
  `demoReady=false`: PASS.
- `git diff --check`: PASS.

## Links

- Commit: [189d34b](https://github.com/HiImNVH/ViSign/commit/189d34bcd4875752dab460716756aa8239996f9f) — pushed `5dc97a6..189d34b`.
- Source document: `data/README.md`.

## Reviewer

**Result**: `SUPERSEDED` — owner P4/Quang nhận lại T008 và phát hành bản sửa tại `c034e6e`; review P1 nằm ở
`docs/evidence/checkpoints/CP1/T008-p4-quang-smoke.md`.

**Note**: P4/Quang kiểm tra lại workflow thực tế trước khi T008 được đánh dấu hoàn thành.
