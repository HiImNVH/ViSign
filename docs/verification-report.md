# T063 accessibility verification — 2026-11-08

**Scope:** CP4 / T063 web recognition accessibility audit, owner P5 Hiển. This report does not cover T067 full local/CI/cloud verification.

## Environment and reproducibility

- Windows; Microsoft Edge (`msedge` channel) with Playwright and simulated video capture.
- Project viewports: desktop 1440×900, mobile 320×640, landscape 640×360; additional focus-clipping stress check at 320×180.
- API v1 model metadata and prediction responses were intercepted with deterministic fixtures; no real backend or physical camera was exercised.
- Run from `apps/web`: `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check`. The script runs ESLint, TypeScript, Vitest, builds a fresh Vite bundle and executes Playwright against `vite preview`.

## Results

| Gate | Verified result | Status |
|---|---|---|
| Lint + typecheck + Vite build | Exit code 0 | PASS |
| Unit/component Vitest | 165 passed, 4 skipped | PASS |
| All Edge Playwright | 75 passed, 3 skipped | PASS |
| T063 Playwright | 7 tests × 3 projects = **21 passed** | PASS |
| axe WCAG 2 A/AA and WCAG 2.1 A/AA | **0 violations** in audited idle/help/accepted/rejected snapshots | PASS |

The three browser skips are the existing T040 live-backend test, one per project. Four unit tests were already skipped. Axe snapshots do not demonstrate full WCAG conformance.

## Findings

| Area | Observed behavior |
|---|---|
| Keyboard | Tab/Shift+Tab navigate History, Help and camera; Enter/Space activate capture, stop and deliberate upload. Stopping does not upload automatically. |
| Focus | Phase transitions, metadata retry, rejected-result retry, camera permission denial and history confirmation/cancel/clear maintain or restore meaningful focus. Escape restores the dialog opener. |
| Announcements | Camera status uses `role=status`, `aria-atomic=true`, and displays `Đang nhận diện…` during submission; accepted/rejected result sections have `aria-live=polite` and accessible names. |
| Labels | Camera region has privacy description, preview video has accessible name, dialogs have titles; permission denial uses an alert. |
| Compact view | Camera control focus outline fits inside 320×180 camera viewport; same accessibility suite passes all three project viewports. |

The audit found and fixed focus loss after transient camera, metadata and history controls unmounted; a stale submitting status; Tab focus escaping the one-button help dialog; and a clipped focus ring at 320×180. The rejected-result E2E fixture was updated to use the API-required `text: 'Không nhận diện được'` value. The full web gate passed after these changes.

## Limits and handoff

- **NOT_RUN:** manual NVDA/JAWS/VoiceOver announcement timing, reading order and repetition. Review the transcript live region with assistive technology before claiming full accessibility.
- **NOT_RUN:** physical camera, real mobile hardware, real backend, production/cloud or CI (T067 scope).
- **PENDING:** independent P1/P2 review; do not mark T063 VERIFIED in `tasks.md` yet.

Smoke evidence: `docs/evidence/checkpoints/CP4/T063-p5-hien-smoke.md`.

## T063 follow-up after P1 changes requested (2026-11-08)

P1 reproduced intermittent `MediaRecorder` failure on their Edge fake-camera run (4, 3, 1 failures across three 21-test runs). P5 could not reproduce it locally: **63/63 passed before the fix**. The follow-up changes capture startup to report `recording` only after `MediaRecorder.start()` succeeds, fails closed when its state unexpectedly becomes inactive, and logs only error name, lifecycle stage, MIME, bytes/chunk counts, timing, and video-track states. No video, browser exception message, device label, or device ID is logged. A test-only observer waits for a nonempty chunk from the **native** MediaRecorder and a minimum duration instead of assuming that a fixed 500 ms delay guarantees an encoded clip; there are no automatic retries.

Verification on Windows / Edge `msedge`, simulated camera and mocked API:

| Command / check | Observed result |
|---|---|
| `npm.cmd run lint` and `npm.cmd run typecheck` | PASS |
| `npx.cmd vitest run tests/recognition/cameraSession.test.ts` | 30/30 PASS, including start failure, named async error, and unexpected inactive recorder |
| `npx.cmd playwright test tests/accessibility/recognition-accessibility.spec.ts --repeat-each=3 --retries=0 --workers=1` | **63/63 PASS** (desktop, mobile, landscape; each scenario repeated 3 times) |
| `$env:VISIGN_BROWSER_CHANNEL='msedge'; npm.cmd run check` | Exit 0; 168 unit PASS / 4 skipped, 84 browser PASS / 12 skipped, lint/typecheck/build PASS |

The 12 browser skips comprise nine optional T088 screenshot capture cases plus three T040 tests requiring a live backend. P1's historical finding remains valid for the machine/run where it occurred. These new results do not establish that native codec/device failures cannot recur on P1's machine; independent re-review and manual screen-reader tests remain pending. T063 stays unchecked.
