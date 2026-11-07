# CP1 T008 — Raw material guidance

- Owner: P4/Quang. Date: 2026-11-07 (Asia/Bangkok).
- User explicitly requested commit and push of T008. Independent reviewer: P1/Huy, P3/Cường — PENDING.
- Baseline: 3815e45 (origin/main fetched before preparation).
- Scope: data/README.md, members/p4-quang/README.md, this evidence only.
- Existing local P0 edits and dataset report are excluded; no raw videos or binaries included.

## Outcome

Clarify intake, original-byte preservation, checksums, relative paths, metadata, privacy and pre-stage checks.
Preserve current lead decisions: dataset-level source/usage declaration for the existing P0 material,
optional signerId, video-held-out grouping by recordingSessionId, no unseen-signer claim.
Distinguish representative-clip review from bulk extraction after convention/schema approval.
No dataset rights or specialist verification is asserted by this documentation change.

## Gates

- PASS: 4/4 Markdown links resolve to tracked files in candidate index via git cat-file -e :<path>.
- PASS: git diff --cached --check, exit 0.
- PASS: 7/7 raw/artifact/secret ignore probes (exit 0), 2/2 documentation/CSV visibility probes (exit 1).
- PASS: exact staged scope is the three Markdown files listed above.
- Code/runtime/cloud tests: NOT_RUN, documentation-only change; no deployment.
- Independent reviewer result: PENDING. No task completion checkbox changed.

## Publication

- Published commit: [c034e6e421f3788fdb7ecbc90ab558476ae310b0](https://github.com/HiImNVH/ViSign/commit/c034e6e421f3788fdb7ecbc90ab558476ae310b0).
- git pull --rebase origin main: HEAD up to date; pre-push divergence 0 1.
- git push origin HEAD:main: exit 0, 3815e45..c034e6e.
- GitHub Actions: not verified in this session; documentation gates above passed locally.
No force push or amend. Local unrelated draft files remain in the original workspace.

## Independent review — P1/Huy

Review time: `2026-11-07T16:33:39+07:00` trên `origin/main` `d156569` (chứa `c034e6e`, `e2bdf7f`).

| Gate | Kết quả |
|---|---|
| Nhất quán spec | Khớp FR-012/FR-015 và quyết định lead 2026-11-07: nguồn/căn cứ sử dụng cấp dataset, `signerId` tùy chọn, `video-held-out` theo `recordingSessionId`, không tuyên bố unseen-signer |
| Nhất quán quy ước | Dẫn đúng `data-convention.md` mục 8; giữ tên gốc trong `incoming/`, chưa bulk rename trước T098 |
| Link | 3/3 link tương đối trỏ tới file đang track |
| Ignore probes | `.mp4`, `.webm`, `.npz`, `.pt`, `.safetensors`, `data/raw/`, `data/processed/`: bị ignore. `data/README.md`, `data/manifests/*.csv`: vẫn track được |
| CI | `quality.yml` trên `e2bdf7f`: success |

Ghi chú không chặn:

1. Cảnh báo ZIP của Quang là đúng: `incoming/ViSign-videos.zip` và `reports/consent.pdf` **không** bị
   `.gitignore` chặn, và CI hygiene cũng chưa chặn `.zip`. Repo legacy từng track một ZIP video 21 MB.
   Đề xuất: P2 thêm `*.zip` vào `.gitignore` (T001–T007 setup), P1 thêm `zip` vào danh sách đuôi cấm của
   `quality.yml` (T091).
2. Câu "Không commit/push trước khi người dùng yêu cầu" nên đổi thành "trước khi tới lượt integration
   window và các gate liên quan đạt" cho đúng quy trình nhóm.
3. Bản candidate T008 trước đó của P1 (`docs/evidence/checkpoints/CP1/T008-p1-huy-data-guidance-smoke.md`)
   được thay bằng bản của owner P4; evidence P1 đánh dấu superseded.

**Reviewer result**: `P1_VERIFIED`; `P3` còn `PENDING` (không chặn đóng CP1 vì P1 là reviewer chính của T008).
