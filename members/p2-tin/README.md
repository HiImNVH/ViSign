# P2 Tín - Backend/Cloud/Security

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P2` |
| Current member | Tín |
| Role | Backend/API, cloud và security; CP1 setup coordinator |
| Canonical ownership | `services/inference-api/`, `infra/gcp/`, `tests/security/`; T001–T007 setup paths |
| Allowed commit scopes | `setup` (chỉ T001–T007), `api`, `backend`, `security`, `cloud` |
| Current checkpoint | `CP1` |
| Integration window | `ACTIVE` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T001-T007 / CP1` | `REVIEW` | monorepo dirs, root/API/AI pyproject + `uv.lock`, web Vite/lint/test config, `.gitignore` | Gate local 10/10 PASS; chờ push và review Cường (AI), Hiển (web) | P1/Huy |
| `T086 / CP1 review` | `TODO` | `docs/evidence/checkpoints/CP1/T086-p1-huy-member-frame-smoke.md` | Verify member frame của Huy từ `origin/main` | P2/Tín là reviewer |
| `T099 / CP2` | `BLOCKED` | API convention, OpenAPI và client types | Chờ lead gửi quy ước FE–BE API | P5/Hiển và P1/Huy |
| `CP3-CP7` | `PLANNED` | predictor, errors/security, admin API, Cloud Run | Chờ checkpoint tương ứng | P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | `T001-T007 / CP1` |
| Proposed commit | `CP1 T001-T007(setup): scaffold monorepo toolchain` |
| Exact staged paths | `.gitignore`, `pyproject.toml`, `services/inference-api/{pyproject.toml,uv.lock,src/visign_api/__init__.py,tests/unit/test_package_smoke.py}`, `ai/{pyproject.toml,uv.lock,src/visign_ai/__init__.py,tests/test_package_smoke.py}`, `apps/web/{package.json,package-lock.json,index.html,src/main.tsx,src/App.tsx,tests/setup.ts,tsconfig.json,vite.config.ts,eslint.config.js,playwright.config.ts}`, `.gitkeep` cho `data/`, `tests/`, `.github/workflows/`, `infra/gcp/`, `members/p2-tin/README.md`, smoke evidence |
| Pre-commit sync | `PASS` — rebase lên `7b3c073`; gate chạy lại; `origin/main...HEAD` = `0 0` lúc 2026-11-07T13:43+07:00 |
| Gate commands | `uv sync --locked`, Ruff, `python -m mypy`, pytest cho API/AI; `npm ci`, lint, typecheck, test, build cho web; `git diff --cached --check` — 10/10 PASS, Playwright `NOT_RUN` |
| Smoke evidence | `docs/evidence/checkpoints/CP1/T001-T007-p2-tin-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` — pull/rebase và rerun gate sau commit |
| Push status | `NOT_PUSHED` |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP0/T086` | Independent CP0 verification | `CP0 T086(verify): record independent P2 verification` | `c77fd98264a6b22cff2a203de9380d5c3dd92f53` | [commit](https://github.com/HiImNVH/ViSign/commit/c77fd98264a6b22cff2a203de9380d5c3dd92f53) | 5/5 PASS | P1/Huy | `VERIFIED` |
| `CP1/T001-T007` | Assign setup toolchain | `CP1 T001-T007(spec): assign setup toolchain to P2 Tin` | `abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4` | [commit](https://github.com/HiImNVH/ViSign/commit/abb465b65bdeffd0c28ea9bcb28dac7271bdb8a4) | Docs check | P1/Huy | `PUSHED` |
| `CP1/T001-T007` | Implement monorepo toolchain | `CP1 T001-T007(setup): scaffold monorepo toolchain` | `PENDING` | `PENDING` | 10/10 PASS local | P1/Huy | `LOCAL-DRAFT` |

## Handoff

- Current risks: setup chạm web và AI paths ngoài ownership thường kỳ của Tín; `.gitignore` chặn
  mọi `*.webm` nên golden clip T014/T064 cần ngoại lệ có review; vị trí E2E T032 (`tests/e2e/`) khác
  Playwright `testDir` (`apps/web/tests/`).
- Required input: Cường review `ai/pyproject.toml`; Hiển review web toolchain; T099 vẫn chờ lead.
- Next owner/action: Tín push candidate CP1 rồi bàn giao Cường/Hiển/Huy verify từ `origin/main`.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P1/Huy | P2/Tín | Nhận T001–T007, CP1 integration window active |
