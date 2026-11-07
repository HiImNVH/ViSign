# T091 smoke evidence — GitHub Actions quality gate (kéo sớm từ CP7)

## Identification

| Field | Value |
|---|---|
| Checkpoint/task | `CP7 / T091` — phần `quality.yml`; `deploy-gcp.yml` vẫn chờ CP7 |
| Implementer | `P1 Huy` |
| Reviewer | `P2 Tín` (API/AI job), `P5 Hiển` (web job) |
| Candidate commit | `CP7 T091(ci): add quality gate workflow` |
| Commit SHA | `c902ea3fc4fd7958309b30e4a431cee0d3dcd287` — [c902ea3](https://github.com/HiImNVH/ViSign/commit/c902ea3fc4fd7958309b30e4a431cee0d3dcd287) |
| Run time | `2026-11-07T14:22:33+07:00` |
| Status | `PASS` local và GitHub Actions ([run 42351034900](https://github.com/HiImNVH/ViSign/actions/runs/42351034900)) |

## Lý do kéo sớm

CP1/CP2 đang tái lập gate bằng tay cho từng commit. Workflow chạy đúng các lệnh đó trên mọi push/PR,
nên reviewer có link Actions bền vững thay vì chỉ dựa vào log máy cá nhân. Không deploy trong workflow.

## Phạm vi

| Job | Lệnh |
|---|---|
| `api` | `uv sync --locked`, `ruff check`, `mypy src tests`, `pytest` cho `services/inference-api` |
| `ai` | `libgl1`, `uv sync --locked`, `ruff check`, `mypy src tests`, `pytest -rs` cho `ai` |
| `web` | `npm ci`, lint, typecheck, Vitest, build, `npm audit --omit=dev --audit-level=high` |
| `hygiene` | Chặn raw media/model binary/secret bị track; `git diff --check` commit mới nhất |

Pin: uv `0.13.7` và Node 24, khớp môi trường CP1; Python 3.12 do uv quản lý theo `requires-python`.

## Local smoke trước push

| Gate | Kết quả |
|---|---|
| API | Ruff, mypy, pytest: 44 passed |
| AI | Ruff, mypy no issues (10 files), pytest 15 passed / 5 skipped (clip/browser fixture local) |
| Web | `npm ci`, lint, typecheck, Vitest, build: PASS |
| Hygiene | Không file bị cấm được track; YAML parse OK |

## GitHub Actions

| Job | Kết quả | Thời gian |
|---|---|---|
| API | success | 10 s |
| AI | success — 67 package, Ruff/mypy đạt, 15 passed / 5 skipped | 49 s |
| Web | success | 22 s |
| Hygiene | success | 4 s |

## Rủi ro

- `ai/uv.lock` lấy torch từ PyPI nên Linux kéo theo CUDA toolkit (~36 package nvidia/cuda). Job AI chậm
  và tốn dung lượng; dùng cache uv. Run đầu chỉ 49 s nên chưa cần đổi; index CPU vẫn là quyết định
  T003/T092 của P2/P3 nếu image Cloud Run quá nặng.
- Playwright/E2E chưa vào workflow; thêm khi T032 có spec fake-camera.
- 5 test AI skip trên CI vì cần clip tham chiếu local; parity thật vẫn do owner chạy.

## Links

- Commit: [c902ea3](https://github.com/HiImNVH/ViSign/commit/c902ea3fc4fd7958309b30e4a431cee0d3dcd287).
- Actions run: [42351034900](https://github.com/HiImNVH/ViSign/actions/runs/42351034900) — `success`.

## Reviewer

### Independent review — P2/Tín

Review time: `2026-11-07T14:55+07:00` trên `origin/main` `5b6a441`.

| Kiểm tra | Kết quả |
|---|---|
| Lệnh job `api` | Trùng gate local của P2 (`uv sync --locked`, Ruff, `python -m mypy`, pytest); từ `5add400` chạy thêm `tests/contract` (drift test T099) |
| Quyền và concurrency | `permissions: contents: read`; `concurrency` hủy run cũ trên cùng ref |
| Kết quả thực tế | Run [42351545729](https://github.com/HiImNVH/ViSign/actions/runs/42351545729) xanh; run [42352747056](https://github.com/HiImNVH/ViSign/actions/runs/42352747056) đỏ do test flaky của T039, không phải workflow |

Ghi chú không chặn:

1. `actions/checkout@v4` và `actions/setup-node@v4` bị GitHub cảnh báo "Node.js 20 is deprecated"; nâng
   lên bản major dùng Node 24 khi có.
2. `cancel-in-progress` trên `main` làm commit trung gian không có run riêng (ví dụ `fb56354` chỉ có kết
   quả qua run của `b248ec7`); evidence cần ghi run của commit chứa nó.
3. Bước hygiene chỉ `git diff --check HEAD~1 HEAD`; push nhiều commit một lần chỉ kiểm commit cuối. Danh sách
   đuôi cấm thiếu `.safetensors`/`.tflite` so với `.gitignore`.
4. Chưa có `ruff format --check` (P1 đã ghi để T092 quyết định).

**Result**: `P2_VERIFIED`

## Follow-up sau review P2 — `2026-11-07T15:38:42+07:00`

| # | Ghi chú P2 | Xử lý trong `quality.yml` |
|---|---|---|
| 1 | Action v4 chạy Node 20 (deprecated) | `actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v10.3.3` (đều `node24`; setup-uv không phát hành tag major nên pin bản đầy đủ); input `fetch-depth`, `node-version`, `cache`, `cache-dependency-path`, `version`, `enable-cache`, `cache-dependency-glob` còn nguyên |
| 2 | `cancel-in-progress` làm commit trung gian trên `main` mất run | Group theo `github.sha` cho push; chỉ hủy run cũ của cùng PR |
| 3 | Hygiene chỉ kiểm commit cuối | `fetch-depth: 0`; push kiểm `github.event.before..HEAD`, PR kiểm `merge-base..HEAD`; nhánh mới/before không tồn tại thì lùi về `HEAD~1` |
| 4 | Thiếu `.safetensors`/`.tflite` | Thêm vào danh sách đuôi bị chặn, khớp `.gitignore` |

Không xử lý ở đây: `ruff format --check` — để T092 quyết định như ghi chú trước.

Local: YAML parse OK; không file bị cấm được track; `git diff --check` trên dải `7b3c073..HEAD` PASS.
Run đầu [42356363410](https://github.com/HiImNVH/ViSign/actions/runs/42356363410) fail ở job API/AI: `Unable to resolve action astral-sh/setup-uv@v10` vì repo không có tag `v10`; sửa thành `v10.3.3`.
Actions run sau sửa: [42356425710](https://github.com/HiImNVH/ViSign/actions/runs/42356425710) trên `4909fb4` — 4/4 job `success`, không còn annotation cảnh báo Node 20; hygiene kiểm dải `before..HEAD` của push.

**Follow-up result**: 4/4 ghi chú P2 đã xử lý; chờ P2 xác nhận lại nếu cần.

### Xác nhận follow-up — P2/Tín (`2026-11-07T15:50+07:00`)

Tái lập trên `origin/main` `7b1e84f`:

| Kiểm tra | Kết quả |
|---|---|
| Tag action tồn tại | `actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v10.3.3`: GitHub API trả 200 |
| Actions | [42356425710](https://github.com/HiImNVH/ViSign/actions/runs/42356425710) (`4909fb4`) và [42356530609](https://github.com/HiImNVH/ViSign/actions/runs/42356530609) (`7b1e84f`): `success` |
| Nội dung | YAML parse OK; job `api` vẫn chạy `tests/contract` (drift T099); group concurrency theo `github.sha` cho push; hygiene kiểm `before..HEAD`, danh sách đuôi có `.safetensors`/`.tflite` |
| Whitespace | `git diff --check 7b3c073 HEAD`: PASS |

**Follow-up result**: `P2_VERIFIED` — 4/4 ghi chú đã xử lý đúng; `ruff format --check` vẫn để T092.
