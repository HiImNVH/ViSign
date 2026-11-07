# CP3 T043 — Ghép camera / model-info / prediction (P5 Hiển)

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint / task | `CP3 / T043` (`US1`) |
| Owner | `P5 Hiển` |
| Reviewer | `P2 Tín`, `P1 Huy` — chờ review độc lập |
| Commit | Local candidate `CP3 T043(web): integrate camera with recognition results`; lấy SHA từ git log sau commit, chưa push |
| Ngày / múi giờ | `2026-11-07`, `Asia/Ho_Chi_Minh` (`UTC+07:00`) |
| Môi trường | Windows, Node/npm theo `apps/web/package.json`, Vitest 5.0.5, Playwright 1.64.1, Edge Chromium (`VISIGN_BROWSER_CHANNEL=msedge`) |
| Trạng thái | `IMPLEMENTED_LOCAL / READY_FOR_REVIEW`; chưa được reviewer xác nhận và chưa đóng CP3 |

## 2. Phạm vi thay đổi

- `apps/web/src/App.tsx`: tạo một `useRecognition()` duy nhất, truyền controller vào `CameraRecorder`; dùng chung phiên camera và metadata/result.
- `apps/web/src/features/recognition/CameraRecorder.tsx`: quay clip WebM local, chỉ POST `/api/v1/predictions` khi chọn **Gửi nhận diện** và `GET /api/v1/model-info` đã sẵn sàng. Fixture/pilot/full cùng endpoint. Hiển thị `RecognitionResult` sau khi response accepted và khớp modelVersion; rejected/API error chỉ hiện feedback. Người dùng hủy, quay lại hoặc tắt camera để xóa kết quả cũ / abort request.
- `apps/web/src/{content/vi.ts,components/CameraHelp.tsx,styles.css}`: hướng dẫn gửi có chủ đích, metadata loading/retry, phản hồi lỗi và bố cục gọn không cuộn.
- `apps/web/tests/browser/camera.spec.ts`: fake camera WebM thật trên Edge, route API mock cho fixture/pilot/full, kiểm tra multipart POST chỉ sau khi click, retry metadata, rejected, modelVersion mismatch, clip mới, bố cục `320×180`, desktop/mobile/landscape.
- `apps/web/tests/recognition/{recognition-flow.test.tsx,recognition-overlay.test.tsx}`: cập nhật harness/component test đúng boundary của controller.
- `apps/web/README.md`, `members/p5-hien/README.md`: mô tả luồng hiện tại và handoff.
- Không thay đổi API server, mô hình, dataset, feature schema hoặc endpoint theo `artifactKind`.

## 3. Gate và smoke test

Thực thi từ `apps/web` bằng PowerShell: `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check`.

| # | Gate | Kết quả |
|---|---|---|
| 1 | ESLint + TypeScript | PASS, exit 0 ở cả full gate trước và sau rebase |
| 2 | Vitest unit/component | PASS, **80/80** tests, 7 files ở cả hai lần chạy |
| 3 | Vite production build | PASS, exit 0 ở cả hai lần chạy |
| 4 | Playwright Edge fake camera / API mocked | PASS, **39/39** tests qua desktop, mobile, landscape ở cả hai lần chạy |
| 5 | Đồng bộ git | `git fetch origin main`: remote cập nhật `f1eb7ea`, sau đó `1b14f1e` (T019/T037 evidence); stash đúng T043, `git pull --rebase origin main` và `git stash apply` đều exit 0 ở cả hai lần; `origin/main...HEAD` = `0 1` sau rebase cuối |
| 6 | Full gate sau rebase | PASS, exit 0; `npm.cmd run check` sau rebase `f1eb7ea`: lint/typecheck/build PASS, Vitest 80/80 PASS, Playwright 39/39 PASS (58.7s). Rebase tiếp tới `1b14f1e` chỉ bổ sung tài liệu backend/AI, không đụng frontend; không cần chạy lại frontend gate |
| 7 | `git diff --check` | PASS, exit 0 trước rebase; kiểm tra lại trước commit |

**Phạm vi test:** `getUserMedia`/`MediaRecorder` trên fake-camera Y4M; request HTTP dùng route mock theo hợp đồng `/api/v1/model-info` và `/api/v1/predictions`. Không chạy backend local hoặc model thật; không đo accuracy/latency end-to-end. Trong các browser test không mock model-info, Vite có thể ghi `ECONNREFUSED 127.0.0.1:8000`, do backend không chạy; những case đó kiểm tra hành vi fallback và vẫn PASS.

## 4. Link và artifact

| Loại | Tham chiếu | Ghi chú |
|---|---|---|
| Commit diff | Chưa có URL — local candidate, chờ integration window | Không ghi link SHA chưa push như đã public |
| GitHub Actions | NOT_RUN — candidate chưa push | Workflow sẽ xác minh sau khi có window |
| Report trong repo | `docs/evidence/checkpoints/CP3/T043-p5-hien-integration-smoke.md` | Báo cáo lệnh/kết quả có thể tái lập |
| Backend/API | API v1 theo `docs/team/fe-be-api-convention.md` | GET model-info; POST predictions; browser sử dụng mock |
| Model/data | Fixture/pilot/full trả về từ metadata mock | Không có model binary hay raw clip được commit |

## 5. Rủi ro, rollback và handoff

- **Rủi ro:** Chưa chạy cặp frontend/backend thật, camera thiết bị thật, hay parity model; API/model cần Tín/Cường cung cấp runtime và sample phù hợp.
- **Rollback:** Revert riêng commit T043 khi đã được tích hợp; T042 accepted-result component vẫn độc lập.
- **Người kế tiếp:** P2/Tín và P1/Huy review integration + kiểm tra tương thích API đang chạy; P1/Huy điều phối integration window. Sau đó mới push và đánh dấu task `[X]` theo evidence độc lập.
- **Blocker push:** `docs/team/git-checkpoints.md` quy định chỉ owner có integration window được push; status nhóm hiện chưa bàn giao window cho P5.

## 6. Xác nhận

- [x] Owner xác nhận toàn bộ gate sau rebase cuối.
- [ ] Candidate staging không có secret/raw video/model binary.
- [ ] SHA public + link được điền sau push.
- [ ] Reviewer chạy độc lập và xác nhận.

**Reviewer result**: `PENDING`.

## Independent review — P1/Huy

Huy (P1) review và kết luận **đạt**; ghi nhận `2026-11-07T22:06:58+07:00` trên `630f9ab`. Gate tái chạy: AI 73 passed, 5 skipped (thiếu fixture clip local); API + contract 332 passed, 2 skipped; web lint, typecheck, Vitest 88/88, build PASS; CI `quality.yml` xanh.

**Reviewer result**: `P1_VERIFIED` → T043 `[X]`.
