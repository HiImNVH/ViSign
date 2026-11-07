# P5 Hiển - Frontend/UX

## Member profile

| Field | Value |
|---|---|
| Worker ID | `P5` |
| Current member | Hiển |
| Role | Frontend, UX và browser E2E |
| Canonical ownership | `apps/web/`, frontend tests và UX evidence |
| Allowed commit scopes | `web`, `ui`, `ux`, `e2e` |
| Current checkpoint | `CP1 review`, chuẩn bị `CP2` |
| Integration window | `WAITING` |
| Last updated | `2026-11-07` |

## Current assignments

| Task/CP | Status | Planned canonical paths | Next action / Blocker | Reviewer |
|---|---|---|---|---|
| `T004/T006 / CP1` | `REVIEW` | web Vite/lint/test config do Tín tạo | Review web toolchain | P1/Huy |
| `T040 / CP2` | `PLANNED` | typed API client và model-info | Quy ước lead tại `docs/team/fe-be-api-convention.md`; chờ Tín đóng băng T099 | P2/Tín |
| `T051-T053 / CP4` | `PLANNED` | error/retry/placeholders và integration | Chờ contract foundation | P2/Tín và P1/Huy |

## Commit đang chuẩn bị

| Field | Value |
|---|---|
| Task/checkpoint | Chưa có commit active; hiện chỉ review T004/T006 |
| Proposed commit | `CP2 T040(web): add versioned inference API client` |
| Exact staged paths | `PENDING` sau khi T099 và CP2 được mở |
| Pre-commit sync | `PENDING` |
| Gate commands | web lint/typecheck/unit/build và API contract/type test |
| Smoke evidence | `docs/evidence/checkpoints/CP2/T040-p5-hien-smoke.md` |
| Local commit | `PENDING` |
| Pre-push sync | `PENDING` |
| Push status | `BLOCKED` — chờ T099 và CP2 window |

## Commit ledger

| CP/Task | Purpose | Proposed/actual message | Full SHA | GitHub link | Gate | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CP2/T040` | Versioned inference API client | `CP2 T040(web): add versioned inference API client` | `PENDING` | `PENDING` | `NOT_RUN` | P2/Tín, P1/Huy | `BLOCKED` |

## Handoff

- Current risks: tự chốt client fields trước T099 sẽ gây contract drift.
- Required input: Tín/lead chốt FE–BE API convention và OpenAPI v1.
- Next owner/action: review T004/T006; sau đó chờ Huy mở CP2.
- Work-in-progress limit: tối đa 2 task `DOING`.

## Handoff history

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-11-07 | P2/Tín | P5/Hiển | Review web toolchain T004/T006 |
