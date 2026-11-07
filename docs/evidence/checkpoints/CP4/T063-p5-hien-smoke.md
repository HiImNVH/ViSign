# CP4 T063 — P5 Hiển smoke evidence

## Identification

| Field | Value |
|---|---|
| Checkpoint/task | CP4 / T063 |
| Owner/reviewer | P5 Hiển / P1 Huy and P2 Tín (pending) |
| Commit | PENDING — full SHA and GitHub URL after publish |
| Date/timezone | 2026-11-08, Asia/Ho_Chi_Minh (UTC+07:00) |
| Environment | Windows, Edge `msedge` via Playwright, simulated camera, API v1 mocks |
| Status | TEST_PASS / READY_FOR_REVIEW |

## Scope

Keyboard, focus restoration, status announcements, dialogs, camera labels, rejected/accepted responses and small-viewport focus. Source: `apps/web/tests/accessibility/recognition-accessibility.spec.ts`, `CameraRecorder.tsx`, `HistoryPanel.tsx`, `CameraHelp.tsx`, and `styles.css`. No backend contract/runtime dependency changes.

## Smoke checks

| # | Objective and command | Actual | Status |
|---|---|---|---|
| 1 | Lint/typecheck/build: `cd apps/web; npm.cmd run check` | All static gates and build exit 0 | PASS |
| 2 | Unit/component in same gate | 165 pass, 4 skipped | PASS |
| 3 | Browser keyboard/WCAG/status in same gate, `$env:VISIGN_BROWSER_CHANNEL='msedge'` | 75 pass, 3 skipped; T063 21/21; axe 0 violations on audited states | PASS |
| 4 | Negative cases: denied camera, rejected response, no auto-upload, history focus | All assertions passed with fake camera/API | PASS |
| 5 | Manual screen reader on real device | Not exercised | NOT_RUN |
| 6 | Production/backend/real-camera smoke | Beyond T063 scope | NOT_RUN |

## Artifacts

| Artifact | Reference |
|---|---|
| Commit diff | PENDING, link after push |
| GitHub Actions | NOT_RUN; not queried for this local candidate |
| Findings | `docs/verification-report.md` |
| Automated suite | `apps/web/tests/accessibility/recognition-accessibility.spec.ts` |
| Cloud/model | NOT_RUN; model metadata and prediction were mocked |

## Risks, rollback and handoff

Automated checks cannot validate actual screen reader timing or hardware. Roll back the isolated T063 commit if any UI behavior regresses. P1/P2 should independently run Edge gate and review focus/announcements; reserve full system checks for T067. Integration window must be observed before push.

## Confirmation

- [x] Owner ran full web gate after final UI changes.
- [x] Candidate contains no raw video, private dataset, model binary or credentials.
- [ ] Commit SHA/link recorded after publish.
- [ ] Independent reviewer repeated gate.

**Reviewer result:** PENDING. **Reviewer note:** Awaiting independent assessment.

## Independent review — P1/Huy

Review `2026-11-08T01:39:48+07:00` trên `b5ca295` (theo uỷ quyền của Huy), Edge `msedge`, máy P1.

| Kiểm tra | Kết quả |
|---|---|
| Nội dung audit | axe WCAG 2/2.1 A+AA 0 vi phạm ở các trạng thái được audit; bàn phím, khôi phục focus, `role=status`/`aria-live`, nhãn camera — đạt khi quay được clip |
| Ổn định bộ test | **Chập chờn**: 3 lượt chạy `recognition-accessibility.spec.ts` → 4, 3, 1 test hỏng / 21 |
| Nguyên nhân quan sát | Camera chuyển **"Camera gặp lỗi"** ngay khi đang quay (fake device + MediaRecorder), các bước sau không có clip; cùng hiện tượng xuất hiện trong lượt chụp ảnh T088 |

**Reviewer result**: `CHANGES_REQUESTED` (trung bình) — nội dung accessibility đạt, nhưng (1) điều tra lỗi camera
khi quay (khu vực T039: bắt `MediaRecorder` `error` và ghi tên lỗi, kiểm tra có phải race giữa start/stop hay
tài nguyên device), vì người dùng thật có thể gặp; (2) làm bộ test ổn định (chờ trạng thái thay vì
`waitForTimeout`, hoặc retry chỉ khi lỗi thiết bị giả được nhận diện). T063 giữ `[ ]`.
