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
