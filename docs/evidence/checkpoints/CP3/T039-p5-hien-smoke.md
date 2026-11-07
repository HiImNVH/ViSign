# CP3 — T039: camera capture local

## Nhận dạng và đồng bộ

| Trường | Giá trị |
|---|---|
| Owner / Reviewer | P5 Hiển / P2 Tín, P1 Huy — review PENDING |
| Task | T039; phần camera test T031 và copy T028 hỗ trợ; chưa đóng các task/checkpoint |
| Status | PASS local trên Edge; NOT_PUSHED; chưa có API/model integration |
| Ngày/giờ | 2026-11-07T13:50:37+07:00 |
| Pre-commit sync | Đồng bộ `origin/main` tại `18a07aef641b424ddf4772249623b1bc04a4b926`; dùng toolchain CP1 của Tín, giữ nguyên dependency/lockfile; khôi phục camera candidate, clean install và chạy lại toàn bộ gate; remote-only count 0 |
| Commit | PENDING trước push; tìm local SHA bằng `git log -1 --format=%H -- apps/web/src/features/recognition/cameraSession.ts` |
| Pre-push sync / GitHub link | NOT_RUN / PENDING — chưa có integration window, không push |
| Môi trường | Windows 11, Node 26.7.0, npm 11.19.0, Playwright 1.64.1, Vitest 5.0.5, Vite 8.3.5, Edge Chromium 157.0.4341.42 |

## Phạm vi và ranh giới

- Bật camera chỉ mở preview. Quay ký hiệu → Kết thúc tạo Blob WebM trong bộ nhớ.
- Hủy yêu cầu xin quyền bỏ qua stream trả muộn; Hủy đoạn quay giữ preview; Tắt camera giải phóng thiết bị.
- Chỉ yêu cầu video (`audio: false`); không gửi request API, lưu file, localStorage, object URL hoặc log payload.
- Dừng tự động sau 5 giây; kiểm tra client sơ bộ 300 ms–6 giây, tối đa 10 MiB theo envelope T015.
  Backend vẫn phải xác thực MIME/content, byte count và duration từ decoder khi tích hợp.
- Theo dõi generation của permission request và identity recorder; gỡ listener trước khi stop,
  đợi final data/stop, bỏ empty/unexpected/late events, finalization timeout 3 giây.
- Cleanup stream, chunks, timers, preview và Blob khi reset, pagehide, unmount hoặc lỗi.
- API client T040, recognition state T041, result T042 và integration T043 chưa thuộc commit này.

## Spec Kit và skill áp dụng

- `speckit-implement`: chạy prerequisites với `SPECIFY_FEATURE_DIRECTORY=specs/001-vsl-recognition-mvp`;
  đọc spec/plan/tasks, constitution, camera research/data-model/contract và quickstart.
- Checklist requirements: 18/18 checked, 0 unchecked; không sửa checkbox của checklist.
- Không có `.specify/extensions.yml`, nên không có before/after implementation hook cần dispatch.
- Viết camera session tests trước implementation: lần đầu fail vì module chưa tồn tại; sau implementation đạt.
- Tuân thủ quy định completion của repository: giữ task chưa đóng khi mới là candidate local.
- UI/UX Pro Max: nhãn hành động rõ, focus, live status, bố cục responsive và chữ đủ tương phản.
- Frontend Design: ưu tiên vùng camera, nền sáng, font hệ thống hỗ trợ tiếng Việt; không thêm nội dung quảng bá.
- Emil/mobile-native: safe area/zoom, touch targets 48px, hover theo capability, press transform 160ms,
  giảm chuyển động theo `prefers-reduced-motion`; modal dùng native dialog, không thêm thư viện animation.

| Before | After | Why |
|---|---|---|
| Chưa có phản hồi khi thao tác camera | Status tiếng Việt và focus vào hành động tiếp theo | Người dùng bàn phím/screen reader biết trạng thái |
| Chuyển động chưa có mục đích cụ thể | Chỉ phản hồi nhấn nhỏ; keyboard/reduced motion không dịch chuyển | Tránh làm chậm luồng lặp lại |
| Chưa có giới hạn capture | Safety stop, byte cap, finalization timeout | Giữ tài nguyên hữu hạn và không treo giao diện |

## Gate và kết quả

Chạy từ `apps/web/`:

```powershell
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm.cmd run typecheck
npm.cmd run check
```

| Gate | Kết quả | Status |
|---|---|---|
| Clean install | `npm.cmd ci` theo package-lock CP1 của Tín; 278 packages; exit 0 | PASS |
| ESLint | 0 warnings; exit 0 | PASS |
| TypeScript | Strict typecheck, gồm config/tests; exit 0 | PASS |
| Vitest | 32 tests / 3 files; exit 0 | PASS |
| Vite build | 21 modules, build thành công; exit 0 | PASS |
| Browser | 8 tests; desktop 1440×900 và mobile viewport 320×640; exit 0 | PASS trên Edge |
| Git diff | `git diff --check`; exit 0 | PASS |
| Physical webcam / phone | Chưa chạy; kiểm tra giả lập không chứng minh hành vi thiết bị thật | NOT_RUN |
| API/model/CI/cloud | Chưa tích hợp, không nằm trong candidate T039 | NOT_RUN |

Unit/component tests kiểm tra preview không tự ghi, duplicate enable/start/stop, denied/retry,
stream/play trả muộn, playback failure, final chunk ordering, cancel trong lúc stopping,
stale callbacks, empty clip, duration/byte limits, timeout, missing recorder/MIME, track ended,
stop failure, StrictMode, pagehide/unmount cleanup và focus.

Browser tests dùng fixture Y4M tổng hợp 320×240, 30fps; gọi `getUserMedia` và `MediaRecorder` thật:
preview có frame/time tiến lên, quay và hoàn tất clip không rỗng, hủy/quay lại/tắt camera,
track chuyển `ended`, preview srcObject về null, không request non-GET hoặc `/api/`, không pageerror.
Test denial dùng Chromium CDP với permission `camera`; test dialog kiểm tra Escape/focus/reduced motion.

## Giới hạn và artifact

- Lần kiểm tra ban đầu bằng Playwright 1.65.0 / Chromium Headless Shell 158.0.8127.18
  trả `NotSupportedError` cho fake camera; camera tests không đạt trên binary đó.
  Gate cuối dùng toolchain của Tín (Playwright 1.64.1) và Edge 157, đã chạy lại đạt.
  Chưa xác nhận camera trên bundled Chromium của Playwright 1.64.1.
  Không mock HTTP hoặc bỏ qua test để ghi PASS; channel Edge được chỉ rõ ở lệnh tái lập.
- Ảnh kiểm tra sinh bởi browser test tại
  `apps/web/test-results/camera-explicitly-records--a591f-M-clip-then-releases-camera-{desktop,mobile}/camera-captured.png`.
  Đã xem cả hai ảnh; chỉ chứa frame tổng hợp, không có hình ảnh cá nhân.
- Y4M `.local/`, browser reports/trace, `node_modules/` và `dist/` được ignore; không stage binary.
- Source/tests và evidence này là artifact tái lập trong repo. GitHub commit/Actions chưa có vì chưa push/workflow.
- Dependency của toolchain CP1 được giữ nguyên: clean install ghi nhận 10 cảnh báo moderate ở dev;
  `npm audit --omit=dev` ghi nhận 0 vulnerability runtime. Chưa nâng dependency trong T039.
- Mức engine của một số dependency dev cao hơn Node 22.12 khai báo; đã ghi để Tín review.
  Gate camera được chạy trên Node 26.7.0, không khẳng định tương thích Node tối thiểu của toolchain.

## Handoff và rollback

- Chờ toolchain/foundation của Tín, T099 cho API client và Huy mở integration window.
- Huy/Tín chạy lại gate, review camera thật và contract trước tích hợp; không coi T039 local là hoàn tất US1/CP3.
- Rollback bằng revert riêng commit T039 sau review; không reset/force-push main.
- Override: UI tiếng Việt theo constitution thay core §5.2; commit theo CP/task thay core §11.2.

## Independent review — P2/Tín

Review time: `2026-11-07T14:55+07:00` trên `origin/main` `5b6a441` (chứa T039 `e9badad`…`dc52640`); Windows 11,
Node 24.18.0, Edge (`VISIGN_BROWSER_CHANNEL=msedge`).

| Gate | Kết quả độc lập |
|---|---|
| Static/build | `npm ci`, `npm run lint`, `typecheck`, `build`: PASS |
| Browser | `npx playwright test`: 21 passed trên Edge |
| Unit | `vitest run`: 42 passed nhưng **không ổn định** — xem mục 1 |
| Contract | Giới hạn 300 ms/5000 ms/6000 ms/10 MiB, ưu tiên `video/webm;codecs=vp8` → `vp9` → `video/webm`, `audio: false` khớp `docs/contracts/api-conventions.md`; mirror chỉ là CSS `scaleX(-1)` trên `video`, dữ liệu gửi đi không bị lật |

Phát hiện:

1. `CHANGES_REQUESTED` — **test focus flaky làm đỏ CI `main`**. `CameraRecorder.tsx` chuyển focus trong
   `useEffect` (passive, chạy sau commit), còn `recognition-flow.test.tsx` kiểm `toHaveFocus()` ngay sau
   `waitFor(status = 'Camera sẵn sàng')`. Khi assertion chạy giữa commit và effect, focus vẫn ở `body`.
   - Local: 13/15 lần pass với code hiện tại.
   - Thử đổi sang `useLayoutEffect` (chạy đồng bộ sau commit, trước paint — đúng chỗ cho quản lý focus):
     30/30 lần pass, toàn bộ 42 test vẫn pass. P2 đã khôi phục file, không commit thay owner.
   - CI: [run 42352747056](https://github.com/HiImNVH/ViSign/actions/runs/42352747056) job Web fail ở
     bước Unit tests với đúng assertion này; các run trước trên cùng code (`dc52640`, `a8ea4c6`) xanh.
   - Đề xuất: P5 đổi sang `useLayoutEffect`; nếu muốn giữ `useEffect` thì test phải `await waitFor(() =>
     expect(button).toHaveFocus())`.
2. Ghi chú: thời lượng client đo bằng `performance.now()`; server vẫn là nguồn quyết định theo PTS (T049).
3. Engine Node: đã sửa ở T004 (`^22.22.2 || ^24.15.0 || >=26.0.0`) theo ghi chú của P5;
   `apps/web/README.md` còn ghi "Node.js 22.12+", P5 cập nhật khi sửa mục 1.

**Reviewer result**: `CHANGES_REQUESTED` (P2) — chỉ mục 1; phần còn lại đạt. P1 còn `PENDING`.
