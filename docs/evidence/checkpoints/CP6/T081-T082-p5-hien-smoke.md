# CP6 T081–T082 — P5 Hiển: frontend internal admin training

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint / tasks | CP6 / T081 frontend tests; T082 typed client, `/admin/train-model` và pilot UI |
| Owner / reviewer | P5 Hiển / P1 Huy, P2 Tín (đang chờ) |
| Commits | T082: `eb14519a46e2a0dd83bd30af6ba4848467eef7c0`; T081 là micro-commit riêng, xem `git log --grep='CP6 T081'`; bổ sung GitHub URL sau push |
| Ngày / timezone | 2026-11-08, Asia/Ho_Chi_Minh |
| Base | `main` đồng bộ tới `7739c66` bằng stash/fast-forward/apply trước commit; remote mới chỉ đổi tài liệu cloud và CloudFormation, không ảnh hưởng web gate |
| Môi trường | Windows PowerShell, Node 26, npm 11, Vitest 5, Playwright Edge (desktop/mobile/landscape) |
| Status | `TEST_PASS / READY_FOR_REVIEW`; backend live integration `NOT_RUN` |

## 2. Phạm vi

- T082: lazy route nội bộ `/admin/train-model`; nhập/đổi/ngắt token chỉ ở React memory, gửi Bearer header (không ghi local/sessionStorage hoặc URL), biểu mẫu inspect MP4/WebM tới 100 MiB, tải ZIP kết quả.
- T082: typed admin API với lỗi Việt hóa ổn định và giới hạn URL W&B; trạng thái preflight/train (không chạy song song), polling 4 giây khi job active, metadata/metrics/history mới nhất trước, hiển thị W&B online/offline.
- T081: component test cho auth/401, 404 disabled, 409 conflict, 503 unavailable, 504 timeout, multipart inspect + ZIP, local invalid clip, preflight, train, history, W&B allowlist, JSON bất thường; browser test kiểm tra route thực, nhập token và không ghi credential vào storage.
- Không can thiệp T078–T080 backend của P2, T083 AI/data của P3/P4, model release gate hoặc trang camera public.

## 3. Smoke và bằng chứng

| # | Gate / command tái lập từ repo root | Quan sát | Status |
|---|---|---|---|
| 1 | `cd apps/web; $env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check` | ESLint, `tsc --noEmit`, Vite build hoàn tất, exit 0 | PASS |
| 2 | Vitest trong `npm.cmd run check` | 177 passed, 4 skipped (9 test T081 mới) | PASS |
| 3 | Playwright Edge trong `npm.cmd run check` | 87 passed, 12 skipped trên 3 viewport; route T082 có 3 pass | PASS |
| 4 | Component `apps/web/tests/admin/admin-training.test.tsx` | Cover 401/404/409/503/504, input invalid, ZIP, online/offline W&B, malformed response; backend messages chứa path/token không xuất hiện trong UI | PASS |
| 5 | Live `/api/admin/*` với token thực | Chưa có implement T078–T080 trong repo hiện hành; chỉ xác nhận qua mock + contract | NOT_RUN |
| 6 | Cleanup ZIP/worker, job concurrency dưới backend thực | Thuộc T078–T080 backend; P2 phải tự kiểm chứng, FE không có quyền xác nhận | NOT_RUN |

Các browser skips là screenshot capture opt-in và backend live camera tests có điều kiện; không tính là pass. Test admin sử dụng `test-secret` giả trong bộ test, không ghi credential thật.

## 4. Artifact và link

| Loại | Vị trí | Ghi chú |
|---|---|---|
| Frontend | `apps/web/src/features/admin/` và `apps/web/src/services/adminApi.ts` | P5 ownership |
| Entrypoint | `apps/web/src/main.tsx` | Điều hướng lazy, trang nhận diện public còn nguyên |
| Unit + browser | `apps/web/tests/admin/admin-training.test.tsx`, `apps/web/tests/browser/admin-route.spec.ts` | Test tái lập offline bằng mock |
| Commit diff | Bổ sung GitHub URL sau push được Huy mở integration window | Tránh ghi SHA chưa tồn tại |
| GitHub Actions | NOT_RUN: mới kiểm chứng tại máy P5 | P1 chạy CI sau tích hợp |
| Admin API | NOT_RUN: P2 chưa bàn giao T078–T080 | Contract `specs/001-vsl-recognition-mvp/contracts/admin-tools.md` |

## 5. Rủi ro, rollback và handoff

- UI hiện chỉ kiểm chứng bằng mocked HTTP; contract có thể cần chỉnh theo response triển khai thật của Tín. Chính P2 xác nhận auth, concurrency 409, cleanup và 404 khi disabled; P5 chạy lại smoke với API thực sau bàn giao.
- Các route admin được đưa vào bundle web, nhưng backend phải tiếp tục tắt mặc định khi không có `VISIGN_ADMIN_TOKEN`. Không đưa token thật hoặc nội dung inspect vào repo.
- Rollback mỗi thay đổi theo micro-commit CP6 T081/T082 riêng; không ảnh hưởng T083 hoặc API recognition public.
- P1/P2 review độc lập trước khi chuyển `[ ]` thành `[X]` trong `tasks.md`; không tự đóng CP6.

## 6. Xác nhận

- [x] Owner chạy frontend full gate sau chỉnh code.
- [x] Không stage secret, video, weights hay binary runtime.
- [ ] Full SHA và GitHub link cập nhật sau push.
- [ ] Reviewer tự chạy gate và ghi kết quả.

**Reviewer result:** `PENDING`

**Reviewer note:** Chờ P1/Huy và P2/Tín.

## Independent review — P1/Huy (2026-11-08, `a498da5` + `c0d598f`)

| Kiểm | Kết quả |
|---|---|
| Gate web | ESLint + `tsc` sạch; Vitest **177 passed / 4 skipped**; `admin-route.spec.ts` lặp 2 lần × 3 viewport **6/6**; CI `c0d598f` xanh |
| Contract | FE gọi đúng 5 endpoint của `contracts/admin-tools.md`, ánh xạ 401/404/409/503/504 thành câu tiếng Việt ổn định, không hiển thị chuỗi lỗi backend |
| Token | Chỉ nằm trong state React; gửi `Authorization: Bearer`, `credentials: 'omit'`, `no-store`; 401 xoá token; không có `localStorage`/`sessionStorage`/`dangerouslySetInnerHTML`/`console` trong mã admin |
| W&B URL | Chỉ nhận `https` tới `wandb.ai`/`forge.coreweave.com` đúng dạng run, không có user/password |
| Production (EC2 `52.65.207.133`) | `/admin/train-model` → 200 `text/html` (nginx fallback SPA); `/api/admin/pilot` → 404 vì admin tắt mặc định — đúng ranh giới bảo mật |

Điểm cần chốt với P2 khi làm T079–T080: contract chỉ ghi `prepare`/`train` trả **202** mà chưa định nghĩa body,
trong khi FE đọc `TrainingRun` từ body; tên trường multipart (`video`) cũng chưa có trong contract. Bổ sung hai
điểm này vào `admin-tools.md` để FE/BE khớp.

**Reviewer result**: T081 `P1_VERIFIED`, tick `[X]`. T082 `P1_VERIFIED` phần FE; giữ `[ ]` đến khi smoke với backend
T078–T080 thật.
