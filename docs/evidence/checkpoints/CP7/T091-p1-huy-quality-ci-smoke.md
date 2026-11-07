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

**Result**: `PENDING`
