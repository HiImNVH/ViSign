# CP1 T004 smoke evidence — khai báo đúng mức Node tối thiểu

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP1 / T004` (sửa sau review của P5) |
| Owner | `P2 Tín` |
| Reviewer | `P5 Hiển` (người phát hiện), `P1 Huy` |
| Candidate commit | `CP1 T004(setup): align Node engines with dependency floor` |
| Commit | `84478b28b99dfd180fb09e09e187a5b813160894` — [84478b2](https://github.com/HiImNVH/ViSign/commit/84478b28b99dfd180fb09e09e187a5b813160894); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42353287941) |
| Ngày/giờ | `2026-11-07T14:55+07:00` |
| Status | `PASS` local |

## Vấn đề

`apps/web/package.json` khai báo `"node": ">=22.12.0"`, nhưng dependency dev trong lockfile yêu cầu cao hơn:

| Dependency | `engines.node` |
|---|---|
| `jsdom` 30.1.3 | `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0` |
| `eslint` 10.13.0, `@eslint/js` | `^20.19.0 \|\| ^22.13.0 \|\| >=24` |
| `vitest` 5.0.5 | `^22.12.0 \|\| ^24.0.0 \|\| >=26.0.0` |

Node 22.12–22.22.1, 23.x, 24.0–24.14 và 25.x thỏa khai báo cũ nhưng không thỏa `jsdom`.

## Thay đổi

- `apps/web/package.json` và `packages[""].engines` trong `apps/web/package-lock.json`:
  `"node": "^22.22.2 || ^24.15.0 || >=26.0.0"` (giao của mọi dependency trực tiếp). Không đổi dependency.
- Không sửa `plan.md`, `quickstart.md` (P1) và `apps/web/README.md` (P5) vẫn ghi "Node.js 22.12+"; owner
  cập nhật.

## Smoke

| Gate | Kết quả | Status |
|---|---|---|
| `npx semver@7.7.2 -r "<range>" 22.12.0 22.22.2 24.0.0 24.15.0 24.18.0 26.7.0` | Chấp nhận 22.22.2, 24.15.0, 24.18.0, 26.7.0; loại 22.12.0, 24.0.0 | `PASS` |
| `npm ci` | 278 packages, exit 0 | `PASS` |
| `npm run lint`, `npm run typecheck` | exit 0 | `PASS` |
| CI `quality` dùng `node-version: "24"` | Bản 24 mới nhất ≥ 24.15.0 nên vẫn thỏa | `PASS` |

**Reviewer result**: `PENDING`
