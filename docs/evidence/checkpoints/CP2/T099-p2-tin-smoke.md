# CP2 T099 smoke evidence — đóng băng quy ước API v1 FE–BE

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP2` |
| Task | `T099` |
| Owner | `P2 Tín` |
| Reviewer | `P5 Hiển` (consumer, xác nhận D1–D4 và `inference-api.ts`); `P1 Huy` (lead) |
| Candidate commit | `CP2 T099(api): freeze FE-BE API v1 conventions with drift test` |
| Commit | `5add4005e572efcd17b921fb144b9feea1b7189c` — [5add400](https://github.com/HiImNVH/ViSign/commit/5add4005e572efcd17b921fb144b9feea1b7189c) |
| Ngày/giờ | `2026-11-07T14:43:17+07:00` |
| Môi trường | Windows 11, Git Bash, uv 0.13.7, CPython 3.12.15, Node.js 24.18.0 |
| Status | `PASS` local; chờ push và xác nhận của P5 |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh: D1–D4 của lead handoff được owner chốt; `openapi.yaml`, Python domain và
  TypeScript types khớp enum/field/required/nullable và được drift test khóa trong CI.
- File chính:
  - `docs/contracts/api-conventions.md` (bản đóng băng `api-conventions-v1.0.0`);
  - `specs/001-vsl-recognition-mvp/contracts/openapi.yaml` (D1: mô tả 422, không đổi schema/version);
  - `apps/web/src/types/inference-api.ts` (D3/D4, viết tay);
  - `tests/contract/test_api_contract_drift.py` (drift test);
  - `.github/workflows/quality.yml` (một dòng: job `api` chạy thêm `tests/contract`).
- Không thuộc phạm vi: `ROUTE_NOT_FOUND`/`METHOD_NOT_ALLOWED` (T073), API client và timeout D2 (T040/T053),
  câu chữ lỗi `vi.ts` (T028/T052), bump `info.version`.
- Ghi chú ownership: `inference-api.ts` nằm trong `apps/web/` và trùng file với T027 của P5; T099 liệt kê
  file này nên P2 tạo bản tối thiểu, P5 review và tiếp tục mở rộng ở T027/T040.

## 3. Pre-commit synchronization

- Pull `a8ea4c6` (P3 verify T003) trước khi sửa; `origin/main...HEAD` = `0 0` lúc
  `2026-11-07T14:43:17+07:00`.

## 4. Smoke test

| # | Mục tiêu | Command | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Test-first RED | `uv run --project services/inference-api pytest tests/contract -q` trước khi sửa | Test D1 và TS fail | 1 failed (D1), 9 errors (thiếu TS), 5 passed (Python ↔ OpenAPI) | `PASS` |
| 2 | Drift GREEN | Cùng command sau D1 + TS | Toàn bộ đạt | 15 passed | `PASS` |
| 3 | Drift bắt lỗi | Tạm bỏ một mã lỗi / bỏ `\| null` của `macroF1` / đổi `timingsMs?` thành required trong TS | Mỗi lần fail | 3/3 lần `1 failed, 14 passed`; khôi phục → 15 passed, file giống hệt | `PASS` |
| 4 | API + contract | `pytest services/inference-api/tests tests/contract -q`; Ruff; `ruff format --check`; `python -m mypy tests/contract services/inference-api/src services/inference-api/tests` | Không lỗi | 88 passed; Ruff/format đạt; mypy 15 files no issues | `PASS` |
| 5 | Web | `npm run lint`, `typecheck`, `test`, `build` trong `apps/web` | Không lỗi | exit 0 cả bốn | `PASS` |
| 6 | YAML | `yaml.safe_load` cho `quality.yml` và `openapi.yaml` | Parse được | OK | `PASS` |
| 7 | Git hygiene | `git diff --cached --check`; quét file bị cấm/secret | Không lỗi | exit 0; không có file bị cấm/secret trong 7 path staged | `PASS` |

## 5. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/5add4005e572efcd17b921fb144b9feea1b7189c` | Pushed 2026-11-07T14:47:39+07:00 |
| GitHub Actions | `https://github.com/HiImNVH/ViSign/actions/runs/42353287941` | Job `api` chạy drift test: success. Run trước [42352747056](https://github.com/HiImNVH/ViSign/actions/runs/42352747056) đỏ ở job Web do test flaky T039, không liên quan |
| Bản đóng băng | `docs/contracts/api-conventions.md` | `api-conventions-v1.0.0` |

## 6. Rủi ro, rollback và handoff

- Rủi ro còn lại: 3 điểm lệch ghi tại `docs/contracts/api-conventions.md` mục 3 (`HealthResponse.modelVersion`
  required hay không — chờ P1; mã 404/405 ở T073; MIME ở T049). Drift test đọc TS bằng regex nên
  interface phải giữ mỗi field một dòng.
- Rollback: `git revert` riêng commit này; domain Python và web không phụ thuộc file mới ngoài drift test.
- Việc người kế tiếp cần làm: P5 xác nhận D1–D4 và `inference-api.ts` rồi mở T040; P1 quyết định điểm
  lệch 1; P1 xác nhận dòng thêm vào `quality.yml`.
- Blocker: không có.

## 7. Xác nhận

- [x] Owner đã chạy lại gate sau lần đồng bộ cuối.
- [x] Không có secret, raw video, landmark bulk hoặc model binary bị stage.
- [x] Full SHA và link đã được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.

## Independent review — P1/Huy (lead)

Review time: `2026-11-07T16:38:40+07:00` trên `origin/main` `d3afdff` (chứa `5add400`).

| Gate | Kết quả |
|---|---|
| D1–D4 | Khớp lead handoff; mô tả 422 trong `openapi.yaml` đúng D1 |
| Drift test | `pytest tests/contract -q`: 15 passed. Mutation: xoá `SERVICE_BUSY` khỏi TS → 1 failed; trả mô tả 422 cũ → 1 failed; đã khôi phục |
| CI | Job `api` chạy `tests/contract`; các run sau `5add400` success |
| Điểm lệch 1 (`HealthResponse.modelVersion`) | **Lead quyết định theo OpenAPI**: optional + nullable. Đã sửa `docs/team/fe-be-api-convention.md` mục 4 trong commit review này; không đổi schema/TS |
| Điểm lệch 2, 3 | Đồng ý chuyển sang T073 và T049 |

**Lead result**: `P1_VERIFIED`; `P5` (consumer) còn `PENDING`.

**Reviewer note**: Chờ P5 xác nhận consumer (D2 timeout, D3 fallback, `inference-api.ts`).

## Follow-up sau review P5 — câu chữ preflight (`2026-11-07T19:12+07:00`)

- `docs/contracts/api-conventions.md` lên `api-conventions-v1.0.1`: "mọi response/mọi lỗi" giới hạn cho response
  của API; thêm ngoại lệ preflight CORS (không `X-Request-ID`, origin lạ nhận `400` text thường, FE xử lý như lỗi
  mạng/CORS) và ghi hậu quả của `CORS_ALLOW_CREDENTIALS=true`; thêm mục lịch sử thay đổi.
- Không đổi `openapi.yaml`, Python domain hay `inference-api.ts`: drift test vẫn xanh trong gate API + contract.
