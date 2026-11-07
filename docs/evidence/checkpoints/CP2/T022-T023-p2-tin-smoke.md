# CP2 T022–T023 smoke evidence — API config và structured logging

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP2` |
| Task | `T022-T023` (kèm `ruff format` theo ghi chú review T019–T021 của P1) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P5 Hiển` review CORS mặc định |
| Candidate commit | `CP2 T022-T023(api): add runtime settings and privacy-safe logging` |
| Commit | `fb563545e33accbbf82bb83ad9373e5eb85e8add` — [fb56354](https://github.com/HiImNVH/ViSign/commit/fb563545e33accbbf82bb83ad9373e5eb85e8add) |
| Ngày/giờ | `2026-11-07T14:24:49+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15, pydantic-settings 2 |
| Status | `PASS` local và CI; chờ reviewer verify |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh:
  - T022: `Settings` đọc `MODEL_ARTIFACT_PATH`, MIME allowlist WebM VP8/VP9, giới hạn 10,485,760 byte,
    300–6000 ms, timeout chờ slot suy luận 3 s và CORS chỉ origin Vite, không credential, cấm `*`;
    giá trị không dương hoặc `MIN >= MAX` bị từ chối khi khởi động. Không cấu hình artifact thì
    `model_artifact_path=None` (fail closed, không tự dùng fixture).
  - T023: log JSON một dòng, chỉ ghi `requestId`, `modelVersion`, `processingTimeMs`, `timingsMs`,
    `accepted`, `errorCode`, `method`, `path`, `statusCode`; mọi field khác (clip, frame, landmark,
    tensor, classLabel, tên file) bị bỏ. Level theo `.agent/core.md` §5.1 (`WARNING` → `WARN`),
    ASCII-safe cho console Windows, `configure_logging()` idempotent.
- File/module chính: `services/inference-api/src/visign_api/{config,observability}.py`, 2 file unit
  test; `ruff format` cho 6 file domain/test đã push ở `9b888a1` (chỉ xuống dòng, không đổi logic).
- Không thuộc phạm vi: đọc feature schema (T037), thư mục tạm (T024), middleware/CORS wiring (T026).
- Nguồn tham khảo: legacy `HiImNVH/7nghiep367` nhánh `backend` `b708c72`. Khác legacy:
  - bỏ default artifact trỏ vào fixture, bỏ `app_name`/`debug`/`busy_retry_after_seconds` chưa dùng
    (Retry-After nằm trong `ERROR_CATALOG`);
  - `get_settings()` có cache thay cho biến global `settings`; `configure_logging()` thay cho logger
    tạo sẵn khi import;
  - bỏ `classLabel`/`confidence` khỏi danh sách log vì T023 không yêu cầu (tối thiểu hóa dữ liệu).
- Dependency/contract/version: release `0.0.1`, API `v1`; khớp `docs/team/fe-be-api-convention.md`
  mục 3 và 6 (`377ac98`).

## 3. Pre-commit synchronization

- Remote tiến tới `c902ea3` (P1 T091 CI workflow, không chạm file candidate): `git stash push
  --include-untracked`, `git pull --rebase`, `git stash apply`; so nội dung stash với worktree (bỏ qua
  CRLF) không lệch rồi mới `git stash drop`.
- Đồng bộ lại trước commit: remote tiến tới `38cc955` (P1 docs/review, không chạm file candidate);
  stash/pull/apply lần hai, so nội dung không lệch; gate chạy lại lúc `2026-11-07T14:29:15+07:00`: 73 passed,
  Ruff/format/mypy đạt.
- `git rev-list --left-right --count origin/main...HEAD`: `0 0` tại `38cc955`.
- Pre-push: `git pull --rebase origin main` không có commit mới (`0 2`); push `38cc955..b248ec7`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `uv run --project services/inference-api pytest services/inference-api/tests -q` trước khi có module | Test mới fail | 2 collection errors, exit 2 | `PASS` |
| 2 | Unit GREEN | Cùng command, thêm `-W error` | Toàn bộ đạt, không warning | 73 passed, exit 0 | `PASS` |
| 3 | Install | `uv sync --locked --project services/inference-api` | Lockfile khớp | exit 0 | `PASS` |
| 4 | Lint/format | `ruff check services/inference-api`; `ruff format --check services/inference-api` | Không lỗi | All checks passed; 14 files already formatted | `PASS` |
| 5 | Type | `python -m mypy services/inference-api/src services/inference-api/tests` | Không lỗi | 14 source files no issues | `PASS` |
| 6 | CI parity | Các lệnh job `api` trong `.github/workflows/quality.yml` | Giống bước 3–5 | Đạt local | `PASS` |
| 7 | Runtime HTTP | — | — | `NOT_RUN`: chưa có FastAPI app (T026) | `NOT_RUN` |

## 5. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/fb563545e33accbbf82bb83ad9373e5eb85e8add` | Pushed 2026-11-07T14:30:16+07:00 |
| GitHub Actions | `https://github.com/HiImNVH/ViSign/actions/runs/42351545729` | Run trên `b248ec7` (chứa `fb56354`): api, ai, web, hygiene đều `success` |
| API/cloud | `NOT_RUN` | Chưa có endpoint |

## 6. Rủi ro, rollback và handoff

- Rủi ro còn lại: giới hạn clip đang khai báo ở cả `visign_ai` decoder và config API; cần một nguồn
  hằng số chung khi API gọi pipeline (T037/T049).
- Rollback: `git revert` riêng commit này; domain T019–T021 không phụ thuộc module mới.
- Việc người kế tiếp cần làm: Huy verify; Hiển xác nhận CORS origin mặc định.
- Blocker: không có. Push khi window `CLOSED` theo yêu cầu owner; không có commit remote chen giữa.

## 7. Xác nhận

- [x] Owner đã chạy lại gate sau lần đồng bộ cuối.
- [x] Không có secret, raw video, landmark bulk hoặc model binary bị stage.
- [x] Full SHA và link đã được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

**Reviewer result**: `PENDING`

**Reviewer note**: Chờ verify từ `origin/main`.
