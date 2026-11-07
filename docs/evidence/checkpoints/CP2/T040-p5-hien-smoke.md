# T040 — frontend API client

- Client sends a single camera blob as multipart `clip`, sends UUID `X-Request-ID` and reads response correlation and `Retry-After`. It supports model-info and health, request cancellation, 15 s prediction and 5 s metadata timeouts.
- Responses receive runtime shape checks; unknown error codes remain available to a future UI fallback without exposing server messages. Optional diagnostics can be absent.
- Windows / Node 26.7.0: lint, typecheck, Vitest and production build passed. Tests use mocked transport; no live endpoint or UI recognition integration is claimed. T041/T043/T053 remain separate.
- Candidate includes only the client, its tests and this evidence. Existing uncommitted camera/README changes were present during tests and are excluded from the commit.
- Status: local implementation for independent P2/P1 review; not verified end-to-end.
