# CP1 T001–T007 smoke evidence — monorepo toolchain

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP1` |
| Task | `T001-T007` |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P3 Cường` review T003; `P5 Hiển` review T004/T006 |
| Candidate commit | `CP1 T001-T007(setup): scaffold monorepo toolchain` |
| Commit | `84958a34c44bc5e1d7e655cae6b6ed85e07d0c08` — [84958a3](https://github.com/HiImNVH/ViSign/commit/84958a34c44bc5e1d7e655cae6b6ed85e07d0c08) |
| Ngày/giờ | `2026-11-07T13:41:17+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15 (uv-managed), Node.js 24.18.0, npm 11.16.0 |
| Status | `PASS` local; remote verification pending |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh: ba project Python API, Python AI và web cài được dependency từ lockfile,
  lint/typecheck đạt và chạy test rỗng/smoke thành công; `.gitignore` chặn raw video, model binary,
  landmark bulk, file tạm và secret.
- File/module chính: `pyproject.toml`, `services/inference-api/{pyproject.toml,uv.lock,src,tests}`,
  `ai/{pyproject.toml,uv.lock,src,tests}`, `apps/web/` config/scaffold, `.gitignore`,
  `.gitkeep` cho `data/`, `tests/`, `.github/workflows/`, `infra/gcp/`.
- Không thuộc phạm vi: domain/router API (CP2), pipeline AI, UI recognition, `data/README.md` (T008),
  workflow CI (T091).
- Nguồn tham khảo: toolchain legacy `HiImNVH/7nghiep367` nhánh `Model/Cường` commit `985e871`; chỉ lấy
  file cấu hình, không lấy application code. Thay đổi so với legacy: version `0.0.1`, bỏ email giả
  trong `authors`, bỏ `pytest-asyncio` chưa dùng, bỏ script `test:smoke` trỏ tới file không tồn tại,
  gộp Vitest vào `vite.config.ts` theo T006, `requires-python` API khóa `<3.13`.
- Version: release `0.0.1`, API `v1`; chưa có feature schema/model trong candidate.

## 3. Pre-commit synchronization

- `git fetch origin main` sau commit `9cfdf14` của Huy: PASS; `git pull --rebase --autostash` sạch.
- Remote tiến tiếp tới `7b3c0733ea24d4c7913045beb83e75245af47196` (Huy, docs-only): `git stash push
  --include-untracked`, `git pull --rebase`, `git stash apply` không conflict; chạy lại API/AI/web gate
  lúc `2026-11-07T13:43:10+07:00`, tất cả exit 0.
- `git rev-list --left-right --count origin/main...HEAD`: `0 0`.
- Pre-push: `git pull --rebase origin main` không có commit mới (`0 1`); push `7b3c073..84958a3`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | API install | `uv sync --project services/inference-api --locked` | Lockfile khớp, cài được | 38 package resolved, exit 0 | `PASS` |
| 2 | API lint/type | `uv run --project services/inference-api ruff check services/inference-api`; `... python -m mypy services/inference-api/src services/inference-api/tests` | Không lỗi | Ruff all passed; mypy 2 files no issues; exit 0 | `PASS` |
| 3 | API smoke test | `uv run --project services/inference-api pytest services/inference-api/tests -q` | Import package đạt | 1 passed, exit 0 | `PASS` |
| 4 | AI install | `uv sync --project ai --locked`; import `av, mediapipe, numpy, cv2, torch, sklearn, matplotlib, yaml` | Dependency pin cài và import được | 68 package resolved; torch `2.11.0+cpu`, mediapipe `1.1.1`; exit 0 | `PASS` |
| 5 | AI lint/type/test | `ruff check ai`; `python -m mypy ai/src ai/tests`; `pytest ai/tests -q` (qua `uv run --project ai`) | Không lỗi, smoke đạt | Ruff passed; mypy no issues; 1 passed; exit 0 | `PASS` |
| 6 | Web install | `npm ci` trong `apps/web` | Cài từ lockfile | 278 packages, exit 0 | `PASS` |
| 7 | Web lint/type | `npm run lint`; `npm run typecheck` | Không lỗi | exit 0 cả hai | `PASS` |
| 8 | Web test rỗng | `npm test` | Vitest chạy, không có test vẫn đạt | `passWithNoTests`, exit 0 | `PASS` |
| 9 | Web build | `npm run build` | `tsc` + Vite build đạt | `dist/index.html` + bundle JS, exit 0 | `PASS` |
| 10 | Git hygiene | `git diff --check`; quét đuôi raw/model/secret và pattern credential trên candidate | Không lỗi, không file bị cấm | exit 0; không có file bị cấm/secret; chỉ cảnh báo LF→CRLF | `PASS` |
| 11 | Playwright | `npm run test:browser` | — | `NOT_RUN`: chưa có spec E2E; T032 thêm luồng fake-camera | `NOT_RUN` |

## 5. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/84958a34c44bc5e1d7e655cae6b6ed85e07d0c08` | Pushed 2026-11-07T13:45:31+07:00 |
| GitHub Actions | `NOT_RUN` — workflow thuộc T091/CP7 | CP1 dùng local gate |
| Report trong repo | File evidence này | — |
| API/cloud | `NOT_RUN` — chưa có endpoint ở CP1 | `/api/v1/health` thuộc CP2/T026 |
| Data/model | `NOT_RUN` — không có data/model trong candidate | `.gitignore` chặn binary |

## 6. Rủi ro, rollback và handoff

- Rủi ro còn lại:
  - Trên máy Tín, Windows Application Control chặn `mypy.exe` trong `ai/.venv`; dùng
    `python -m mypy` thay thế. Người khác gặp lỗi tương tự dùng cùng cách.
  - `.gitignore` chặn mọi `*.webm`/`*.mp4`; golden/representative clip cho T014/T064 cần quyết định
    riêng (ngoại lệ `!` có review hoặc lưu ngoài repo).
  - T032 ghi E2E tại `tests/e2e/`, còn Playwright config legacy đặt test trong `apps/web/tests/`;
    owner T032 cần chốt vị trí trước khi viết spec.
  - Python 3.12 được cung cấp qua `uv`; máy chỉ có Python 3.13 vẫn chạy được nhờ `uv` tự tải 3.12.
- Rollback: `git revert` riêng commit này; không ảnh hưởng tài liệu CP0.
- Việc người kế tiếp cần làm: Cường review `ai/pyproject.toml` và `ai/uv.lock`; Hiển review
  `apps/web/` config; Huy verify từ `origin/main`.
- Blocker: không có.

## 7. Xác nhận

- [x] Owner đã chạy lại gate sau lần rebase cuối.
- [x] Không có secret, raw video, landmark bulk hoặc model binary bị stage.
- [x] Full SHA và link đã được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

## 8. Independent integration review — P1/Huy

Review time: `2026-11-07T13:55:07+07:00` trên commit evidence
`18a07aef641b424ddf4772249623b1bc04a4b926` từ `origin/main`.

| Gate | Kết quả độc lập |
|---|---|
| API | `uv sync --locked`, Ruff, mypy và pytest: PASS; 1 test passed |
| AI | `uv sync --locked`, Ruff, mypy và pytest: PASS; 1 test passed |
| AI imports | `av`, MediaPipe, NumPy, OpenCV, Torch, scikit-learn, Matplotlib, YAML: PASS |
| Web | `npm ci`, lint, typecheck, Vitest empty smoke và Vite build: PASS |
| Production dependency audit | `npm audit --omit=dev`: 0 vulnerability |
| Git hygiene | Worktree sạch sau gate; generated environments/build output đều bị ignore |

Ghi chú không chặn:

- `npm audit` đầy đủ báo 10 `moderate` ở lint toolchain dev-only qua `minimatch`; production audit
  sạch. Không chạy `npm audit fix --force`; T092 sẽ đánh giá/fix có kiểm soát.
- `uv` in cảnh báo root `pyproject.toml` không có `[project]`; root chỉ giữ shared Ruff/mypy/pytest
  config, còn API/AI có project và lockfile riêng. Cảnh báo không làm sai environment hoặc gate.
- P3/Cường vẫn phải review dependency/pin AI của T003; P5/Hiển vẫn phải review web toolchain T004/T006
  trước khi CP1 chuyển hoàn toàn sang `VERIFIED`.

**Reviewer result**: `P1_VERIFIED`; `P3` và `P5` còn `PENDING`.

**Reviewer note**: Implementation/gate không cần sửa trước specialized review; hai rủi ro đã được
ghi rõ để T092 và owner liên quan xử lý.

## Independent review — P3/Cường

Review time `2026-11-07T15:00:39+07:00` (+07:00) trên commit `a8516df33d655b8d491fa8f2a3d48522dc8b80bc`.
Phạm vi T003 gồm `ai/pyproject.toml` và `ai/uv.lock` từ commit toolchain `84958a3`.
Hai tệp này giữ nguyên tại commit được kiểm thử.

| Gate | Kết quả |
|---|---|
| `uv sync --locked --project ai` | PASS, 68 package được resolve và 49 package được kiểm tra trong môi trường |
| `uv run --locked --project ai python -c "import av, mediapipe, numpy, cv2, torch, sklearn, matplotlib, yaml"` | PASS, đủ 8 import. Windows, Python 3.12.15, Torch 2.11.0+cpu |
| `uv run --locked --project ai ruff check ai` | PASS |
| `uv run --locked --project ai python -m mypy ai/src ai/tests` | PASS, 10 tệp |
| `uv run --locked --project ai pytest ai/tests -q` | PASS, 15 passed và 5 skipped. Dùng thư mục tạm riêng cho pytest |

Ghi chú — Package AI yêu cầu Python 3.12, khóa phiên bản thư viện chính và tách dependency dev. Môi trường CPU đáp ứng smoke test T003. Bốn test browser và một test MediaPipe với clip tham chiếu được skip vì lượt review này không cấu hình fixture tùy chọn. Cảnh báo về root `pyproject.toml` không chặn gate của project `ai`.

**Reviewer result**: `VERIFIED` cho T003.
